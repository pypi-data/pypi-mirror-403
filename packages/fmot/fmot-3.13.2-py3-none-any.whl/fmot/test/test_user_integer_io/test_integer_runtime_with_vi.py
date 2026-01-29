import torch
import fmot
from torch import nn
import numpy as np
import pytest


class MulModel(nn.Module):
    def __init__(self, imm):
        super().__init__()
        self.imm = imm

    def forward(self, x):
        return x * self.imm


@pytest.mark.parametrize("imm", [1, 1.5])
def test_mul_by_imm_i16(imm):
    N = 128
    model = MulModel(imm)
    cmodel = fmot.ConvertedModel(model, batch_dim=0)
    calib = [torch.rand(8, N).clamp(-1, 0.99) for _ in range(4)]
    cmodel.quantize(calib)
    graph = cmodel.trace()

    x = torch.rand(1, N).clamp(-1, 0.99)
    x_np = x.numpy()[0]
    y0 = cmodel(x)[0].numpy()
    y1, state1 = graph.run(x_np, dequant=True, return_objs=True)

    x_np_i16 = (x_np * 2**15).astype(np.int16)

    y2, state2 = graph.run(x_np_i16, dequant=True, return_objs=True)

    assert np.all(y1 == y2)
    print("Success!")


if __name__ == "__main__":
    test_mul_by_imm_i16(2)
