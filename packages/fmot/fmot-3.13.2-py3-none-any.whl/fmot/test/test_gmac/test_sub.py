import torch
from torch import nn
from fmot.nn import GMACv2
import fmot


class Sub(torch.nn.Module):
    def __init__(self, act_precision=24):
        super().__init__()
        self.gmac = GMACv2(
            bits_out=act_precision, scalar_multipliers=torch.tensor([1.0, -1.0])
        )

    def forward(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        return self.gmac([], [], [x, y])


class Cast(torch.nn.Module):
    def __init__(self, act_precision=16):
        super().__init__()
        self.gmac = GMACv2(
            bits_out=act_precision, scalar_multipliers=torch.tensor([1.0])
        )

    def forward(self, x):
        return self.gmac([], [], [x])


class SubModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.sub = Sub(24)
        self.cast = Cast(16)

    def forward(self, x, y):
        z = self.sub(x, y)
        return self.cast(z)


def test_sub():
    model = SubModel()

    cmodel = fmot.ConvertedModel(model, "double")
    cmodel.quantize([(torch.randn(8, 128), torch.randn(8, 128)) for _ in range(5)])

    graph = cmodel.trace()
    print(graph)


if __name__ == "__main__":
    test_sub()
