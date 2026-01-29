import torch
from torch import nn, Tensor
import fmot
import pytest
from fmot.qat.nn.quant_wrap import QuantizationSpecificationError
from contextlib import nullcontext
from typing import *


@pytest.mark.parametrize("quanta", [-15, -14, -13])
def test_requant_collection_from_quanta(quanta):
    model = nn.Linear(8, 8)
    cmodel = fmot.ConvertedModel(model)
    requant = cmodel.model.requantizers

    requant.set_quanta(0, quanta=quanta)

    cmodel.quantize([torch.randn(8, 8) for _ in range(4)])

    x = torch.randn(8, 8)
    y = cmodel(x)

    assert y.quanta == quanta
    print(f"{y.quanta} = {quanta} :)")


@pytest.mark.parametrize(
    ["limits", "expected_quanta"], [[(-1, 1), -15], [(-2, 2), -14], [(3, 2), -13]]
)
def test_requant_collection_from_limits(limits, expected_quanta):
    model = nn.Linear(8, 8)
    cmodel = fmot.ConvertedModel(model)
    requant = cmodel.model.requantizers

    requant.set_quanta(0, limits=limits)

    cmodel.quantize([torch.randn(8, 8) for _ in range(4)])

    x = torch.randn(8, 8)
    y = cmodel(x)

    assert y.quanta == expected_quanta
    print(f"{y.quanta} = {expected_quanta} :)")


@pytest.mark.parametrize("quanta", [-15, -13, 0])
def test_quant_collection_from_quanta(quanta):
    class MyModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.lin = nn.Linear(8, 8)

        def forward(self, x):
            y = self.lin(x)
            return x, y

    model = MyModel()
    cmodel = fmot.ConvertedModel(model)
    quantizers = cmodel.model.quantizers
    quantizers.set_quanta(0, quanta=quanta)

    cmodel.quantize([torch.randn(8, 8) for _ in range(4)])
    x, y = cmodel(torch.randn(8, 8))

    assert x.quanta == quanta
    print(f"Input quanta check: {x.quanta} = {quanta} :)")


@pytest.mark.parametrize("qx1", [-14, -12])
@pytest.mark.parametrize("qx2", [-13, -7])
@pytest.mark.parametrize("qz1", [-1, -20])
@pytest.mark.parametrize("qz2", [-3, 100])
@pytest.mark.parametrize(
    "quant_before", [True, False], ids=["quant_before", "quant_after"]
)
def test_mimo_quanta_setting(
    qx1: int, qx2: int, qz1: int, qz2: int, quant_before: bool
):
    class MyModel(nn.Module):
        def forward(self, x1, x2):
            z1 = x1 + x2
            z2 = x1 * x2
            return z1, z2, x1, x2

    model = MyModel()
    cmodel = fmot.ConvertedModel(model)
    quantizers = cmodel.model.quantizers
    requantizers = cmodel.model.requantizers

    if quant_before:
        cmodel.quantize([(torch.randn(8, 8), torch.randn(8, 8)) for _ in range(4)])

    quantizers.set_quanta(0, qx1)
    quantizers.set_quanta(1, qx2)
    requantizers.set_quanta(0, qz1)
    requantizers.set_quanta(1, qz2)

    if not quant_before:
        cmodel.quantize([(torch.randn(8, 8), torch.randn(8, 8)) for _ in range(4)])

    z1, z2, x1, x2 = cmodel(torch.randn(8, 8), torch.randn(8, 8))

    print(f"num None quanta: {sum(map(lambda x: x.quanta is None, [z1, z2, x1, x2]))}")

    assert x1.quanta == qx1
    assert x2.quanta == qx2
    assert z1.quanta == qz1
    assert z2.quanta == qz2

    print(":)")


@pytest.mark.parametrize("quanta", [-15])
@pytest.mark.parametrize("target", ["x", "y"])
@pytest.mark.parametrize(
    "quantize_before", [True, False], ids=["quant_before", "quant_after"]
)
def test_structured_inputs(quanta, target: str, quantize_before):
    class MyModel(nn.Module):
        def forward(self, x: Tensor, conf: Dict[str, Tensor]):
            y = conf["y"]
            z = x + y
            return x, y, z

    model = MyModel()
    cmodel = fmot.ConvertedModel(model)

    calib = [(torch.randn(8, 8), {"y": torch.randn(8, 8)}) for _ in range(4)]
    if quantize_before:
        cmodel.quantize(calib)

    quantizers = cmodel.model.quantizers
    if target == "x":
        quantizers.set_quanta(0, quanta)
    elif target == "y":
        context = (
            pytest.raises(QuantizationSpecificationError)
            if quantize_before
            else nullcontext()
        )
        with context:
            quantizers.set_quanta(1, quanta)

    context = nullcontext()
    if not quantize_before and target == "y":
        context = pytest.raises(QuantizationSpecificationError)

    with context:
        if not quantize_before:
            cmodel.quantize(calib)

        x, y, z = cmodel(*calib[0])

    if target == "x":
        assert x.quanta == quanta


@pytest.mark.parametrize("qx1", [-14, -12])
@pytest.mark.parametrize("qx2", [-13, -7])
@pytest.mark.parametrize("qz1", [-1, -20])
@pytest.mark.parametrize("qz2", [-3, 100])
@pytest.mark.parametrize(
    "quant_before", [True, False], ids=["quant_before", "quant_after"]
)
def test_mimo_quanta_setting_user_api(
    qx1: int, qx2: int, qz1: int, qz2: int, quant_before: bool
):
    class MyModel(nn.Module):
        def forward(self, x1, x2):
            z1 = x1 + x2
            z2 = x1 * x2
            return z1, z2, x1, x2

    model = MyModel()
    cmodel = fmot.ConvertedModel(model)

    if quant_before:
        cmodel.quantize([(torch.randn(8, 8), torch.randn(8, 8)) for _ in range(4)])

    cmodel.set_input_details(0, qx1)
    cmodel.set_input_details(1, qx2)
    cmodel.set_output_details(0, qz1)
    cmodel.set_output_details(1, qz2)

    if not quant_before:
        cmodel.quantize([(torch.randn(8, 8), torch.randn(8, 8)) for _ in range(4)])

    z1, z2, x1, x2 = cmodel(torch.randn(8, 8), torch.randn(8, 8))

    print(f"num None quanta: {sum(map(lambda x: x.quanta is None, [z1, z2, x1, x2]))}")

    assert x1.quanta == qx1
    assert x2.quanta == qx2
    assert z1.quanta == qz1
    assert z2.quanta == qz2

    print(":)")


def test_stft_istft_quant15():
    HOP = 64
    N_FFT = 128

    class Model(nn.Module):
        def __init__(self):
            super().__init__()
            self.stft = fmot.nn.STFT(
                N_FFT, HOP, n_stages=0, window_fn=torch.hann_window(N_FFT)
            )
            self.istft = fmot.nn.ISTFT(
                N_FFT, HOP, n_stages=0, window_fn=torch.hann_window(N_FFT)
            )

        def forward(self, x):
            re, im = self.stft(x)
            y = self.istft(re, im)
            return y

    model = Model()
    cmodel = fmot.ConvertedModel(model, batch_dim=0, seq_dim=1)
    cmodel.set_input_details(0, -15)
    cmodel.set_output_details(0, -15)
    cmodel.quantize([torch.randn(8, 10, HOP) for _ in range(4)])

    y = cmodel(torch.randn(8, 10, HOP))
    assert y.quanta == -15

    graph = cmodel.trace()
    print(graph)

    arith = graph.subgraphs["ARITH"]
    assert arith.inputs[0].quanta == -15
    assert arith.outputs[0].quanta == -15


if __name__ == "__main__":
    # test_structured_inputs(-10, "x", True)
    # test_structured_inputs(-10, "y", True)
    import logging

    logging.basicConfig(level=logging.INFO)

    test_stft_istft_quant15()
