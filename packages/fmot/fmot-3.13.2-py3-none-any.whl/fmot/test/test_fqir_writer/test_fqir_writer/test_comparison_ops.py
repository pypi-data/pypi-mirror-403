import numpy as np
from fmot.fqir.writer import new_fqir_graph, FQIRWriter
from typing import Optional
import pytest


@pytest.mark.parametrize("precision", ["int16", "int24"])
@pytest.mark.parametrize(
    ["op", "value", "input", "output"],
    [
        ["gt0", None, [-1, 0, 1], [0, 0, 1]],
        ["gt", 0, [-1, 0, 1], [0, 0, 1]],
        ["gte", 0, [-1, 0, 1], [0, 1, 1]],
        ["lt", 0, [-1, 0, 1], [1, 0, 0]],
        ["lte", 0, [-1, 0, 1], [1, 1, 0]],
        ["eq", 0, [-1, 0, 1], [0, 1, 0]],
    ],
)
def test_comparison_op(
    op: str, value: Optional[float], precision: str, input: list[int], output: list[int]
):
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph, precision)

    x = writer.add_input(len(input), -15, precision="fq" + precision)
    if op == "gt0":
        y = writer.gt0(x)
    elif op == "gt":
        y = writer.gt(x, value)
    elif op == "gte":
        y = writer.ge(x, value)
    elif op == "lt":
        y = writer.lt(x, value)
    elif op == "lte":
        y = writer.le(x, value)
    elif op == "eq":
        y = writer.eq(x, value)
    else:
        raise ValueError(f"op {op} not defined")
    writer.add_outputs([y])

    x = np.array(input).reshape(1, -1)
    y = graph.run(x, dequant=False)[0]

    if not np.array_equal(y, np.array(output)):
        raise ValueError(
            f"expected output {output}, got {y.tolist()} for {op}({input}, {value})"
        )
