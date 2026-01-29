from fmot.fqir.writer import new_fqir_graph, FQIRWriter
import numpy as np
import pytest


@pytest.mark.parametrize("n_inputs", [1, 2, 4])
@pytest.mark.parametrize("channels", [1, 32, 64])
def test_interleave(n_inputs: int, channels: int):
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph)

    inputs = []
    for i in range(n_inputs):
        inputs.append(writer.add_input(channels, quanta=-15, precision="int16"))
    y = writer.interleave(inputs)
    writer.add_outputs([y])

    inputs = [np.random.randint(-1000, 1000, (4, channels)) for _ in range(n_inputs)]
    y = graph.run(*inputs)

    for i, x in enumerate(inputs):
        assert np.array_equal(x, y[..., i::n_inputs])
    print(f"✅ Interleave test passed with {n_inputs=}, {channels=}")


@pytest.mark.parametrize("n_inputs", [1, 2, 4])
@pytest.mark.parametrize("channels", [1, 32, 64])
def test_deinterleave(n_inputs: int, channels: int):
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph)

    x = writer.add_input(channels=channels * n_inputs, quanta=-15, precision="int16")
    outs = writer.deinterleave(x, channels=channels)
    writer.add_outputs(outs)

    # x = np.random.randint(-1000, 1000, (4, n_inputs * channels))
    x = np.arange(channels * n_inputs).reshape(1, -1)
    outs = graph.run(x)

    if channels == 1:
        outs = [outs]

    for i, y in enumerate(outs):
        assert np.array_equal(y, x[..., i::channels]), f"{i=} {y=} {x=}"
    print(f"✅ Deinterleave test passed with {n_inputs=}, {channels=}")


if __name__ == "__main__":
    test_deinterleave(1, 1)
    # test_interleave(4, 32)
    # test_deinterleave(4, 8)
