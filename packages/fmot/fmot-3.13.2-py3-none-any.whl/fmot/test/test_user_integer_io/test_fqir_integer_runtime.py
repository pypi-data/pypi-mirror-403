import torch
import fmot
import numpy as np
import pytest


def test_integer_runtime():
    model = torch.nn.Linear(32, 32)
    cmodel = fmot.ConvertedModel(model)
    cmodel.quantize([torch.randn(32, 32) for _ in range(4)])
    graph = cmodel.trace()

    # run same input through as a float and as an integer
    quanta = graph.subgraphs["QUANT"].nodes[0].constants["quanta"]
    x_int = np.arange(-16, 16, dtype=np.int16)
    y_from_int = graph.run(x_int, dequant=True)

    x_float = x_int * 2.0**quanta
    y_from_float = graph.run(x_float, dequant=True)

    assert np.array_equal(y_from_int, y_from_float)
    print("integer runtime test passed!")


@pytest.mark.parametrize("maxval", [16, 2**17])
def test_input_range_assertions(maxval):
    model = torch.nn.Linear(8, 8)
    cmodel = fmot.ConvertedModel(model)
    cmodel.quantize([torch.randn(8, 8) for _ in range(4)])
    graph = cmodel.trace()

    x = np.arange(maxval - 8, maxval, dtype=np.int32)

    if maxval > 2**15 - 1:
        with pytest.raises(Exception):
            graph.run(x, dequant=True)
    else:
        graph.run(x, dequant=True)
