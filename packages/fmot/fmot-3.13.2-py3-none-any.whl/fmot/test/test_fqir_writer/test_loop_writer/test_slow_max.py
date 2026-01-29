from fmot.fqir.writer import FQIRWriter
import numpy as np
from fmot.fqir import GraphProto, TensorProto
import pytest


@pytest.mark.parametrize("quanta_in", [-15, -19, -13, 0])
@pytest.mark.parametrize("n_channels", [7, 31, 555])
def test_slow_max(quanta_in: int, n_channels: int):
    """Implement a slow O(N) max -- by taking a running max over each individual element of the tensor"""
    graph = GraphProto()

    x = TensorProto(
        name="x",
        shape=[
            n_channels,
        ],
        dtype="fqint16",
        quanta=quanta_in,
    )
    graph.add_input(x)

    writer = FQIRWriter(graph, None, "int16")
    initial_max = writer.add_parameter(np.zeros([1]), quanta=x.quanta)

    with writer.for_loop_writer(
        n_iter=n_channels, x_to_slice=[x], x_recurse_init=[initial_max]
    ) as lwriter:
        (curr_x,) = lwriter.sliced_inputs
        (prev_max,) = lwriter.recursed_inputs

        gt = lwriter.gt(curr_x, prev_max)
        not_gt = lwriter.logical_not(gt)
        masked_prev = lwriter.multiply(prev_max, not_gt, quanta=x.quanta)
        masked_x = lwriter.multiply(curr_x, gt, quanta=x.quanta)
        new_max = lwriter.add(masked_prev, masked_x, quanta=x.quanta)

        lwriter.update_recursed_state(prev_max, new_max)
        final_max = lwriter.return_final(new_max)

    graph.add_output(final_max)

    print(graph)

    x_val = np.random.uniform(size=n_channels, low=-(2**15), high=2**15 - 1).astype(
        np.int32
    )
    y_val = graph.run(x_val)

    y_exp = np.max(x_val, keepdims=True)

    print(y_exp)
    print(y_val)

    assert np.array_equal(y_val, y_exp)


if __name__ == "__main__":
    test_slow_max(-15, 100)
