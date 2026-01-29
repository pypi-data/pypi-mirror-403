import torch
import fmot
from torch import nn
from fmot.precisions import int24, int16
import math


def test_glog(plot=False):
    class GLOGTester(nn.Module):
        def __init__(self, theta):
            super().__init__()
            self.gmac_in = fmot.nn.GMACv2(fmot.precisions.int24)
            self.glog = fmot.nn.GTelescopeLogIdentity(theta, torch.log, 2**12)
            self.prec_split = fmot.nn.PrecisionSplit([13, 12], [16, 16])

        def forward(self, a, b):
            x = self.gmac_in([a], [b], [])
            y = self.glog(x)
            lo, hi = self.prec_split(y)
            return lo, hi

    class LogBaseline(nn.Module):
        def forward(self, a, b):
            return torch.log(a * b)

    dynrange = 2**23
    x = torch.exp(torch.linspace(0, math.log(dynrange), 1000))
    a = torch.sqrt(x)

    theta = 2**11
    glog = GLOGTester(theta)
    bl = LogBaseline()

    lo, hi = glog(a, a)

    cglog = fmot.ConvertedModel(glog)
    cglog.quantize([(a.unsqueeze(0), a.unsqueeze(0))] * 2)

    bl = fmot.ConvertedModel(bl)
    bl.quantize([(a.unsqueeze(0), a.unsqueeze(0))] * 2)

    lo_q, hi_q = cglog(a, a)
    qbl = bl(a, a)

    expected = lo + hi
    quant = lo_q + hi_q
    baseline = qbl

    error_quant = (expected - quant).pow(2).mean() / expected.pow(2).mean()
    error_baseline = (expected - baseline).pow(2).mean() / expected.pow(2).mean()

    assert error_quant < error_baseline

    print(error_quant.sqrt(), error_baseline.sqrt())

    if plot:
        import matplotlib.pyplot as plt

        plt.plot(x.numpy(), (lo + hi).numpy(), label="Float")
        plt.plot(x.numpy(), (lo_q + hi_q).numpy(), label="Quant GTelescope")
        plt.plot(x.numpy(), qbl.numpy(), label="Quant Baseline")
        plt.title("Quantized int24 Log")
        plt.legend()
        plt.xscale("log", base=2)
        plt.xlabel("x")
        plt.ylabel("log(x)")
        plt.show()


def test_grsqrt(plot=False):
    class GRsqrtTester(nn.Module):
        def __init__(self, theta):
            super().__init__()
            self.gmac_in = fmot.nn.GMACv2(fmot.precisions.int24)
            self.glog = fmot.nn.GTelescopePowIdentity(theta, torch.rsqrt, 2**12)
            self.prec_split = fmot.nn.PrecisionSplit([13, 12], [16, 16])

        def forward(self, a, b):
            x = self.gmac_in([a], [b], [])
            y = self.glog(x)
            lo, hi = self.prec_split(y)
            return lo, hi

    class RsqrtBaseline(nn.Module):
        def forward(self, a, b):
            return torch.rsqrt(a * b)

    dynrange = 2**23
    x = torch.exp(torch.linspace(0, math.log(dynrange), 1000))
    a = torch.sqrt(x)

    theta = 2**11
    glog = GRsqrtTester(theta)
    bl = RsqrtBaseline()

    lo, hi = glog(a, a)

    cglog = fmot.ConvertedModel(glog)
    cglog.quantize([(a.unsqueeze(0), a.unsqueeze(0))] * 2)

    bl = fmot.ConvertedModel(bl)
    bl.quantize([(a.unsqueeze(0), a.unsqueeze(0))] * 2)

    lo_q, hi_q = cglog(a, a)
    qbl = bl(a, a)

    expected = lo + hi
    quant = lo_q + hi_q
    baseline = qbl

    error_quant = (expected - quant).pow(2).mean() / expected.pow(2).mean()
    error_baseline = (expected - baseline).pow(2).mean() / expected.pow(2).mean()

    assert error_quant < error_baseline

    print(error_quant.sqrt(), error_baseline.sqrt())

    if plot:
        import matplotlib.pyplot as plt

        plt.plot(x.numpy(), (lo + hi).numpy(), label="Float")
        plt.plot(x.numpy(), (lo_q + hi_q).numpy(), label="Quant GTelescope")
        plt.plot(x.numpy(), qbl.numpy(), label="Quant Baseline")
        plt.title("Quantized int24 rsqrt")
        plt.legend()
        plt.xscale("log", base=2)
        plt.yscale("log", base=2)
        plt.xlabel("x")
        plt.ylabel("rsqrt(x)")
        plt.show()


def test_greduce_sum():
    class GreduceModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.combine_in = fmot.nn.GMACv2(int24)
            self.greduce = fmot.nn.GReduceSum(int24, int24, -1, keepdim=True)
            self.prec_split = fmot.nn.PrecisionSplit([13, 12], [16, 16])

        def forward(self, a, b):
            z = self.combine_in([a], [b], [])
            z_red = self.greduce(z)
            z_lo, z_hi = self.prec_split(z_red)
            return z_lo, z_hi

    class ReduceModel(nn.Module):
        """baseline reduction model"""

        def forward(self, a, b):
            z = a * b
            return torch.sum(z, dim=-1, keepdim=True)

    model = GreduceModel()

    x = torch.exp(torch.linspace(0, math.log(2**24), 32 * 128)).reshape(128, 32)

    a, b = torch.sqrt(x), torch.sqrt(x)

    zlo, zhi = model(a, b)
    z = zlo + zhi

    z_exp = (a * b).sum(-1, keepdim=True)

    assert torch.all(z == z_exp)

    cmodel = fmot.ConvertedModel(model)
    cmodel.quantize([(a, b) for _ in range(3)])

    zlo_q, zhi_q = cmodel(a, b)
    z_q = zlo_q + zhi_q

    bl_cmodel = fmot.ConvertedModel(ReduceModel())
    bl_cmodel.quantize([(a, b) for _ in range(3)])

    z_bl = bl_cmodel(a, b)

    qerror = torch.mean((z_q - z_exp) ** 2).sqrt() / torch.mean(z_exp.pow(2)).sqrt()
    qerror_bl = torch.mean((z_bl - z_exp) ** 2).sqrt() / torch.mean(z_exp.pow(2)).sqrt()
    print(qerror, qerror_bl)


if __name__ == "__main__":
    test_grsqrt(plot=True)
    test_glog(plot=True)
    test_greduce_sum()
