import torch
from torch import nn
import fmot
from fmot.nn import GMACv2, PrecisionSplit
import pytest
import numpy as np


class SingleVV(nn.Module):
    num_inputs = 2

    def __init__(self, bits_out):
        super().__init__()
        self.gmac = GMACv2(bits_out=bits_out)
        self.gmac_out = GMACv2(bits_out=16, scalar_multipliers=torch.tensor([1]))

    def forward(self, x, y):
        z = self.gmac([x], [y], [])
        z = self.gmac_out([], [], [z])
        return z


class DualVV(nn.Module):
    num_inputs = 4

    def __init__(self, bits_out):
        super().__init__()
        self.gmac = GMACv2(bits_out=bits_out)
        self.gmac_out = GMACv2(bits_out=16, scalar_multipliers=torch.tensor([1]))

    def forward(self, x0, y0, x1, y1):
        z = self.gmac([x0, x1], [y0, y1], [])
        z = self.gmac_out([], [], [z])
        return z


class DualVI(nn.Module):
    num_inputs = 2

    def __init__(self, bits_out):
        super().__init__()
        self.gmac = GMACv2(bits_out=bits_out, scalar_multipliers=torch.randn(2))
        self.gmac_out = GMACv2(bits_out=16, scalar_multipliers=torch.tensor([1]))

    def forward(self, x, y):
        z = self.gmac([], [], [x, y])
        z = self.gmac_out([], [], [z])
        return z


CHANNELS = 128


@pytest.mark.parametrize("bits_out", [8, 16, 24])
@pytest.mark.parametrize("cls", [SingleVV, DualVV, DualVI])
def test_gmac_v2(cls: type[nn.Module], bits_out: int):
    torch.manual_seed(0)

    model = cls(bits_out=bits_out)
    num_inputs = model.num_inputs
    cmodel = fmot.ConvertedModel(model)
    cmodel.quantize(
        [tuple([torch.randn(8, CHANNELS) for _ in range(num_inputs)]) for _ in range(4)]
    )

    x = [torch.randn(8, CHANNELS) for _ in range(num_inputs)]
    y0 = model(*x)
    y1 = cmodel(*x)

    quanta_out = y1.quanta

    qsnr = 10 * torch.log10(y0.pow(2).sum() / ((y0 - y1).pow(2).sum() + 1e-6))
    qsnr_bound = 20 if bits_out == 8 else 26
    assert (
        qsnr > qsnr_bound
    ), f"did not satisfy {bits_out=} {qsnr=:.2f} target: qsnr>={qsnr_bound}"

    graph = cmodel.trace()
    print(graph)

    y_fqir = graph.run(*[xx[0].numpy() for xx in x], dequant=False)
    y_qat = np.floor((y1[0] / 2**quanta_out).numpy()).astype(np.int32)

    assert np.array_equal(y_fqir, y_qat), f"diff: {y_fqir - y_qat}\n{y_fqir=}\n{y_qat=}"


class Split16To2x8(nn.Module):
    def __init__(self):
        super().__init__()
        self.prec_split = PrecisionSplit([8, 8], [8, 8])

    def forward(self, x):
        x_lo, x_hi = self.prec_split(x)
        return x, x_lo, x_hi


def test_split_16_to_2x8(plot=False):
    torch.manual_seed(0)
    NDIM = 128
    model = Split16To2x8()
    cmodel = fmot.ConvertedModel(model)

    cmodel.quantize([torch.randn(8, NDIM) for _ in range(4)])

    x = torch.randn(8, NDIM)
    _, lo_fp, hi_fp = model(x)
    x_qat, lo_qat, hi_qat = cmodel(x)

    assert torch.all(lo_fp + hi_fp == x)

    qat_eff = lo_qat + hi_qat
    if plot:
        import matplotlib.pyplot as plt

        plt.plot(x_qat.flatten(), (x_qat - qat_eff).flatten(), ".")
        plt.savefig("test.png")

    # test that dynamic ranges are the same
    x_qat_maxval = 2 ** (x_qat.quanta + x_qat.bitwidth.bitwidth - 1)
    x_hi_maxval = 2 ** (hi_qat.quanta + hi_qat.bitwidth.bitwidth - 1)
    assert x_qat_maxval == x_hi_maxval

    # test that the maximum error is off-by-1 (since two signed-8b vectors are
    # equivalent to 15b, not 16b)
    error = x_qat - qat_eff
    error_int = error * 2 ** (-x_qat.quanta)
    assert torch.max(torch.abs(error_int)) <= 1
    # an equivalent check is that the low-subvector has a quanta 1 higher than x
    assert lo_qat.quanta == x_qat.quanta + 1

    graph = cmodel.trace()
    print(graph)

    x = x[0]
    _, lo, hi = map(lambda x: x.numpy(), cmodel(x))
    _, lo_fqir, hi_fqir = graph.run(x.numpy(), dequant=True)

    if plot:
        fig, ax = plt.subplots(2)
        ax[0].plot(hi, hi_fqir, ".")
        ax[0].set_title("High")
        ax[1].plot(lo, lo_fqir, ".")
        ax[1].set_title("Low")
        plt.savefig("test2.png")

    assert np.all(hi == hi_fqir), f"high bits mismatched"
    assert np.all(lo == lo_fqir), f"low bits mismatched"
    print("runtime test passed!")


class Split24To3x8(fmot.nn.SuperStructure):
    def __init__(self):
        super().__init__()
        # use this to generate an int24 vector
        self.gmac = GMACv2(bits_out=24)
        self.prec_split = PrecisionSplit([8, 8, 8], [8, 8, 8])

    def forward(self, x, y):
        z24 = self.gmac([x], [y], [])
        z_lo, z_med, z_hi = self.prec_split(z24)
        self.z24 = z24  # save as a property because we cannot return an int24 result
        return z_lo, z_med, z_hi


def test_split_24_to_3x8(plot=False):
    NDIM = 128
    torch.manual_seed(0)

    model = Split24To3x8()
    cmodel = fmot.ConvertedModel(model)

    cmodel.quantize([(torch.randn(8, NDIM), torch.randn(8, NDIM)) for _ in range(4)])

    x = torch.randn(8, NDIM)
    y = torch.randn(8, NDIM)
    lo_fp, med_fp, hi_fp = model(x, y)
    z_fp = model.z24
    lo_qat, med_qat, hi_qat = cmodel(x, y)
    z_qat = cmodel.model.model.z24

    assert torch.all(lo_fp + med_fp + hi_fp == z_fp)

    qat_eff = lo_qat + med_qat + hi_qat
    if plot:
        import matplotlib.pyplot as plt

        plt.plot(z_qat.flatten(), (z_qat - qat_eff).flatten(), ".")
        plt.savefig("test.png")

    # test that dynamic ranges are the same
    z_qat_maxval = 2 ** (z_qat.quanta + z_qat.bitwidth.bitwidth - 1)
    z_hi_maxval = 2 ** (hi_qat.quanta + hi_qat.bitwidth.bitwidth - 1)
    assert z_qat_maxval == z_hi_maxval, f"{z_qat_maxval=} {z_hi_maxval=}"

    # test that the maximum error is off-by-4 (since three signed-8b vectors are
    # equivalent to 22b, not 24b)
    error = z_qat - qat_eff
    error_int = error * 2 ** (-z_qat.quanta)
    assert torch.max(torch.abs(error_int)) <= 4
    # an equivalent check is that the low-subvector has a quanta 1 higher than x
    assert lo_qat.quanta == z_qat.quanta + 2

    # ensure 1-to-1 between FQIR and cmodel runtimes
    graph = cmodel.trace()
    print(graph)

    x, y = x[0], y[0]
    lo, med, hi = map(lambda x: x.numpy(), cmodel(x, y))
    lo_fqir, med_fqir, hi_fqir = graph.run(x.numpy(), y.numpy(), dequant=True)

    if plot:
        fig, ax = plt.subplots(3)
        s_hi = 2 ** (-hi_qat.quanta.item())
        ax[0].plot(hi * s_hi, hi_fqir * s_hi, ".")
        ax[0].set_title("High")
        s_med = 2 ** (-med_qat.quanta.item())
        ax[1].plot(med * s_med, med_fqir * s_med, ".")
        ax[1].set_title("Medium")
        s_lo = 2 ** (-lo_qat.quanta.item())
        ax[2].plot(lo * s_lo, lo_fqir * s_lo, ".")
        ax[2].set_title("Low")
        plt.savefig("test2.png")

    assert np.all(
        hi == hi_fqir
    ), f"high bits had mismatch {(hi - hi_fqir) * 2**(-hi_qat.quanta.item())}"
    assert np.all(
        med == med_fqir
    ), f"medium bits had mismatch {(med - med_fqir) * 2**(-med_qat.quanta.item())}"
    assert np.all(
        lo == lo_fqir
    ), f"low bits had mismatch {(lo - lo_fqir) * 2**(-lo_qat.quanta.item())}"
    print("runtime test passed!")


class Split24by2(nn.Module):
    num_inputs = 2

    def __init__(self, prec_a, prec_b):
        super().__init__()
        self.mul = GMACv2(24)
        self.prec_split = PrecisionSplit([prec_a, prec_b], [16, 16])

    def forward(self, x, y):
        z = self.mul([x], [y], [])
        z_lo, z_hi = self.prec_split(z)
        return z_lo, z_hi


def utilized_bits(x, quanta):
    x_int = x / 2**quanta

    bits = torch.ceil(torch.log2(torch.max(x_int))) + 1

    return bits


@pytest.mark.parametrize(["prec_a", "prec_b"], [[13, 12], [12, 13], [14, 11], [11, 14]])
def test_split_24_to_13x12(prec_a, prec_b):
    NDIM = 10000
    torch.manual_seed(0)

    model = Split24by2(prec_a, prec_b)
    cmodel = fmot.ConvertedModel(model)

    cmodel.quantize([(torch.randn(8, NDIM), torch.randn(8, NDIM)) for _ in range(4)])

    x = torch.randn(8, NDIM)
    y = torch.randn(8, NDIM)
    lo_fp, hi_fp = model(x, y)
    lo_qat, hi_qat = cmodel(x, y)

    lo_bits = utilized_bits(lo_qat, lo_qat.quanta)
    hi_bits = utilized_bits(hi_qat, hi_qat.quanta)
    assert lo_bits == prec_a
    assert hi_bits == prec_b

    graph = cmodel.trace()

    lo_fqir, hi_fqir = graph.run(x[0].numpy(), y[0].numpy(), dequant=True)

    assert np.all(
        hi_fqir == hi_qat[0].detach().cpu().numpy()
    ), f"ratio: {hi_fqir / hi_qat[0].detach().cpu().numpy()}"
    assert np.all(
        lo_fqir == lo_qat[0].detach().cpu().numpy()
    ), f"ratio: {lo_fqir / lo_qat[0].detach().cpu().numpy()}"

    print(f"Precision split test from i24 passed for {prec_a=} {prec_b=}!")


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    test_split_24_to_13x12(13, 12)
    test_split_24_to_13x12(14, 11)
    test_split_24_to_13x12(11, 14)
