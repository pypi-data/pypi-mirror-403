import torch
from torch import nn
import fmot
from fmot.qat.nn import *
from functools import wraps


def with_rounding(func):
    """Enables rounding during test, then disables it"""

    @wraps(func)
    def wrapped(*args, **kwargs):
        fmot.CONFIG.quant_round = True
        fmot.ROUND_CONFIG.add = True
        fmot.ROUND_CONFIG.mul = True
        fmot.ROUND_CONFIG.prod = True

        func(*args, **kwargs)

        fmot.CONFIG.quant_round = False

    return wrapped


@with_rounding
def test_depthwise_tcn():
    model = nn.Sequential(
        fmot.nn.TemporalConv1d(
            32, 32, kernel_size=3, groups=32
        ),  # depthwise conv should have round=False
        nn.ReLU(),
        fmot.nn.TemporalConv1d(
            32, 32, kernel_size=1, groups=1
        ),  # pointwise conv should have round=True
    )
    cmodel = fmot.ConvertedModel(model, batch_dim=0, seq_dim=2)
    for module in cmodel.modules():
        # check that the add and mul nodes (dwconv nodes) in the model have rounding disabled
        if isinstance(module, (VVAdd, VVMul)):
            assert not module.round
            print(f"{module} correctly had round = False")
        # check that the matmul nodes (pwconv) have rounding enabled
        elif isinstance(module, (Matmul, AddMM)):
            assert module.round
            print(f"{module} correctly had round = True")

    print("Succeeded!")


@with_rounding
def test_user_tag():
    class MyModel(nn.Module):
        def __init__(self, H=32):
            super().__init__()
            self.rnn = nn.GRU(H, H, batch_first=True)

        def forward(self, x):
            y, _ = self.rnn(x)
            return y

    def test_with_config(dont_round: bool = None, expect_round=True):
        model = MyModel(32)
        if dont_round is not None:
            model.dont_round = dont_round

        cmodel = fmot.ConvertedModel(model, batch_dim=0, seq_dim=1)

        for module in filter(
            lambda x: isinstance(x, (VVAdd, VVMul, Matmul, AddMM)), cmodel.modules()
        ):
            assert module.round == expect_round

        print(f"{dont_round=} {expect_round=} Suceeded!")

    test_with_config(dont_round=None, expect_round=True)

    test_with_config(dont_round=False, expect_round=True)

    test_with_config(dont_round=True, expect_round=False)


if __name__ == "__main__":
    test_depthwise_tcn()
    test_user_tag()
