import numpy as np
from fmot.fqir.writer import new_fqir_graph, FQIRWriter
from fmot.fqir.writer.kernels import write_distributed_flat_linear
import matplotlib.pyplot as plt
import pytest

ERROR_TOL = 2.3e-1


@pytest.mark.parametrize("in_channels", [8])
@pytest.mark.parametrize("out_channels", [8])
@pytest.mark.parametrize("pad_pre", [0, 10])
@pytest.mark.parametrize("kernel_size", [5, 55])
@pytest.mark.parametrize("pad_post", [0, 10])
@pytest.mark.parametrize("bias", [True, False])
def test_distributed_flat_linear_kernel(
    in_channels: int,
    out_channels: int,
    pad_pre: int,
    kernel_size: int,
    pad_post: int,
    bias: bool,
    plot=False,
):
    np.random.seed(0)

    Q_IN = -15
    Q_WEIGHT = -17
    Q_OUT = -15
    Q_BIAS = -22

    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph)

    x_t = writer.add_input(in_channels, quanta=Q_IN)

    weight = np.random.randint(
        low=-(2**7), high=2**7 - 1, size=(out_channels, in_channels * kernel_size)
    )
    if bias:
        bias = np.random.randint(low=-(2**15), high=2**15 - 1, size=(out_channels,))
    else:
        bias = None

    y_t, intermediates = write_distributed_flat_linear(
        writer,
        x_t,
        weight,
        pad_pre=pad_pre,
        in_channels=in_channels,
        out_channels=out_channels,
        kernel_size=kernel_size,
        pad_post=pad_post,
        quanta_weight=Q_WEIGHT,
        quanta_out=Q_OUT,
        quanta_bias=Q_BIAS,
        bias=bias,
        precision="int16",
        dot_method="tree",
        debug=True,
    )

    writer.add_outputs([y_t] + list(intermediates.values()))

    T = pad_pre + kernel_size + pad_post

    x = np.random.randint(low=-(2**15), high=2**15 - 1, size=(T, in_channels))
    y_fqir = graph.run(x)[0]

    weight = weight.reshape(out_channels, in_channels, kernel_size)
    weight = np.permute_dims(weight, (0, 2, 1))
    weight = weight.reshape(out_channels, -1)

    y_expected = x[pad_pre : pad_pre + kernel_size].flatten() @ weight.T
    if bias is not None:
        sh_bias = Q_BIAS - Q_IN - Q_WEIGHT
        if sh_bias >= 0:
            bias = bias << sh_bias
        else:
            bias = bias >> -sh_bias
        y_expected = y_expected + bias

    y_expected = y_expected >> (Q_OUT - Q_IN - Q_WEIGHT)

    nmse = np.mean((y_expected - y_fqir[-1]) ** 2) / np.mean(y_expected**2)
    print(nmse)
    assert nmse <= ERROR_TOL

    if plot:
        plt.plot(y_fqir[-1], y_expected, ".")
        plt.plot(y_expected, y_expected, "k--")
        plt.show()

        x = np.random.randint(
            low=-(2**15), high=2**15 - 1, size=(3 * T, in_channels)
        )
        outs = graph.run(x)

        plt.plot(outs[0][:, 0])
        plt.show()

        window_size = kernel_size + pad_pre + pad_post

        for name, out in zip(intermediates.keys(), outs[1:]):
            vm = np.max(np.abs(out))
            plt.pcolormesh(out.T, vmin=-vm, vmax=vm, cmap="bwr")
            plt.title(name)
            plt.xlabel("step")
            for i in range(3):
                plt.axvline(i * window_size, color="k")
                plt.axvline(i * window_size + pad_pre, color="r")
                plt.axvline(i * window_size + pad_pre + kernel_size, color="cyan")
            plt.show()


if __name__ == "__main__":
    test_distributed_flat_linear_kernel(
        in_channels=16,
        out_channels=16,
        pad_pre=10,
        kernel_size=55,
        pad_post=0,
        bias=False,
        plot=False,
    )
