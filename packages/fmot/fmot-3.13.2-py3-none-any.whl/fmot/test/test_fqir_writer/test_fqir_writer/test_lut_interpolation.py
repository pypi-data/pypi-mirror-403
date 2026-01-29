from fmot.fqir.writer import FQIRWriter, new_fqir_graph
from fmot.fqir import GraphProto, NodeProto, TensorProto
import numpy as np
import matplotlib.pyplot as plt
import pytest


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


ILUT_FUNCTIONS = {
    "sigmoid": sigmoid,
    "tanh": np.tanh,
    "sin": np.sin,
    "cos": np.cos,
    "exp": np.exp,
}


@pytest.mark.parametrize("precision", ["int16", "int24"])
@pytest.mark.parametrize(
    ["func", "quanta"],
    [["sigmoid", -12], ["tanh", -13], ["sin", -13], ["cos", -13], ["exp", -15]],
)
def test_ilut(func: str, quanta: int, precision: str, plot=False):
    graph = GraphProto()
    if precision == "int24":
        quanta -= 8
    x = TensorProto(name="x", dtype=f"fq{precision}", shape=[1000], quanta=quanta)
    graph.add_input(x)

    writer = FQIRWriter(arith=graph, init=None, act_precision=precision)
    fn = ILUT_FUNCTIONS[func]
    out = writer.interpolating_lut(x, fn, name=func)
    graph.add_output(out)

    if precision == "int16":
        x = np.arange(-(2**15), 2**15, 1, dtype=np.int32)
    else:
        x = np.linspace(-(2**23), 2**23, 200000, dtype=np.int32)
    y = graph.run(x)

    expected = fn(x * 2**quanta) * 2 ** (-out.quanta)

    rms_error = np.sqrt(np.mean(((y - expected) * 2**out.quanta) ** 2))

    print(f"{rms_error = }")

    if plot:
        plt.plot(x, y, "orange", label="quantized")
        plt.plot(x, expected, "k:", label="expected")
        plt.legend()
        plt.title(f"ClaraCraft {func}")
        plt.show()

        plt.plot(x, (y - expected))
        plt.title(f"ClaraCraft {func} error at {precision}")
        plt.show()

    assert rms_error < 1e-3


@pytest.mark.parametrize("precision", ["int16", "int24"])
@pytest.mark.parametrize("func", ["log", "log2", "log10"])
@pytest.mark.parametrize("quanta", [-13, -20])
def test_log(func: str, precision: str, quanta: int, plot=False):
    N_CHAN = 128
    graph = GraphProto()
    x = TensorProto(name="x", dtype=f"fq{precision}", shape=[N_CHAN], quanta=quanta)
    graph.add_input(x)

    writer = FQIRWriter(arith=graph, init=None, act_precision=precision)
    if func == "log":
        y = writer.log(x)
        f = np.log
    elif func == "log2":
        y = writer.log2(x)
        f = np.log2
    elif func == "log10":
        y = writer.log10(x)
        f = np.log10

    yq = y.quanta
    graph.add_output(y)
    # print(graph)

    if precision == "int16":
        x = np.arange(1, 2**15, 1, dtype=np.int32)
    else:
        x = (2.0) ** (np.linspace(0, 23, 1000))
        x = x.astype(np.int32)
    y = graph.run(x)
    expected = f(x * 2**quanta) / 2 ** (yq)

    if plot:
        plt.plot(x, y, "orange", label="quantized")
        plt.xscale("log", base=2)
        plt.plot(x, expected, "k:", label="expected")
        plt.legend()
        plt.title(f"ClaraCraft {func}")
        plt.grid()
        plt.show()

        err = expected - y
        plt.plot(x, err)
        plt.xscale("log", base=2)
        plt.show()

    max_err = np.max(np.abs(expected - y))
    if precision == "int16":
        assert max_err < 250
    else:
        assert max_err < 3e5


@pytest.mark.parametrize("precision", ["int16", "int24"])
@pytest.mark.parametrize("quanta", [-15])
@pytest.mark.parametrize("power", [-2, -1, 1, 2, 3, 0.5, -0.5, 1.3, -0.75, 0.31287])
def test_pow(power: float, quanta: int, precision: str, plot=False):
    if power == -2 and precision == "int24":
        pytest.xfail("int24 pow -2 does not work currently")

    graph = GraphProto()
    x = TensorProto(name="x", dtype=f"fq{precision}", shape=[1000], quanta=quanta)
    graph.add_input(x)

    writer = FQIRWriter(arith=graph, init=None, act_precision=precision)
    out = writer.pow(x, power)
    graph.add_output(out)

    for node in graph.nodes:
        print(node)
        for y in node.outputs:
            print(f"  {y.name}->{y.dtype},{y.quanta}")

    isinteger = power % 1 == 0

    if precision == "int16":
        x = np.arange(-(2**15), 2**15, 1, dtype=np.int32)
    else:
        x = (2.0) ** (np.linspace(0, 23, 3000))
        x = x.astype(np.int32)
        x = np.concatenate([-x, np.zeros(1).astype(np.int32), x])
        x = np.unique(x)
        x = np.sort(x)
    if not isinteger:
        x = x[x > 0]
    y = graph.run(x)

    expected = np.power(x * 2**quanta, power) * 2 ** (-out.quanta)
    expected[np.isnan(expected)] = 0

    mask = np.abs(x) > 5
    rms_error = np.sqrt(np.mean((y - expected)[mask] ** 2))

    print(f"{rms_error = }")

    if plot:
        plt.plot(x, y, "-", label="quantized")
        plt.plot(x, expected, "k:", label="expected")
        plt.xscale("symlog", base=2)
        plt.yscale("symlog", base=2)
        plt.grid()
        plt.legend()
        plt.title(f"ClaraCraft pow({power})")
        plt.show()

    if precision == "int16":
        assert rms_error < 10
    else:
        assert rms_error < 1e6


@pytest.mark.parametrize("quanta", [-15, -7, 0, 7])
@pytest.mark.parametrize("pos_only", [True, False])
def test_reciprocal(quanta: int, pos_only: bool, eps_int: int = 1, plot=False):
    graph = GraphProto()
    x = TensorProto(name="x", dtype="fqint16", shape=[1000], quanta=quanta)
    graph.add_input(x)
    writer = FQIRWriter(arith=graph, init=None, act_precision="int16")
    out = writer.reciprocal(x, pos_only=pos_only, eps_int=eps_int)

    graph.add_output(out)

    if pos_only:
        x = np.arange(0, 2**15, 1, dtype=np.int32)
    else:
        x = np.arange(-(2**15), 2**15, 1, dtype=np.int32)

    y = graph.run(x)

    expected = 1 / (x * 2**quanta) * 2 ** (-out.quanta)

    if plot:
        plt.plot(x, y, "orange", label="quantized")
        plt.plot(x, expected, "k:", label="expected")

        plt.grid()
        plt.legend()
        plt.title(f"ClaraCraft reciprocal")
        plt.xscale("symlog", base=2)
        plt.yscale("symlog", base=2)

        plt.show()


@pytest.mark.parametrize("quanta", [-15, -13, -10])
def test_exp(quanta: int, plot=False):
    graph = GraphProto()
    x = TensorProto(name="x", dtype="fqint16", shape=[1000], quanta=quanta)
    graph.add_input(x)
    writer = FQIRWriter(arith=graph, init=None, act_precision="int16")

    out = writer.interpolating_lut(x, func=np.exp, name="exp")

    graph.add_output(out)

    x = np.arange(-(2**15), 2**15, 1, dtype=np.int32)

    y = graph.run(x)

    expected = np.exp(x * 2**quanta) * 2 ** (-out.quanta)

    if plot:
        plt.plot(x, y, "orange", label="quantized")
        plt.plot(x, expected, "k:", label="expected")
        plt.yscale("log", base=2)

        plt.grid()
        plt.legend()
        plt.title(f"ClaraCraft exp, quanta={quanta}")

        plt.show()


@pytest.mark.parametrize("quanta", [-9, -12])
def test_dB_to_lin(quanta: int, plot=False):
    graph = GraphProto()
    x = TensorProto(name="x", dtype="fqint16", shape=[1000], quanta=quanta)
    graph.add_input(x)
    writer = FQIRWriter(arith=graph, init=None, act_precision="int16")

    def dB_to_lin(x):
        return 10 ** (x / 20)

    out = writer.interpolating_lut(x, func=dB_to_lin, name="dB_to_lin")

    graph.add_output(out)

    x = np.arange(-(2**15), 2**15, 1, dtype=np.int32)

    y = graph.run(x)

    expected = dB_to_lin(x * 2**quanta) * 2 ** (-out.quanta)

    if plot:
        plt.plot(x, y, "orange", label="quantized")
        plt.plot(x, expected, "k:", label="expected")
        plt.yscale("log", base=2)

        plt.grid()
        plt.legend()
        plt.title(f"ClaraCraft dB_to_lin, quanta={quanta}")

        plt.show()


if __name__ == "__main__":
    # test_log("log10", "int24", quanta=-10, plot=True)
    # test_ilut("sin", -13, "int24", True)
    # test_pow(-0.5, -15, "int24", plot=True)
    pass
