import fmot
from fmot.nn import GMACv2
import torch
from torch import nn, Tensor
from fmot.qat.annotated_tensors import UnsupportedPrecisionError
import numpy as np
import pytest


class MyTestModelA(nn.Module):
    def __init__(self):
        super().__init__()
        self.gmac1 = GMACv2(bits_out=24, scalar_multipliers=torch.tensor([1.0, 1.0]))
        self.gmac2 = GMACv2(bits_out=24)
        self.gmac3 = GMACv2(bits_out=16, scalar_multipliers=torch.tensor([1.0]))

    def forward(self, x, y):
        z = self.gmac1([], [], [x, y])
        z = self.gmac2([x], [z], [])
        z = self.gmac3([], [], [z])
        return z


def test_gmac24_virtualization():
    model = MyTestModelA()
    cmodel = fmot.ConvertedModel(model)
    cmodel.quantize([(torch.randn(8, 16), torch.randn(8, 16)) for _ in range(4)])
    graph = cmodel.trace()

    x, y = np.random.randn(16), np.random.randn(16)
    z_exp = model(torch.tensor(x), torch.tensor(y)).detach().numpy()
    z_fqir = graph.run(x, y, dequant=True)

    nmse = np.mean((z_exp - z_fqir) ** 2) / np.var(z_exp)

    assert nmse < 1e-6
    print(f"NMSE: {nmse}")


class UnsupportedA(nn.Module):
    """Unsupported: relu(int24)"""

    def __init__(self):
        super().__init__()
        self.gmac1 = GMACv2(bits_out=24, scalar_multipliers=torch.tensor([1.0, 1.0]))
        self.relu = nn.ReLU()
        self.gmac2 = GMACv2(bits_out=16)

    def forward(self, x, y):
        z = self.gmac1([], [], [x, y])
        z = self.relu(z)
        z = self.gmac2([x], [z], [])
        return z


class UnsupportedB(nn.Module):
    """Unsupported: output int24"""

    def __init__(self):
        super().__init__()
        self.gmac = GMACv2(bits_out=24, scalar_multipliers=torch.tensor([1.0, 1.0]))

    def forward(self, x, y):
        z = self.gmac([], [], [x, y])
        return z


@pytest.mark.parametrize("model_cls", [UnsupportedA, UnsupportedB])
def test_invalid_model(model_cls):
    ### Should raise an error if we try to return an int24 vector
    ### or try to run int24 tensors into unsupported operations
    model = model_cls()
    cmodel = fmot.ConvertedModel(model)

    with pytest.raises(UnsupportedPrecisionError):
        cmodel.quantize([(torch.randn(8, 16), torch.randn(8, 16)) for _ in range(4)])


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    test_gmac24_virtualization()
