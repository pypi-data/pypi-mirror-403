import torch
from torch import nn, Tensor
import fmot
from typing import Dict
import pytest
from fmot.qat.nn.quant_wrap import QuantizationSpecificationError


class MyModel(nn.Module):
    def forward(self, x: Tensor, y: Dict[str, Tensor]):
        z = x + y["input"]
        return z


def test_raises_error_on_wrong_inputs():
    model = MyModel()
    cmodel = fmot.ConvertedModel(model)

    cmodel(torch.randn(8, 8), {"input": torch.randn(8, 8)})

    with pytest.raises(QuantizationSpecificationError):
        cmodel(torch.randn(8, 8), torch.randn(8, 8))
