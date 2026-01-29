from fmot.fqir.writer import FQIRWriter
import numpy as np
from fmot.fqir import GraphProto, TensorProto
import pytest


def test_gt0():
    graph = GraphProto()
    x = TensorProto(
        name="x",
        shape=[
            1000,
        ],
        dtype="fqint16",
        quanta=-15,
    )
    graph.add_input(x)

    writer = FQIRWriter(graph, None, "int16")
    z = writer.gt0(x)

    graph.add_output(z)

    x_vals = np.random.uniform(-(2**15), 2**15 - 1, 1000)
    z_vals = graph.run(x_vals)

    z_expected = (x_vals > 0).astype(int)

    assert np.array_equal(z_vals, z_expected)


def test_logical_not():
    graph = GraphProto()
    x = TensorProto(
        name="x",
        shape=[
            1000,
        ],
        dtype="fqint16",
        quanta=0,
    )
    graph.add_input(x)

    writer = FQIRWriter(graph, None, "int16")
    not_x = writer.logical_not(x)
    graph.add_output(not_x)

    x = np.random.randn(1000)
    x = (x > 0).astype(int)

    outs = graph.run(x)

    assert np.array_equal(outs, np.logical_not(x.astype(bool)).astype(int))


def test_logical_and():
    graph = GraphProto()
    x = TensorProto(
        name="x",
        shape=[
            1000,
        ],
        dtype="fqint16",
        quanta=0,
    )
    graph.add_input(x)
    y = TensorProto(
        name="y",
        shape=[
            1000,
        ],
        dtype="fqint16",
        quanta=0,
    )
    graph.add_input(y)

    writer = FQIRWriter(graph, None, "int16")
    and_xy = writer.logical_and(x, y)

    graph.add_output(and_xy)

    x = np.random.randn(1000)
    x = x > 0
    y = np.random.randn(1000)
    y = y > 0

    out = graph.run(x.astype(int), y.astype(int))
    expected = np.logical_and(x, y).astype(int)

    assert np.array_equal(out, expected)


def test_logical_or():
    graph = GraphProto()
    x = TensorProto(
        name="x",
        shape=[
            1000,
        ],
        dtype="fqint16",
        quanta=0,
    )
    graph.add_input(x)
    y = TensorProto(
        name="y",
        shape=[
            1000,
        ],
        dtype="fqint16",
        quanta=0,
    )
    graph.add_input(y)

    writer = FQIRWriter(graph, None, "int16")
    or_xy = writer.logical_or(x, y)

    graph.add_output(or_xy)

    x = np.random.randn(1000)
    x = x > 0
    y = np.random.randn(1000)
    y = y > 0

    out = graph.run(x.astype(int), y.astype(int))
    expected = np.logical_or(x, y).astype(int)

    assert np.array_equal(out, expected)


def test_logical_xor():
    graph = GraphProto()
    x = TensorProto(
        name="x",
        shape=[
            1000,
        ],
        dtype="fqint16",
        quanta=0,
    )
    graph.add_input(x)
    y = TensorProto(
        name="y",
        shape=[
            1000,
        ],
        dtype="fqint16",
        quanta=0,
    )
    graph.add_input(y)

    writer = FQIRWriter(graph, None, "int16")
    xor_xy = writer.logical_xor(x, y)

    graph.add_output(xor_xy)

    x = np.random.randn(1000)
    x = x > 0
    y = np.random.randn(1000)
    y = y > 0

    out = graph.run(x.astype(int), y.astype(int))
    expected = np.logical_xor(x, y).astype(int)

    assert np.array_equal(out, expected)


if __name__ == "__main__":
    # test_gt0()
    test_logical_not()
