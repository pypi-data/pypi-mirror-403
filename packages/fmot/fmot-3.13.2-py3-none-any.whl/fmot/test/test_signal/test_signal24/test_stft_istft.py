import torch
from torch import nn, Tensor
from fmot.precisions import int16, int24, int8
from fmot.beta.signal24 import STFT, ISTFT
import fmot
import pytest


class IdentityOLA(nn.Module):
    def __init__(
        self, hop_length, window_length, act_precision=int16, weight_precision=int8
    ):
        super().__init__()

        window_fn = torch.hann_window(window_length)

        self.stft = STFT(
            n_fft=window_length,
            hop_size=hop_length,
            n_stages="auto",
            act_precision=act_precision,
            weight_precision=weight_precision,
            window_size=window_length,
            window_fn=window_fn,
        )
        self.istft = ISTFT(
            n_fft=window_length,
            hop_size=hop_length,
            n_stages="auto",
            act_precision=act_precision,
            weight_precision=weight_precision,
            window_size=window_length,
            window_fn=window_fn,
        )

    def forward(self, x):
        (re, im), _ = self.stft(x)
        out = self.istft(re, im)
        return out


def get_pure_tone_calib(
    batch_size: int, num_batches: int, num_frames: int, hop_length: int
):
    num_freqs = batch_size * num_batches
    periods = torch.logspace(1e2 * num_freqs, 1, num_freqs)
    time = torch.arange(num_frames * hop_length)
    waveforms = torch.sin(2 * torch.pi / periods.unsqueeze(1) * time.unsqueeze(0))

    batches = []
    for i in range(num_batches):
        batches.append(
            waveforms[i * batch_size : (i + 1) * batch_size].reshape(
                batch_size, num_frames, hop_length
            )
        )

    return batches


@pytest.mark.parametrize(["hop_length", "window_length"], [[128, 256]])
@pytest.mark.parametrize("act_precision", [int16, int24])
@pytest.mark.parametrize("weight_precision", [int8, int16])
def test_identity_ola(hop_length, window_length, act_precision, weight_precision):
    torch.manual_seed(0)

    model = IdentityOLA(hop_length, window_length, act_precision, weight_precision)
    cmodel = fmot.ConvertedModel(model, batch_dim=0, seq_dim=1)
    cmodel.set_input_details(0, -15)
    cmodel.set_output_details(0, -15)

    calib = get_pure_tone_calib(8, 8, 20, hop_length)
    cmodel.quantize(calib)

    graph = cmodel.trace()

    # evaluate quantized
    x = torch.randn(8, 100, hop_length)
    x = x / torch.max(torch.abs(x))
    y = cmodel(x)
    # y = model(x)
    tgt = x[:, :-1]
    est = y[:, 1:]

    qsnr = 10 * torch.log10(torch.sum(tgt**2) / (torch.sum((tgt - est) ** 2)))

    print(f"{act_precision}x{weight_precision} -> qsnr: {qsnr:.3f} dB")


if __name__ == "__main__":
    test_identity_ola(128, 256, int24, int16)
    test_identity_ola(128, 256, int16, int8)
    test_identity_ola(128, 256, int16, int16)
    test_identity_ola(128, 256, int24, int8)
