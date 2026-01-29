from fmot.fqir.writer.kernels import write_fir
from fmot.fqir.writer import new_fqir_graph, FQIRWriter
from fmot.fqir import GraphProto, TensorProto
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
import pytest


@pytest.mark.parametrize("precision", ["int16", "int24"])
@pytest.mark.parametrize(
    ["b", "hop"],
    [
        [np.array([0.25, 0.25, 0.25, 0.25]), 16],
        [
            signal.firls(
                131,
                bands=np.linspace(0, 8000, 10),
                desired=np.random.uniform(low=0, high=1, size=10),
                fs=16000,
            ),
            64,
        ],
        [
            signal.firls(
                79,
                bands=np.linspace(0, 8000, 10),
                desired=np.random.uniform(low=0, high=1, size=10),
                fs=16000,
            ),
            3,
        ],
    ],
)
def test_static_fir(b: np.ndarray, hop: int, precision: str, plot=False):
    bw = int(precision.split("int")[1])
    x = TensorProto(name="x", dtype=f"fqint{bw}", shape=[hop], quanta=-bw + 1)
    main = new_fqir_graph([x])

    writer = FQIRWriter(main.subgraphs["ARITH"], main.subgraphs["INIT"], precision)
    y = write_fir(writer, b, x)

    main.subgraphs["ARITH"].add_output(y)
    main.add_output(y)

    T = max(10, 100 // hop)
    x_vals = np.random.uniform(
        low=-(2 ** (bw - 1)), high=2 ** (bw - 1) - 1, size=(T, hop)
    ).astype(np.int32)

    y_vals = main.run(x_vals)
    y_expected = signal.lfilter(b, 1, x_vals.flatten()) * 2 ** (x.quanta - y.quanta)

    if plot:
        plt.plot(y_expected, label="expected")
        plt.plot(y_vals.flatten(), label="FQIR")
        plt.legend()
        plt.grid()
        plt.show()

    THETA = 500
    error = np.max(np.abs(y_vals.flatten() - y_expected))
    assert error < THETA, f"error {error} > {THETA}"
    print(f"success! max_error (abs): {error}")


if __name__ == "__main__":
    b, h = (
        signal.firls(
            131,
            bands=np.linspace(0, 8000, 10),
            desired=np.random.uniform(low=0, high=1, size=10),
            fs=16000,
        ),
        64,
    )

    test_static_fir(b, h, "int24", True)
