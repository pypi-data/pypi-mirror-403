from fmot.fqir.writer import FQIRWriter
import numpy as np
from fmot.fqir import GraphProto, TensorProto
import pytest


@pytest.mark.parametrize("quanta", [-15, -3])
@pytest.mark.parametrize("n_channels", [7, 32, 155, 1])
@pytest.mark.parametrize("op", ["max", "min", "sum", "argmax", "argmin"])
def test_reduce(quanta: int, n_channels: int, op: str, print_fqir=False):
    graph = GraphProto()

    x = TensorProto(
        name="x",
        shape=[
            n_channels,
        ],
        dtype="fqint16",
        quanta=quanta,
    )
    graph.add_input(x)

    writer = FQIRWriter(graph, None, "int16")
    if op == "max":
        y = writer.max(x)
    elif op == "min":
        y = writer.min(x)
    elif op == "sum":
        y = writer.sum(x, method="tree")
    elif op == "argmax":
        y = writer.argmax(x)
    elif op == "argmin":
        y = writer.argmin(x)
    else:
        raise NotImplementedError(f"op: {op} is not a reduction op.")
    graph.add_output(y)

    x_val = np.random.uniform(size=n_channels, low=-(2**15), high=2**15 - 1).astype(
        np.int32
    )
    y_val = graph.run(x_val)

    if print_fqir:
        print(graph)

    if op == "max":
        y_exp = np.max(x_val, keepdims=True)
    elif op == "min":
        y_exp = np.min(x_val, keepdims=True)
    elif op == "sum":
        y_exp = (np.sum(x_val, keepdims=True) * 2 ** (x.quanta - y.quanta)).astype(
            np.int32
        )
    elif op == "argmax":
        y_exp = np.argmax(x_val, keepdims=True)
    elif op == "argmin":
        y_exp = np.argmin(x_val, keepdims=True)

    print(f"{y_exp=}, {y_val=}")

    if op in ["max", "min"]:
        atol = 2
    elif op in ["sum"]:
        atol = 8
    elif op in ["argmax", "argmin"]:
        atol = 0

    assert np.allclose(
        y_val, y_exp, atol=atol
    ), f"{atol=}, max_error={np.max(np.abs(y_val - y_exp))}"


if __name__ == "__main__":
    test_reduce(-15, 312, "sum", print_fqir=True)
    # test_reduce(-15, 312, "min")
