import torch
from fmot.nn import FFT
import fmot
import numpy as np
from fmot.tracing.compare_fqir import run_fqir_autocompare


def test_fft():
    torch.manual_seed(0)
    model = FFT(512, 1)
    cmodel = fmot.ConvertedModel(model, observer="min_max")
    cmodel.quantize([torch.randn(8, 512) for _ in range(4)])
    graph = cmodel.trace()

    x = torch.randn(1, 512)

    re0, im0 = cmodel(x)
    re0, im0 = map(lambda x: x.detach().numpy(), [re0, im0])
    re1, im1 = graph.run(x.numpy(), dequant=True)

    # assert np.array_equal(re0, re1)
    # assert np.array_equal(im0, im1)

    print(run_fqir_autocompare(cmodel, graph, [x]))


if __name__ == "__main__":
    test_fft()
