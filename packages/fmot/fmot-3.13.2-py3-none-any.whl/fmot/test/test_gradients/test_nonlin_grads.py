import torch
from torch import nn
import fmot
from torch.autograd import gradcheck
import pytest


class ReciprocalModel(nn.Module):
    def forward(self, x):
        return 1 / x


class LogModel(nn.Module):
    def forward(self, x):
        return torch.log(x)


@pytest.mark.parametrize("model_cls", [ReciprocalModel, LogModel])
@pytest.mark.parametrize("telescope_interpolate", [True, False])
def test_telescoped_gradients(
    model_cls: type[nn.Module], telescope_interpolate: bool, plot=False
):
    telescope_orig = fmot.CONFIG.telescope_interpolate
    fmot.CONFIG.telescope_interpolate = telescope_interpolate

    model = model_cls()
    cmodel = fmot.ConvertedModel(model)
    cmodel.quantize(
        [2 ** torch.linspace(-14, 0, 1000, requires_grad=True) for _ in range(4)]
    )

    x = nn.Parameter(2 ** torch.linspace(-14, 0, 1000))
    y_q = cmodel(x)
    loss = y_q.pow(2).mean()
    loss.backward()

    grad_cmodel = x.grad

    x.grad = None
    y = model(x)
    loss = y.pow(2).mean()
    loss.backward()
    grad_model = x.grad

    x = x.detach()

    # no NaNs!
    assert not torch.any(torch.isnan(grad_cmodel))

    if plot:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(2)
        ax[0].plot(x, torch.abs(grad_cmodel), label="qat")
        ax[0].plot(x, torch.abs(grad_model), label="f.p.")
        x_nangrad = x[torch.isnan(grad_cmodel)]
        ax[0].plot(x_nangrad, [1e4] * len(x_nangrad), "s", label="NaN Grad")
        ax[0].set_xscale("log", base=2)
        ax[0].set_yscale("log")
        ax[0].set_xlabel("x")
        ax[0].set_ylabel(r"$| \partial / \partial{x} (1/x) |$")
        ax[0].legend()
        ax[1].plot(x, y_q.detach().abs(), label="qat")
        ax[1].plot(x, y.detach().abs(), label="f.p.")
        ax[1].set_xscale("log", base=2)
        ax[1].set_yscale("log")
        ax[1].set_xlabel("x")
        ax[1].set_ylabel("| f(x) |")
        ax[1].legend()
        plt.suptitle(f"QAT {model_cls} Forward and Backwards Passes")
        plt.show()

    fmot.CONFIG.telescope_interpolate = telescope_orig


if __name__ == "__main__":
    test_telescoped_gradients(ReciprocalModel, True, plot=True)
    test_telescoped_gradients(LogModel, True, plot=True)
