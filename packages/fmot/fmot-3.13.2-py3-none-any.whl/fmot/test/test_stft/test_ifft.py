import torch
import fmot
import numpy as np
import matplotlib.pyplot as plt

# relative tolerance for tests:
FP_TOL = 1e-10
Q_TOL = 1e-4


def test_ifft():
    torch.random.manual_seed(0)
    n_fft = 512
    n_stages = 3
    model = fmot.nn.IFFT(n_fft, n_stages)

    x_re = torch.randn(1, n_fft)
    x_im = torch.randn(1, n_fft)

    with torch.no_grad():
        y = torch.fft.ifft(x_re + 1j * x_im)
        re0 = y.real
        im0 = y.imag

        re1, im1 = model(x_re, x_im)

    re_nmse = (re0 - re1).pow(2).mean() / re0.pow(2).mean()
    im_nmse = (im0 - im1).pow(2).mean() / im0.pow(2).mean()

    assert re_nmse < FP_TOL
    assert im_nmse < FP_TOL

    cmodel = fmot.ConvertedModel(model)
    cmodel.quantize([(x_re, x_im) for _ in range(3)])
    with torch.no_grad():
        re2, im2 = cmodel(x_re, x_im)

    re_nmse = (re0 - re2).pow(2).mean() / re0.pow(2).mean()
    im_nmse = (im0 - im2).pow(2).mean() / im0.pow(2).mean()

    assert re_nmse < Q_TOL
    assert im_nmse < Q_TOL


def test_irfft():
    torch.random.manual_seed(0)
    n_fft = 512
    n_stages = 3
    model = fmot.nn.IRFFT(n_fft, n_stages)

    x = torch.randn(1, n_fft)
    y = torch.fft.rfft(x)
    y_re = y.real
    y_im = y.imag

    with torch.no_grad():
        x0 = model(y_re, y_im)

    fp_nmse = (x0 - x).pow(2).mean() / x.pow(2).mean()

    assert fp_nmse < FP_TOL

    cmodel = fmot.ConvertedModel(model)
    cmodel.quantize([(y_re, y_im) for _ in range(3)])
    with torch.no_grad():
        x1 = cmodel(y_re, y_im)

    q_nmse = (x1 - x).pow(2).mean() / x.pow(2).mean()

    assert q_nmse < Q_TOL


if __name__ == "__main__":
    test_ifft()
    test_irfft()
