"""Test int24 in context of various operations."""
import torch
from torch import nn, Tensor
import fmot
from fmot.nn import GMACv2
import pytest
from contextlib import nullcontext
from fmot.qat.annotated_tensors import UnsupportedPrecisionError
import numpy as np


class Int24Cat(nn.Module):
    def __init__(self):
        super().__init__()
        self.cast1 = GMACv2(bits_out=24, scalar_multipliers=torch.tensor([1.0]))
        self.cast2 = GMACv2(bits_out=24, scalar_multipliers=torch.tensor([1.0]))
        self.cast3 = GMACv2(bits_out=16, scalar_multipliers=torch.tensor([1.0]))

    def forward(self, x, y):
        x = self.cast1([], [], [x])
        y = self.cast2([], [], [y])
        z = torch.cat([x, y], dim=-1)
        z = self.cast3([], [], [z])
        return z


def get_calib_data(num_inputs: int, shape: list[int], random_scales=False):
    if random_scales:
        scales = np.exp(np.random.randn(num_inputs))
    else:
        scales = np.ones(num_inputs)
    calib = [
        tuple([torch.randn(*shape) * scales[i] for i in range(num_inputs)])
        for _ in range(4)
    ]
    return calib


def supported(status: bool):
    return pytest.mark.parametrize("supported", [status])


@pytest.mark.parametrize("random_scales", [True, False])
@supported(True)
def test_i24_cat(supported: bool, random_scales: bool):
    model = Int24Cat()
    cmodel = fmot.ConvertedModel(model)

    calib = get_calib_data(2, [8, 16], random_scales)

    if supported:
        ctx = nullcontext()
    else:
        ctx = pytest.raises(UnsupportedPrecisionError)

    with ctx:
        cmodel.quantize(calib)

    if supported:
        graph = cmodel.trace()

        x, y = get_calib_data(2, [1, 16], random_scales)[0]
        z = cmodel(x, y).squeeze(0).numpy()

        z_np = graph.run(x[0].numpy(), y[0].numpy(), dequant=True)

        assert np.array_equal(z, z_np)
        print("Success!")


class Int24Chunk(nn.Module):
    def __init__(self):
        super().__init__()
        self.cast1 = GMACv2(bits_out=24, scalar_multipliers=torch.tensor([1.0]))
        self.cast2 = GMACv2(bits_out=16, scalar_multipliers=torch.tensor([1.0]))
        self.cast3 = GMACv2(bits_out=16, scalar_multipliers=torch.tensor([1.0]))

    def forward(self, x):
        x = self.cast1([], [], [x])
        a, b = torch.chunk(x, 2, -1)
        a = self.cast2([], [], [a])
        b = self.cast3([], [], [b])
        return a, b


class Int24Split(nn.Module):
    def __init__(self):
        super().__init__()
        self.cast1 = GMACv2(bits_out=24, scalar_multipliers=torch.tensor([1.0]))
        self.cast2 = GMACv2(bits_out=16, scalar_multipliers=torch.tensor([1.0]))
        self.cast3 = GMACv2(bits_out=16, scalar_multipliers=torch.tensor([1.0]))

    def forward(self, x):
        x = self.cast1([], [], [x])
        a, b = torch.split(x, [4, 12], -1)
        a = self.cast2([], [], [a])
        b = self.cast3([], [], [b])
        return a, b


@pytest.mark.parametrize("cls", [Int24Chunk, Int24Split])
@supported(True)
def test_i24_split_chunk(cls: type[nn.Module], supported: bool):
    model = cls()
    cmodel = fmot.ConvertedModel(model)

    calib = get_calib_data(1, [8, 16])

    if supported:
        ctx = nullcontext()
    else:
        ctx = pytest.raises(UnsupportedPrecisionError)

    with ctx:
        cmodel.quantize(calib)

    if supported:
        graph = cmodel.trace()

        x = torch.randn(1, 16)
        a, b = map(lambda z: z.squeeze().numpy(), cmodel(x))

        a_np, b_np = graph.run(x[0].numpy(), dequant=True)

        assert np.array_equal(a, a_np)
        assert np.array_equal(b, b_np)
        print("Success!")


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    test_i24_cat(supported=True, random_scales=True)
    test_i24_split_chunk(Int24Chunk, supported=True)
    test_i24_split_chunk(Int24Split, supported=True)
