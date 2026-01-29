from fmot.fqir.writer.fqir_writer import quantize
import numpy as np


def test_quantize_array():
    x = np.random.randn(1000)
    x_int, quanta = quantize(x, bits=16)
    assert np.all(np.logical_and(x_int >= -(2**15), x_int < 2**15))

    x_quant = 2**quanta * x_int
    rms_error = np.sqrt(np.mean((x_quant - x) ** 2))
    assert rms_error < 1e-4


def test_quantize_zero():
    z, quanta = quantize(0, bits=16)
    assert quanta == -15
