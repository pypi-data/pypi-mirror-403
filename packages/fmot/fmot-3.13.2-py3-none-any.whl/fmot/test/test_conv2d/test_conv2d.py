import torch
import fmot
from torch import nn, Tensor
import numpy as np
import pytest
from fmot.nn.conv import UnsupportedConvParametersError


def test_fp_temporal_conv2d():
    D_BAND = 16
    N_BAND = 3
    layer = fmot.nn.TemporalConv2d(
        d_band_in=D_BAND,
        n_band_in=N_BAND,
        d_band_out=8,
        kernel_t=1,
        kernel_band=1,
        dilation_t=1,
        dilation_band=1,
        padding_band=0,
        stride_band=1,
        bias=True,
    )

    # layer.weight.data[:] = 0
    layer.bias.data[:] = 0

    x = torch.randn(8, D_BAND * N_BAND, 10)
    y0 = layer(x)

    layer.bias.data[:] = 1
    y1 = layer(x)

    assert torch.allclose(y1 - y0, torch.ones_like(y1))

    cmodel = fmot.ConvertedModel(layer, batch_dim=0, seq_dim=2)
    y2 = cmodel(x)
    assert torch.all(y2 == y1)


@pytest.mark.parametrize("kernel_t", [1, 3])
@pytest.mark.parametrize("kernel_band", [1, 3])
@pytest.mark.parametrize("dilation_t", [1, 2])
@pytest.mark.parametrize("dilation_band", [1, 2])
@pytest.mark.parametrize("padding_band", [0, 1])
@pytest.mark.parametrize("stride_band", [1, 2])
@pytest.mark.parametrize("bias", [True, False])
@pytest.mark.parametrize("depthwise", [False, True])
def test_quant_temporal_conv2d(
    kernel_t,
    kernel_band,
    dilation_t,
    dilation_band,
    padding_band,
    stride_band,
    bias,
    depthwise,
    plot=False,
):
    D_BAND = 8
    N_BAND = 5 * dilation_band
    D_BAND_OUT = D_BAND

    layer = fmot.nn.TemporalConv2d(
        d_band_in=D_BAND,
        n_band_in=N_BAND,
        d_band_out=D_BAND_OUT,
        kernel_t=kernel_t,
        kernel_band=kernel_band,
        dilation_t=dilation_t,
        dilation_band=dilation_band,
        padding_band=padding_band,
        stride_band=stride_band,
        bias=bias,
        groups=1 if not depthwise else D_BAND,
    )

    cmodel = fmot.ConvertedModel(layer, batch_dim=0, seq_dim=2)
    cmodel.quantize([torch.randn(8, D_BAND * N_BAND, 15) for _ in range(4)])

    x = torch.randn(8, D_BAND * N_BAND, 15)
    y0 = layer(x)
    y1 = cmodel(x)

    nmse = (y0 - y1).pow(2).mean() / y0.pow(2).mean()
    assert nmse < 4e-3

    graph = cmodel.trace()
    print("Traced...")

    x = x[0]
    y_fmot = cmodel(x.unsqueeze(0))[0].detach().numpy()
    y_fqir = graph.run(x.numpy(), dequant=True)

    print(graph)

    diff = y_fmot - y_fqir
    print(f"max diff: {np.max(np.abs(diff))}")

    if plot:
        import matplotlib.pyplot as plt

        plt.plot(y_fmot.flatten(), y_fqir.flatten(), ".")
        plt.xlabel("fmot")
        plt.ylabel("fqir")
        plt.show()

    assert np.all(y_fmot == y_fqir), f"max_diff: {np.max(np.abs(diff))}"


if __name__ == "__main__":
    test_fp_temporal_conv2d()
    test_quant_temporal_conv2d(1, 1, 1, 1, 0, 1, bias=True, depthwise=False, plot=False)
    test_quant_temporal_conv2d(1, 1, 1, 1, 0, 1, bias=True, depthwise=True, plot=False)
