import torch
from torch import nn
from fmot.nn.signal_processing import Atan2
from torch.autograd import gradcheck
import pytest


@pytest.mark.parametrize("norm", [True, False])
def atan2_gradcheck(norm: bool):
    # x = torch.linspace(-0.9, 0.9, 100, requires_grad=True).reshape(1, -1)
    # y = torch.linspace(-0.9, 0.9, 100, requires_grad=True).reshape(-1, 1)
    torch.manual_seed(0)
    x = torch.randn(32, 32, requires_grad=True)
    y = torch.randn(32, 32, requires_grad=True)

    gradcheck(Atan2(norm=norm), (x, y), atol=2e-1)
