import torch
import fmot
from fmot.nn import STFT
import pytest


@pytest.mark.parametrize(["window_size", "hop_size"], [[512, 160]])
def test_stft_window_hop_nondivisible(window_size: int, hop_size: int):
    stft = STFT(
        window_size, hop_size, window_size, window_fn=torch.hann_window(window_size)
    )

    cmodel = fmot.ConvertedModel(stft, batch_dim=0, seq_dim=1)
    cmodel.quantize([torch.randn(8, 10, hop_size) for _ in range(4)])
    graph = cmodel.trace()

    print(f"Success! STFT with {window_size=} and {hop_size=} converted and traced")

    x = torch.randn(8, 10, hop_size)
    y_re, y_im = cmodel(x)
    assert y_re.shape[-1] == window_size // 2 + 1
    print("Success! has the correct number of output channels")


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    test_stft_window_hop_nondivisible(512, 160)
