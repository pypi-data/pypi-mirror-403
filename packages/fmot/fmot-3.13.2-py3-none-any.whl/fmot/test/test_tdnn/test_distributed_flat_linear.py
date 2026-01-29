import torch
import fmot
from fmot.nn import CumulativeFlattenedLinear
import numpy as np
import pytest

ETOL = 1e-1


@pytest.mark.parametrize("in_channels", [16, 32])
@pytest.mark.parametrize("out_channels", [2, 16])
@pytest.mark.parametrize("padding", [0, 17])
@pytest.mark.parametrize("kernel_size", [45, 67])
@pytest.mark.parametrize("bias", [True, False])
def test_distributed_flattened_linear(
    in_channels, out_channels, padding, kernel_size, bias
):
    torch.manual_seed(0)
    seq_length = padding + kernel_size
    model = CumulativeFlattenedLinear(
        seq_length=seq_length,
        trim_frames=padding,
        channels_per_timestep=in_channels,
        out_channels=out_channels,
        bias=bias,
    )

    expected_shape = (out_channels, in_channels * kernel_size)
    window_size = kernel_size + padding

    _ = model(torch.randn(8, in_channels, window_size))

    cmodel = fmot.ConvertedModel(model, batch_dim=0, seq_dim=2)
    cmodel.quantize([torch.randn(8, in_channels, window_size) for _ in range(4)])
    graph = cmodel.trace()

    print(graph.subgraphs["ARITH"])

    np.random.seed(0)

    x = np.random.randn(in_channels, window_size)
    y = graph.run(x, dequant=True)

    y_expected = (
        cmodel(torch.as_tensor(x).float().unsqueeze(0)).squeeze(0).detach().numpy()
    )

    error = np.mean((y_expected - y) ** 2)
    nmse = error / np.mean(y_expected**2)
    print(nmse)

    assert nmse <= ETOL


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    test_distributed_flattened_linear(16, 2, 5, 10, False)
