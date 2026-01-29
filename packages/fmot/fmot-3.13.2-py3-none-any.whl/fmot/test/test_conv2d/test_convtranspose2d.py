import torch
import fmot
from fmot.nn import TemporalConvTranspose2d, TemporalConv2d
import pytest


@pytest.mark.parametrize(
    ["d_band_in", "d_band_out", "groups"], [[32, 32, 32], [16, 32, 1]]
)
@pytest.mark.parametrize("n_band_in", [8])
@pytest.mark.parametrize(["kernel_t", "dilation_t"], [[1, 1], [3, 1], [3, 3]])
@pytest.mark.parametrize(
    ["kernel_band", "stride_band", "padding_band", "padding_band_out"],
    [[3, 2, 1, 0], [3, 2, 1, 1], [1, 1, 0, 0]],
)
@pytest.mark.parametrize("bias", [True, False])
def test_tconv2d(
    d_band_in: int,
    n_band_in: int,
    d_band_out: int,
    kernel_band: int,
    kernel_t: int,
    dilation_t: int,
    stride_band: int,
    padding_band: int,
    padding_band_out: int,
    bias: bool,
    groups: int,
):
    model = TemporalConvTranspose2d(
        d_band_in=d_band_in,
        n_band_in=n_band_in,
        d_band_out=d_band_out,
        kernel_band=kernel_band,
        kernel_t=kernel_t,
        dilation_t=dilation_t,
        stride_band=stride_band,
        padding_band=padding_band,
        padding_band_out=padding_band_out,
        bias=bias,
        groups=groups,
    )

    print(model)
    x = torch.randn(8, d_band_in * n_band_in, 10)
    y = model(x)
    d_out = y.shape[1]

    assert d_out // model.n_band_out == d_band_out

    cmodel = fmot.ConvertedModel(model, batch_dim=0, seq_dim=2)
    cmodel.quantize([torch.randn(8, d_band_in * n_band_in, 10) for _ in range(2)])
    graph = cmodel.trace()


if __name__ == "__main__":
    test_tconv2d(
        d_band_in=32,
        n_band_in=8,
        d_band_out=32,
        kernel_band=1,
        kernel_t=1,
        dilation_t=1,
        stride_band=1,
        padding_band=0,
        padding_band_out=0,
        bias=False,
        groups=1,
    )
