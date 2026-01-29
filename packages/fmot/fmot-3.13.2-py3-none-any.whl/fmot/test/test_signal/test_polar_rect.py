import torch
from torch import nn
import fmot
from fmot.nn.signal_processing import MagPhase, PolarToRect
import numpy as np

N_TEST = 200


class Rect2Polar2Rect(nn.Module):
    def __init__(self):
        super().__init__()
        self.magphase = MagPhase()
        self.p2r = PolarToRect()

    def forward(self, re, im):
        mag, phase = self.magphase(re, im)
        re, im = self.p2r(mag, phase)
        return re, im


class Polar2Rect2Polar(nn.Module):
    def __init__(self):
        super().__init__()
        self.magphase = MagPhase()
        self.p2r = PolarToRect()

    def forward(self, mag, phase):
        re, im = self.p2r(mag, phase)
        mag, phase = self.magphase(re, im)
        return mag, phase


@torch.no_grad()
def test_rect2polar(plot=False):
    """Tests that we can convert to polar coordinates and back"""

    x, y = np.meshgrid(np.linspace(-1, 1, N_TEST), np.linspace(-1, 1, N_TEST))
    x, y = map(torch.tensor, (x, y))

    model = Rect2Polar2Rect()
    cmodel = fmot.ConvertedModel(model)
    cmodel.quantize([(x, y)] * 2)

    xp, yp = model(x, y)

    err_x = (x - xp).square().mean().sqrt()
    err_y = (y - yp).square().mean().sqrt()

    if not plot:
        assert err_x < 5e-3
        assert err_y < 5e-3

    if plot:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(2)
        ax[0].plot(x.flatten(), xp.flatten(), ".")
        ax[1].plot(y.flatten(), yp.flatten(), ".")
        for a in ax:
            a.grid()
            a.set_xlabel("F.P.")
            a.set_ylabel("Quant")
        ax[0].set_xlabel("Re")
        ax[1].set_ylabel("Im")
        plt.show()


@torch.no_grad()
def test_polar2rect(plot=False):
    """Tests that we can convert to polar coordinates and back"""

    mag, phase = np.meshgrid(
        np.linspace(0, 1, N_TEST), np.linspace(-np.pi, np.pi, N_TEST)
    )
    x, y = map(torch.tensor, (mag, phase))

    model = Rect2Polar2Rect()
    cmodel = fmot.ConvertedModel(model)
    cmodel.quantize([(x, y)] * 2)

    xp, yp = model(x, y)

    err_x = (x - xp).square().mean().sqrt()
    err_y = (y - yp).square().mean().sqrt()

    if not plot:
        assert err_x <= 5e-3
        assert err_y <= 5e-3

    if plot:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(2)
        ax[0].plot(x.flatten(), xp.flatten(), ".")
        ax[1].plot(y.flatten(), yp.flatten(), ".")
        for a in ax:
            a.grid()
            a.set_xlabel("F.P.")
            a.set_ylabel("Quant")
        ax[0].set_xlabel("Mag")
        ax[1].set_ylabel("Phase")
        plt.show()


if __name__ == "__main__":
    test_rect2polar(plot=False)
    test_polar2rect(plot=False)
