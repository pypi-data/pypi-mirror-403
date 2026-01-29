import torch
from torch import nn, Tensor
import fmot
from fmot.nn import GMACv2, Sequencer, MIMOSequencer
import numpy as np
import pytest


class _I24EMA(Sequencer):
    def __init__(self, n_channels, alpha):
        super().__init__([[n_channels]])
        if alpha != 1:
            self.add = GMACv2(
                bits_out=24, scalar_multipliers=torch.tensor([alpha, 1 - alpha])
            )
        else:
            self.add = GMACv2(bits_out=24, scalar_multipliers=torch.tensor([1, 1]))
        self.cast = GMACv2(bits_out=16, scalar_multipliers=torch.tensor([1]))

    @torch.jit.export
    def step(self, x_t: Tensor, state: list[Tensor]) -> tuple[Tensor, list[Tensor]]:
        (y_prev,) = state
        y_curr = self.add([], [], [y_prev, x_t])
        y_16 = self.cast([], [], [y_curr])

        return y_16, [y_curr]


class I24EMA(nn.Module):
    def __init__(self, n_channels, alpha):
        super().__init__()
        self.cumsum = _I24EMA(n_channels, alpha)

    def forward(self, x):
        y, _ = self.cumsum(x)
        return y


@pytest.mark.parametrize("n_channels", [16])
@pytest.mark.parametrize("alpha", [0.9, 1.0])
def test_i24_cumsum(n_channels, alpha):
    model = I24EMA(n_channels, alpha)

    cmodel = fmot.ConvertedModel(model, batch_dim=0, seq_dim=1)
    cmodel.quantize([torch.randn(8, 100, n_channels) for _ in range(4)])

    print("Quantized successfully!")

    graph = cmodel.trace()

    x = torch.randn(1, 100, n_channels)
    y_cmodel = cmodel(x)[0].numpy()
    y_fqir = graph.run(x[0].numpy(), dequant=True)

    assert np.array_equal(y_cmodel, y_fqir), f"diff: {y_cmodel - y_fqir}"

    print("Runtimes match!")


class _I24DualEMA(MIMOSequencer):
    def __init__(self, n_channels, alpha):
        super().__init__(
            num_inputs=2, num_outputs=2, state_shapes=[[n_channels], [n_channels]]
        )
        if alpha != 1:
            self.add = GMACv2(
                bits_out=24, scalar_multipliers=torch.tensor([alpha, 1 - alpha])
            )
        else:
            self.add = GMACv2(bits_out=24, scalar_multipliers=torch.tensor([1, 1]))
        self.cast = GMACv2(bits_out=16, scalar_multipliers=torch.tensor([1]))

    @torch.jit.export
    def step(
        self, x_t: list[Tensor], state: list[Tensor]
    ) -> tuple[list[Tensor], list[Tensor]]:
        x0, x1 = x_t
        y0, y1 = state

        y0 = self.add([], [], [y0, x0])
        y0_16 = self.cast([], [], [y0])

        y1 = self.add([], [], [y1, x1])
        y1_16 = self.cast([], [], [y1])

        return [y0_16, y1_16], [y0, y1]


class I24DualEMA(nn.Module):
    def __init__(self, n_channels, alpha):
        super().__init__()
        self.cumsum = _I24DualEMA(n_channels, alpha)

    def forward(self, x, y):
        outs, _ = self.cumsum([x, y])
        x, y = outs
        return x + y


@pytest.mark.parametrize("n_channels", [16])
@pytest.mark.parametrize("alpha", [0.9, 1.0])
def test_i24_mimo_cumsum(n_channels, alpha):
    model = I24DualEMA(n_channels, alpha)

    cmodel = fmot.ConvertedModel(model, batch_dim=0, seq_dim=1)
    cmodel.quantize(
        [
            (torch.randn(8, 100, n_channels), torch.randn(8, 100, n_channels))
            for _ in range(4)
        ]
    )

    print("Quantized successfully!")

    graph = cmodel.trace()

    x = torch.randn(1, 100, n_channels)
    y = torch.randn(1, 100, n_channels)
    y_cmodel = cmodel(x, y)[0].numpy()
    y_fqir = graph.run(x[0].numpy(), y[0].numpy(), dequant=True)

    assert np.array_equal(y_cmodel, y_fqir), f"diff: {y_cmodel - y_fqir}"

    print("Runtimes match!")


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    test_i24_mimo_cumsum(16, 1)
