import fmot
import torch
from fmot.beta.signal24.higher_precision_matmul import get_higher_precision_matmul
from fmot.beta.signal24.gmac_wrappers import Cast16
from fmot.precisions import int8, int16, int24
import pytest
import numpy as np


@pytest.mark.parametrize(
    ["act_precision", "weight_precision"],
    [[int16, int8], [int16, 16], [24, int8], [int24, int16]],
)
def test_higher_matmul(act_precision, weight_precision):
    torch.manual_seed(0)

    matrix = torch.randn(32, 32)

    mm = get_higher_precision_matmul(matrix, act_precision, weight_precision)

    if act_precision == int24:
        mm = torch.nn.Sequential(mm, Cast16())

    x = torch.randn(8, 32)

    y0 = torch.matmul(x, matrix.T)
    y1 = mm(x)

    cmodel = fmot.ConvertedModel(mm)
    cmodel.quantize([torch.randn(8, 32) for _ in range(4)])

    y2 = cmodel(x)

    mse01 = torch.mean((y0 - y1) ** 2)
    mse02 = torch.mean((y0 - y2) ** 2)

    assert mse01 < 1e-10

    if weight_precision == int8:
        assert mse02 < 2e-2, f"{mse02=} threshold: 1e-2"
    else:
        assert mse02 < 4e-6, f"{mse02=} threshold: 4e-6"

    graph = cmodel.trace()

    y_graph = graph.run(x[0].numpy(), dequant=True)
    assert np.all(y_graph == y2[0].detach().cpu().numpy())


if __name__ == "__main__":
    test_higher_matmul(int16, int8)
    test_higher_matmul(16, 16)
    test_higher_matmul(24, 16)
    test_higher_matmul(int24, 8)
