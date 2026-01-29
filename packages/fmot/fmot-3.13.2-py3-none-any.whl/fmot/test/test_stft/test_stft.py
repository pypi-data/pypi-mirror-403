import math
import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

import fmot


class Model(nn.Module):
    """Dooes a Fourier transform with asymmetric window"""

    def __init__(self, n_fft=512):
        super().__init__()
        self.hop_length = n_fft // 4

        N_1 = int(3 / 4 * n_fft)
        N_2 = int(1 / 4 * n_fft)
        self.asym_window = nn.Parameter(
            torch.tensor(
                [np.sin(np.pi / 2 * n / N_1) for n in range(N_1)]
                + [np.cos(np.pi / 2 * n / N_2) for n in range(N_2)],
                dtype=torch.float32,
            ),
            requires_grad=False,
        )
        self.stft_kwargs = {
            "n_fft": n_fft,
            "hop_length": self.hop_length,
            "win_length": n_fft,
            "window": self.asym_window,
            "return_complex": False,
            "center": False,
        }

    def forward(self, x):
        """

        Args:
            x

        Returns:
            y
        """
        spec = torch.stft(x.squeeze(1), **self.stft_kwargs).split(1, -1)
        re, im = spec[0].squeeze(-1), spec[1].squeeze(-1)

        return re, im

    def pad_input(self, input):
        """This padding adds points so we can generate a full chunk of size hop_length at the end
        DOES NOT do the padding for alignement on the left (but does it on the right), because handled
        by fmot internal buffer
        """
        if input.dim() not in [2, 3]:
            raise RuntimeError("Input can only be 2 or 3 dimensional.")
        if input.dim() == 2:
            input = input.unsqueeze(1)
        T = input.shape[2]
        n_frames = int(math.ceil(T / self.hop_length))

        n_pad = n_frames * self.hop_length - T
        if n_pad != 0:
            input = F.pad(input, (0, n_pad))

        input = F.pad(input, (self.hop_length * 3, self.hop_length))

        return input, n_pad


class Qat(nn.Module):
    """
    TinyLSTM speech enhancement network
    """

    def __init__(self, n_fft=512, n_stages=3):
        super().__init__()

        N_1 = int(3 / 4 * n_fft)
        N_2 = int(1 / 4 * n_fft)
        self.hop_length = n_fft // 4
        self.asym_window = nn.Parameter(
            torch.tensor(
                [np.sin(np.pi / 2 * n / N_1) for n in range(N_1)]
                + [np.cos(np.pi / 2 * n / N_2) for n in range(N_2)],
                dtype=torch.float32,
            ),
            requires_grad=False,
        )
        # Override STFT with fmot
        self.stft = fmot.nn.STFT(
            n_fft=n_fft,
            hop_size=self.hop_length,
            n_stages=n_stages,
            window_size=n_fft,
            window_fn=self.asym_window,
        )

    def forward(self, x):
        """

        Args:
            x: hop chunks

        Returns:
            y
        """
        re, im = self.stft(x)

        return re, im

    def pad_input(self, input):
        """This padding adds points so we can generate a full chunk of size hop_length at the end
        DOES NOT do the padding for alignement on the left (but does it on the right), because handled
        by fmot internal buffer
        """
        if input.dim() not in [2, 3]:
            raise RuntimeError("Input can only be 2 or 3 dimensional.")
        if input.dim() == 2:
            input = input.unsqueeze(1)
        T = input.shape[2]
        n_frames = int(math.ceil(T / self.hop_length))

        n_pad = n_frames * self.hop_length - T
        if n_pad != 0:
            input = F.pad(input, (0, n_pad))

        input = F.pad(input, (0, self.hop_length))

        return input, n_pad

    def preprocess(self, x):
        """
        Simple module that reshapes audio back-and-forth from (B, num_samples)
        format to (B, num_frames, hop_length) format. Also does the padding.

        Can be used in a very simple manner with:
        """
        n_batches = x.shape[0]
        input, n_pad = self.pad_input(x)
        input = input.reshape(n_batches, -1, self.hop_length)

        return input, n_pad


def test_stft_logic():
    torch.manual_seed(0)
    model1 = Model()
    model2 = Qat()

    x = torch.randn(5, 1, 128 * 4)
    x1, n_pad1 = model1.pad_input(x)
    re1, im1 = model1(x1)

    x2, n_pad2 = model2.preprocess(x)
    re2, im2 = model2(x2)
    re2, im2 = re2.transpose(2, 1), im2.transpose(2, 1)

    assert abs(re2 - re1).sum() < 1e-2
