import fmot
import torch
from torch import nn

BATCH = 8
HOP = 32
WIN = 256
SYNTH_WIN = 64


class fmotAsymmetricOLA(nn.Module):
    def __init__(self, window_size: int, synthesis_size: int, hop_size: int):
        super().__init__()

        # design an asymmetric hann window
        size_falling = synthesis_size // 2
        size_rising = window_size - size_falling

        window_fn = torch.cat(
            [
                torch.hann_window(2 * size_rising)[:size_rising],
                torch.hann_window(2 * size_falling)[size_falling:],
            ]
        )

        # use fmot tools to design a synthesis window that satisfies the WOLA condition
        synth_window_fn = fmot.nn.design_wola(window_fn, hop_size, synthesis_size)

        self.stft = fmot.nn.STFT(window_size, hop_size, window_fn=window_fn)
        self.istft = fmot.nn.ISTFT(
            window_size,
            hop_size,
            synthesis_window_size=synthesis_size,
            window_fn=window_fn,
            synthesis_window_fn=synth_window_fn,
        )

    def forward(self, x):
        re, im = self.stft(x)
        y = self.istft(re, im)
        return y


def test_asym_ola_docs_example():
    ola = fmotAsymmetricOLA(WIN, SYNTH_WIN, HOP)

    ola_delay = ola.istft.ola_delay

    ola(torch.randn(10, 10, 32))
    cmodel = fmot.ConvertedModel(ola, batch_dim=0, seq_dim=1)
    x_1 = torch.rand(BATCH, 10, 32)
    x_2 = torch.rand(BATCH, 10, 32)
    cmodel.quantize([x_1, x_2])
    graph = cmodel.trace()
    print(graph)
