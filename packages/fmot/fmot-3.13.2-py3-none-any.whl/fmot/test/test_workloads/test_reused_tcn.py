import torch
from torch import nn
import fmot
import pytest


class ReusedOArch(nn.Module):
    def __init__(self, rnn_hidden_size=64, rnn_num_layers=2):
        super().__init__()

        self.conv1 = fmot.nn.TemporalConv1d(
            in_channels=256, out_channels=48, kernel_size=3, stride=1
        )
        self.conv2 = fmot.nn.TemporalConv1d(
            in_channels=48, out_channels=256, kernel_size=3, stride=1
        )
        self.norm1 = nn.BatchNorm1d(num_features=256)
        self.activation1 = nn.ReLU()
        self.rnn1 = nn.LSTM(
            input_size=256, hidden_size=64, num_layers=1, batch_first=True
        )
        self.rnn2 = nn.LSTM(
            input_size=64, hidden_size=256, num_layers=1, batch_first=True
        )
        self.conv_transpose1 = fmot.nn.TemporalConvTranspose1d(
            in_channels=256, out_channels=48, kernel_size=3, stride=1
        )
        self.conv_transpose2 = fmot.nn.TemporalConvTranspose1d(
            in_channels=48, out_channels=256, kernel_size=3, stride=1
        )
        self.norm2 = nn.BatchNorm1d(num_features=256)
        self.activation2 = nn.ReLU()
        self.linear = nn.Linear(in_features=256, out_features=256)

    def forward(self, x):
        y = self.conv1(x)
        y = self.conv2(y)
        y = self.conv1(y)
        y = self.conv2(y)
        y = self.conv1(y)
        y = self.conv2(y)
        y = self.conv1(y)
        y = self.conv2(y)
        y = self.conv1(y)
        y = self.conv2(y)
        y = self.conv1(y)
        y = self.conv2(y)
        y = self.norm1(y)
        y = self.activation1(y)
        y = y.transpose(1, 2)
        y, _ = self.rnn1(y)
        y, _ = self.rnn2(y)
        y = y.transpose(1, 2)
        # y = self.conv_transpose1(y)
        y = self.conv_transpose1(y)
        y = self.conv_transpose2(y)
        y = self.conv_transpose1(y)
        y = self.conv_transpose2(y)
        y = self.conv_transpose1(y)
        y = self.conv_transpose2(y)
        y = self.conv_transpose1(y)
        y = self.conv_transpose2(y)
        y = self.conv_transpose1(y)
        y = self.conv_transpose2(y)
        y = self.conv_transpose1(y)
        y = self.conv_transpose2(y)
        y = self.norm2(y)
        y = self.activation2(y)
        y = y.transpose(1, 2)
        y = self.linear(y)
        y = y.transpose(1, 2)
        return y


class SingleUseOArch(ReusedOArch):
    def forward(self, x):
        y = self.conv1(x)
        y = self.conv2(y)
        y = self.norm1(y)
        y = self.activation1(y)
        y = y.transpose(1, 2)
        y, _ = self.rnn1(y)
        y, _ = self.rnn2(y)
        y = y.transpose(1, 2)
        # y = self.conv_transpose1(y)
        y = self.conv_transpose1(y)
        y = self.conv_transpose2(y)
        y = self.norm2(y)
        y = self.activation2(y)
        y = y.transpose(1, 2)
        y = self.linear(y)
        y = y.transpose(1, 2)
        return y


@pytest.mark.parametrize("reused", [True, False])
def test_oarch(reused):
    if reused:
        model = ReusedOArch()
    else:
        model = SingleUseOArch()

    x = torch.randn(1, 256, 100)
    y = model(x)
    print(y.shape)

    cmodel = fmot.ConvertedModel(model, batch_dim=0, seq_dim=2)
    y1 = cmodel(x)

    print(y1.shape)

    cmodel.quantize([torch.randn(1, 256, 100) for _ in range(4)])
    graph = cmodel.trace()


if __name__ == "__main__":
    test_oarch(reused=True)
