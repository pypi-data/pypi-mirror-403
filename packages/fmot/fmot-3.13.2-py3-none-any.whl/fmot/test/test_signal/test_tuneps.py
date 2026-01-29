import torch
import fmot
import math
import pytest
from contextlib import nullcontext


@pytest.mark.parametrize("eps", [2**-8, 2**-12, 2**-14, 2**-15])
@pytest.mark.parametrize("scale", [1, 10])
def test_tuneps(eps, scale):
    if eps < 2**-14:
        with pytest.raises(ValueError):
            model = fmot.nn.TuningEpsilon(eps)
    else:
        model = fmot.nn.TuningEpsilon(eps)

        x = torch.linspace(0, scale, 1000).reshape(10, -1)
        model(x)

        epsilon = model.epsilon()
        assert epsilon == scale * eps

        cmodel = fmot.ConvertedModel(model)
        cmodel.quantize([x for _ in range(4)])

        graph = cmodel.trace()

        node = graph.subgraphs["ARITH"].nodes[0]
        eps_quant = node.constants["y"] >> -node.constants["shamt_y"]
        assert eps_quant != 0

        print(f"{eps_quant=}")
        eps_bits = math.log2(float(eps_quant))
        desired_eps_bits = 14 + math.log2(eps)
        assert abs(eps_bits - desired_eps_bits) < 1, f"{eps_bits=} {desired_eps_bits=}"


@pytest.mark.parametrize("eps", [2**-8, 2**-12, 2**-14, 2**-15])
@pytest.mark.parametrize("scale", [1, 10])
def test_logeps(eps, scale):
    if eps < 2**-13:
        with pytest.raises(ValueError):
            model = fmot.nn.signal_processing.LogEps(eps)
    else:
        model = fmot.nn.signal_processing.LogEps(eps)

        x = scale * torch.exp(
            torch.linspace(math.log(2**-16), 0, 1000).reshape(10, -1)
        )
        model(x)

        cmodel = fmot.ConvertedModel(model)
        cmodel.quantize([x for _ in range(4)])

        y0 = model(x)
        y1 = cmodel(x)

        # maximum error tolerance of 1
        assert torch.max((y0 - y1).abs()) < 0.5
