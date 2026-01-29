import torch
from torch import nn
import fmot


class MyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lin1 = nn.Linear(32, 32)
        self.lin2 = nn.Linear(32, 32)

    def forward(self, x):
        x = self.lin1(x)
        fmot.tag(x, "lin.1")
        x = torch.relu(x)
        fmot.tag(x, "relu.1")
        x = self.lin2(x)
        fmot.tag(x, "lin.2")
        x = torch.relu(x)
        fmot.tag(x, "relu.2")
        return x


model = MyModel()
cmodel = fmot.ConvertedModel(model)
cmodel.quantize([torch.randn(32, 32) for _ in range(4)])
graph = cmodel.trace()

# print out the arithmetic graph:
print(graph.subgraphs["ARITH"])
