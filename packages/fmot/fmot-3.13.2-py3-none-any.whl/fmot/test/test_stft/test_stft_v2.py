import torch
from torch import nn
import fmot
import pathlib
from functools import partial
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample

HERE = pathlib.Path(__file__).parent


def get_audio():
    sr, audio = wavfile.read(str(HERE / "stft_test_audio.wav"))
    audio = resample(audio, int(len(audio) * 16000 / sr))
    audio = audio[: 16000 * 2]
    return audio


class IdentityOla(nn.Module):
    def __init__(
        self,
        hop_len,
        win_len,
        stft_cls: type[nn.Module],
        istft_cls: type[nn.Module],
        n_stages=3,
    ):
        super().__init__()
        window_fn = torch.hann_window(win_len)
        self.stft = stft_cls(win_len, hop_len, n_stages=n_stages, window_fn=window_fn)
        self.istft = istft_cls(win_len, hop_len, n_stages=n_stages, window_fn=window_fn)

    def forward(self, x):
        re, im = self.stft(x)
        return self.istft(re, im)


def _test_stft(hop_len=64, win_len=128, n_stages="auto", v2=True, plot=False):
    if v2:
        stft_cls = partial(fmot.nn.STFT, norm_min="auto", weight_precision=16)
        istft_cls = partial(fmot.nn.ISTFT, norm_min="auto", weight_precision=16)
    else:
        stft_cls = partial(fmot.nn.STFT, norm_min=None, weight_precision=8)
        istft_cls = partial(fmot.nn.ISTFT, norm_min=None, weight_precision=8)
    ola = IdentityOla(
        hop_len, win_len, stft_cls=stft_cls, istft_cls=istft_cls, n_stages=n_stages
    )

    audio = get_audio()

    x = torch.as_tensor(audio).float()
    x = 0.99 * x / torch.max(torch.abs(x))
    T = len(x) // hop_len
    x = x[: hop_len * T]
    x = x.reshape(1, T, hop_len)
    x = x

    y = ola(x)

    cmodel = fmot.ConvertedModel(ola, batch_dim=0, seq_dim=1)

    calib = [x * 10 ** (g / 20) for g in [0, -10, -20, -30, -40, -50, -60, -70, -80]]
    calib = torch.cat(calib, 0)
    calib = [calib[:5], calib[5:], calib[:5]]
    cmodel.quantize(calib)

    qsnrs = []
    for gain_db in [0, -20, -40, -60, -70]:
        gain = 10 ** (gain_db / 20)
        y_q = cmodel(x * gain) / gain
        y_tgt = y

        qsnr = 10 * torch.log10((y_tgt).pow(2).mean() / (y_tgt - y_q).pow(2).mean())

        print(f"At {gain_db} dBFS, snr={qsnr.item():.3f}")

        if plot:
            import matplotlib.pyplot as plt

            plt.plot(y_tgt.flatten())
            plt.plot(y_q.flatten())
            plt.show()

        qsnrs.append(qsnr.detach().item())

    return qsnrs


def test_stft(hop_len=64, win_len=128, n_stages="auto"):
    print("STFT v1, no-round:")
    fmot.CONFIG.quant_round = False
    qsnrs_nr = _test_stft(hop_len, win_len, n_stages, v2=False)
    print("STFT v1, round:")
    qsnrs_r = _test_stft(hop_len, win_len, n_stages, v2=False)

    print("STFT v2, no-round:")
    fmot.CONFIG.quant_round = False
    qsnrs_v2_nr = _test_stft(hop_len, win_len, n_stages, v2=True)
    print("STFT v2, round:")
    fmot.CONFIG.quant_round = True
    qsnrs_v2_r = _test_stft(hop_len, win_len, n_stages, v2=True)

    v1_nr = np.mean(qsnrs_nr)
    v1_r = np.mean(qsnrs_r)
    v2_nr = np.mean(qsnrs_v2_nr)
    v2_r = np.mean(qsnrs_v2_r)

    print(
        f"Average QSNRS:\n\tv1 w/o rounding: {v1_nr}\n\tv1 w/ rounding: {v1_r}"
        f"\n\tv2 w/o rounding: {v2_nr}\n\tv2 w/ rounding: {v2_r}"
        f"\n overall improvement: {v2_r - v1_nr} dB"
    )

    assert v2_r - v1_nr > 5  # should be 10 dB of improvement, at least.


if __name__ == "__main__":
    # fmot.CONFIG.quant_round = True

    # print("v2 OLA:")
    # _test_stft(v2=True, plot=True)
    # print("v1 OLA:")
    # _test_stft(v2=False, plot=True)

    test_stft()
