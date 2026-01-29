from fmot.fqir.writer import FQIRWriter, new_fqir_graph
import numpy as np
import pytest


def get_ema_fqir(channels: int, alpha: float, quanta=-15):
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph)
    x = writer.add_input(channels, quanta)
    y_prev = writer.add_zeros_buffer(channels, quanta)
    y_t = writer.add(
        writer.multiply(y_prev, alpha, quanta=quanta),
        writer.multiply(x, (1 - alpha), quanta=quanta),
        quanta=quanta,
    )
    writer.assign(y_prev, y_t)
    writer.add_outputs([y_t])

    return graph


@pytest.mark.parametrize("channels", [32])
@pytest.mark.parametrize("n_iter", [2, 3, 4])
def test_sequential_loop_nest_simple_ema(channels: int, n_iter: int):
    """Simple test-case: single input EMA nested as a loop of n_iter iterations"""

    # get a simple EMA graph
    ema = get_ema_fqir(channels, 0.9, quanta=-15)

    # nest this into a multi-time-step graph
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph)
    x = writer.add_input(channels * n_iter, quanta=-15)
    (y,) = writer.inline_fqir_graph_in_sequential_loop(
        n_iter=n_iter, inputs=[x], graph=ema
    )
    writer.add_outputs([y])

    # run and compare these two
    T = 10
    x = np.random.randint(low=-1000, high=1000, size=(T * n_iter, channels))
    print(graph)

    y0 = ema.run(x)

    y1 = graph.run(x.reshape(T, channels * n_iter))

    y1 = y1.reshape(T * n_iter, channels)

    assert np.array_equal(y0, y1)

    print("SUCCESS!")


def get_case2_graph(channels: int):
    """Two buffers recieve the same update --> this was causing AEC to fail"""
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph)
    x = writer.add_input(channels, -15)
    b0 = writer.add_zeros_buffer(channels, -15)
    b1 = writer.add_zeros_buffer(channels, -15)
    y = writer.add(b0, b1, quanta=-15)
    writer.assign(b0, x)
    writer.assign(b1, x)
    writer.add_outputs([y])
    return graph


@pytest.mark.parametrize("channels", [32])
@pytest.mark.parametrize("n_iter", [2, 3, 4])
def test_sequential_loop_nest_case2(channels: int, n_iter: int):
    """Simple test-case: graph has multiple buffers that recieve updates *from the same source*
    this testcase isolates the core issue that was causing AEC merging to fail.
    """

    # get a graph with two buffers that recieve the same update
    orig = get_case2_graph(channels)

    # nest this into a multi-time-step graph
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph)
    x = writer.add_input(channels * n_iter, quanta=-15)
    (y,) = writer.inline_fqir_graph_in_sequential_loop(
        n_iter=n_iter, inputs=[x], graph=orig
    )
    writer.add_outputs([y])

    # run and compare these two
    T = 10
    x = np.random.randint(low=-1000, high=1000, size=(T * n_iter, channels))
    print(graph)

    y0 = orig.run(x)

    y1 = graph.run(x.reshape(T, channels * n_iter))

    y1 = y1.reshape(T * n_iter, channels)

    assert np.array_equal(y0, y1)

    print("SUCCESS!")


@pytest.mark.parametrize("channels", [32])
@pytest.mark.parametrize("n_iter", [2, 3, 4])
def test_parallel_loop_nest_simple_ema(channels: int, n_iter: int):
    # get a simple EMA graph
    ema = get_ema_fqir(channels, 0.9, quanta=-15)

    # nest this into a multi-time-step graph
    looped_ema = new_fqir_graph()
    writer = FQIRWriter.from_fqir(looped_ema)
    x = writer.add_input(channels * n_iter, quanta=-15)
    (y,) = writer.inline_fqir_graph_in_parallel_loop(
        n_iter=n_iter, inputs=[x], graph=ema
    )
    writer.add_outputs([y])

    # run and compare these two
    T = 10
    x = np.random.randint(low=-1000, high=1000, size=(T, channels * n_iter))
    # print(looped_ema)

    y0 = []
    for i in range(n_iter):
        y0.append(ema.run(x[:, i * channels : (i + 1) * channels]))
    y0 = np.concatenate(y0, axis=-1)
    print("unlooped ema ran!")

    y1 = looped_ema.run(x)

    print("looped ema ran!")

    assert np.array_equal(y0, y1)

    print("SUCCESS!")


@pytest.mark.parametrize("channels", [32])
@pytest.mark.parametrize("n_iter", [2, 3, 4])
def get_multiply_ema_fqir(channels: int, alpha: float, quanta=-15):
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph)
    a = writer.add_input(channels, quanta)
    b = writer.add_input(channels, quanta)
    x = writer.multiply(a, b, quanta=-15)
    y_prev = writer.add_zeros_buffer(channels, quanta)
    y_t = writer.add(
        writer.multiply(y_prev, alpha, quanta=quanta),
        writer.multiply(x, (1 - alpha), quanta=quanta),
        quanta=quanta,
    )
    writer.assign(y_prev, y_t)
    writer.add_outputs([y_t])

    return graph


@pytest.mark.parametrize("channels", [32])
@pytest.mark.parametrize("n_iter", [2, 3, 4])
def test_parallel_loop_nest_scope_ema(channels: int, n_iter: int):
    # 2-input EMA, first input is sliced, second input is reused scope

    # get 2-input EMA graph
    ema = get_multiply_ema_fqir(channels, 0.9, quanta=-15)

    # nest this into a multi-time-step graph
    looped_ema = new_fqir_graph()
    writer = FQIRWriter.from_fqir(looped_ema)
    a = writer.add_input(channels * n_iter, quanta=-15)
    b = writer.add_input(channels, quanta=-15)
    (y,) = writer.inline_fqir_graph_in_parallel_loop(
        n_iter=n_iter, inputs=[a, b], scope_indices=[1], graph=ema
    )
    writer.add_outputs([y])

    # run and compare these two
    T = 10
    a = np.random.randint(low=-1000, high=1000, size=(T, channels * n_iter))
    b = np.random.randint(low=-1000, high=1000, size=(T, channels))
    # print(looped_ema)

    y0 = []
    for i in range(n_iter):
        y0.append(ema.run(a[:, i * channels : (i + 1) * channels], b))
    y0 = np.concatenate(y0, axis=-1)
    print("unlooped ema ran!")

    y1 = looped_ema.run(a, b)

    print("looped ema ran!")

    assert np.array_equal(y0, y1)

    print("SUCCESS!")


if __name__ == "__main__":
    # test_sequential_loop_nest_simple_ema(32, 3)
    test_sequential_loop_nest_case2(32, 3)
    test_parallel_loop_nest_simple_ema(32, 3)
    test_parallel_loop_nest_scope_ema(32, 3)
