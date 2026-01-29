from fmot.fqir.writer import FQIRWriter
import numpy as np
from fmot.fqir import GraphProto, TensorProto
import pytest


@pytest.mark.parametrize("precision", ["int16", "int24"])
@pytest.mark.parametrize(["quanta_x", "quanta_y"], [[-15, -12], [-15, -15], [-7, 7]])
def test_add_tensors(quanta_x: int, quanta_y: int, precision: str):
    graph = GraphProto()

    x = TensorProto(
        name="x",
        shape=[
            10000,
        ],
        dtype=f"fq{precision}",
        quanta=quanta_x,
    )
    y = TensorProto(
        name="y",
        shape=[
            10000,
        ],
        dtype=f"fq{precision}",
        quanta=quanta_y,
    )
    graph.add_input(x)
    graph.add_input(y)

    writer = FQIRWriter(graph, None, act_precision=precision)
    z = writer.add(x, y)

    graph.add_output(z)

    bw = int(precision.split("int")[1])

    vals = np.linspace(-(2 ** (bw - 1)), 2 ** (bw - 1) - 1, 100, dtype=np.int32)
    x_vals, y_vals = np.meshgrid(vals, vals)

    z_vals = graph.run(x_vals, y_vals)

    z_expected = (x_vals * 2 ** (quanta_x) + y_vals * 2 ** (quanta_y)) / 2 ** (z.quanta)

    max_err = np.max(np.abs(z_vals - z_expected))

    print(f"{precision=} {np.max(np.abs(z_vals))=}")
    print(max_err)
    assert max_err <= 2


@pytest.mark.parametrize("precision", ["int16", "int24"])
@pytest.mark.parametrize(["quanta_x", "quanta_y"], [[-15, -12], [-15, -15], [-7, 7]])
def test_mul_tensors(quanta_x: int, quanta_y: int, precision: str):
    graph = GraphProto()

    x = TensorProto(
        name="x",
        shape=[
            10000,
        ],
        dtype=f"fq{precision}",
        quanta=quanta_x,
    )
    y = TensorProto(
        name="y",
        shape=[
            10000,
        ],
        dtype=f"fq{precision}",
        quanta=quanta_y,
    )
    graph.add_input(x)
    graph.add_input(y)

    writer = FQIRWriter(graph, None, precision)
    z = writer.multiply(x, y)

    graph.add_output(z)

    bw = int(precision.split("int")[1])

    vals = np.linspace(-(2 ** (bw - 1)), 2 ** (bw - 1) - 1, 100, dtype=np.int32)
    x_vals, y_vals = np.meshgrid(vals, vals)

    z_vals = graph.run(x_vals, y_vals)

    z_expected = (x_vals * 2 ** (quanta_x) * y_vals * 2 ** (quanta_y)) / 2 ** (z.quanta)

    max_err = np.max(np.abs(z_vals - z_expected))

    print(max_err)
    assert max_err <= 2
