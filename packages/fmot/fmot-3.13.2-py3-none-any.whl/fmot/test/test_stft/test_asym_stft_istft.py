import torch
from fmot.nn.fft import STFT, ISTFT, design_wola, check_wola
import pytest


@pytest.mark.parametrize(
    ["hop_size", "n_fft", "window_size", "synth_size", "lookahead"],
    [
        [16, 256, 128, 128, 0],  # padded STFT; 8 hops of overlap
        [
            16,
            256,
            128,
            32,
            32,
        ],  # padded STFT; asymmetric windowing (2 frame overlap); 32 sample stagger
        [
            16,
            256,
            128,
            64,
            17,
        ],  # padded STFT; asymmetric windowing (4 frame overlap); 17 sample stagger
    ],
)
def test_asym_stft(
    hop_size: int, n_fft: int, window_size: int, synth_size: int, lookahead: int
):
    window = torch.hann_window(window_size)
    stft = STFT(n_fft, hop_size, window_size=window_size, window_fn=window)

    synth_window = design_wola(window, hop_size, synth_size, lookahead)

    check_wola(window, synth_window, hop_size, lookahead)

    istft = ISTFT(
        n_fft, hop_size, window_size, synth_size, window, synth_window, lookahead
    )

    x = torch.randn(8, 100, hop_size)
    re, im = stft(x)
    y = istft(re, im)

    x = x.reshape(8, -1)
    y = y.reshape(8, -1)

    ola_delay = hop_size * (synth_size // hop_size - 1) + lookahead

    # check for low reconstruction error
    error = torch.norm(x[:, :-ola_delay] - y[:, ola_delay:])
    assert error < 1e-4
    print(f"STFT-ISTFT reconstruction error: {error}")


if __name__ == "__main__":
    hop = 16
    n_fft = 256
    window_size = 128
    synth_size = 64
    lookahead = 16

    test_asym_stft(hop, n_fft, window_size, synth_size, lookahead)
