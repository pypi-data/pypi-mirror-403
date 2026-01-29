from fmot.fqir.writer import FQIRWriter
import numpy as np
from fmot.fqir import GraphProto, TensorProto
import pytest


@pytest.mark.parametrize("precision", ["int16", "int24"])
@pytest.mark.parametrize(
    ["float_val", "quanta_in"],
    [[1.0, -15], [0, -15], [-3, -15], [100, -1], [-100.332, -18]],
)
def test_add_float(float_val: float, quanta_in: int, precision: str):
    graph = GraphProto()

    x = TensorProto(
        name="x",
        shape=[
            1000,
        ],
        dtype=f"fq{precision}",
        quanta=quanta_in,
    )
    graph.add_input(x)

    writer = FQIRWriter(graph, None, precision)
    y = writer._add_float(x, float_val)

    graph.add_output(y)

    bits = int(precision.split("int")[1])

    x_vals = np.linspace(-(2 ** (bits - 1)), 2 ** (bits - 1) - 1, 1000, dtype=np.int32)
    y_vals = graph.run(x_vals)

    y_expected = (x_vals * 2 ** (quanta_in) + float_val) / 2 ** (y.quanta)

    max_err = np.max(np.abs(y_vals - y_expected))

    print(max_err)
    assert max_err <= 2


@pytest.mark.parametrize("precision", ["int16", "int24"])
@pytest.mark.parametrize(
    ["float_val", "quanta_in"],
    [[1.0, -15], [0, -13], [0.7313, -14], [-2.6, 8], [1e-12, -5]],
)
def test_mul_float(float_val: float, quanta_in: int, precision: str):
    graph = GraphProto()

    x = TensorProto(
        name="x",
        shape=[
            1000,
        ],
        dtype=f"fq{precision}",
        quanta=quanta_in,
    )
    graph.add_input(x)

    writer = FQIRWriter(graph, None, precision)
    y = writer.multiply(x, float_val)

    graph.add_output(y)

    bits = int(precision.split("int")[1])

    x_vals = np.linspace(-(2 ** (bits - 1)), 2 ** (bits - 1) - 1, 1000, dtype=np.int32)
    y_vals = graph.run(x_vals)

    y_expected = (x_vals * 2 ** (quanta_in) * float_val) / 2 ** (y.quanta)

    max_err = np.max(np.abs(y_vals - y_expected))

    print(max_err)
    assert max_err <= 2


@pytest.mark.parametrize("precision", ["int16", "int24"])
def test_gt0(precision: str):
    graph = GraphProto()

    x = TensorProto(
        name="x",
        shape=[
            1000,
        ],
        dtype=f"fq{precision}",
        quanta=-15,
    )
    graph.add_input(x)

    writer = FQIRWriter(graph, None, precision)
    y = writer.gt0(x)

    graph.add_output(y)

    bits = int(precision.split("int")[1])

    x_vals = np.linspace(-(2 ** (bits - 1)), 2 ** (bits - 1) - 1, 1000, dtype=np.int32)
    y_vals = graph.run(x_vals)

    y_expected = (x_vals > 0).astype(np.int32)

    max_err = np.max(np.abs(y_vals - y_expected))

    print(max_err)
    assert max_err <= 2


@pytest.mark.parametrize("quanta_in", [-15, -13, 10])
def test_precision_split_reconstruction(quanta_in):
    graph = GraphProto()

    x = TensorProto(
        name="x",
        shape=[
            1000,
        ],
        dtype="fqint16",
        quanta=quanta_in,
    )
    graph.add_input(x)

    writer = FQIRWriter(graph, None, "int16")
    lo, hi = writer._precision_split(x, [9, 8], ["int16", "int8"])
    graph.add_output(lo)
    graph.add_output(hi)

    x_vals = np.linspace(-(2**15), 2**15 - 1, 1000, dtype=np.int32)
    lo_vals, hi_vals = graph.run(x_vals)

    reconstructed = lo_vals * 2 ** (lo.quanta) + hi_vals * 2 ** (hi.quanta)
    expected = x_vals * 2**x.quanta

    assert np.array_equal(reconstructed, expected)


if __name__ == "__main__":
    # test_mul_float(1.0, -15)
    # test_mul_float(0, -13)
    # test_mul_float(-2.6, 8)
    test_precision_split_reconstruction(-15)
