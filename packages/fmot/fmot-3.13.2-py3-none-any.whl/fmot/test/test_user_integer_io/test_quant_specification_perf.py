import torch
from torch import nn
import fmot
import matplotlib.pyplot as plt
from fmot.qat.nn import Quantizer, FixedQuantaObserver, MinMaxObserver
from fmot.qat.bitwidths import fqint16
from functools import partial


class MyModel(nn.Module):
    def __init__(self, ch_in, ch_out):
        super().__init__()
        self.lin = nn.Linear(ch_in, ch_out)

    def forward(self, x):
        y = self.lin(x)
        return y, x


@torch.no_grad()
def test_forced_quanta():
    model0 = MyModel(32, 32)
    inputs = [torch.randn(32, 32).clamp(-1, 1) for _ in range(4)]

    cmodel0 = fmot.ConvertedModel(model0)
    cmodel0.quantize(inputs)

    model1 = MyModel(32, 32)
    model1.load_state_dict(model0.state_dict())
    cmodel1 = fmot.ConvertedModel(model1)
    cmodel1.set_input_details(0, -15)
    cmodel1.quantize(inputs)

    x = inputs[0]
    y0, x0 = cmodel0(x)
    y1, x1 = cmodel1(x)

    err = torch.mean((y0 - y1) ** 2) / torch.mean(y0**2)
    assert err < 1e-5
    assert x1.quanta == -15


def test_forced_quanta_quantizer():
    quantizer = Quantizer(
        bitwidth=fqint16, observer=partial(FixedQuantaObserver, quanta=-15)
    )
    x = torch.linspace(-1, 1, 1000)
    quantizer.observe = True
    _ = quantizer(x)
    quantizer.quantize = True
    quantizer.observe = False
    y = quantizer(x)

    assert torch.mean((x - y) ** 2) < 1e-3


if __name__ == "__main__":
    test_forced_quanta()
    test_forced_quanta_quantizer()
