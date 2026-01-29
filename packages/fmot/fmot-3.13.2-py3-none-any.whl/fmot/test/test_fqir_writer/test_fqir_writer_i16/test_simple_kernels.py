from fmot.fqir.writer import FQIRWriter
import numpy as np
from fmot.fqir import GraphProto, TensorProto
import pytest


@pytest.mark.parametrize("quanta_in", [-15, -19, -13, 0])
def test_one_minus_x(quanta_in: int):
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
    # negate x
    xneg = writer.multiply(x, -1)
    # add 1
    y = writer._add_float(xneg, 1)

    graph.add_output(y)

    x_vals = np.linspace(-(2**15), 2**15 - 1, 1000, dtype=np.int32)
    y_vals = graph.run(x_vals)

    y_expected = (1 - x_vals * 2 ** (quanta_in)) / 2 ** (y.quanta)

    max_err = np.max(np.abs(y_vals - y_expected))

    print(max_err)
    assert max_err <= 2


@pytest.mark.parametrize("quanta_in", [-15, -7, 0, 7])
def test_sign(quanta_in: int):
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
    y = writer.sign(x)
    graph.add_output(y)

    x_vals = np.linspace(-(2**15), 2**15 - 1, 1000, dtype=np.int32)
    y_vals = graph.run(x_vals)

    y_expected = np.sign(x_vals) / 2 ** (y.quanta)

    if not np.array_equal(y_vals, y_expected):
        num_diffs = np.sum(y_vals != y_expected)
        print(num_diffs)
        raise ValueError(f"sign differed on {num_diffs} input values")


if __name__ == "__main__":
    test_sign(-15)
