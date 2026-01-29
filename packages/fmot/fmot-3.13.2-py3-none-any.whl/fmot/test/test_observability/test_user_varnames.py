import torch
import fmot
from torch import nn
from fmot.nn import TagVarname
import pytest
from typing import Type
from fmot.functional import tag


class MyModelA(nn.Module):
    # FQIR node idxs mapped to their output tensor names
    idxs_to_names = {0: "pre_relu", 1: "post_relu", 2: "pre_sin", -1: "post_sin"}
    hidden_size = 32

    def __init__(self):
        super().__init__()
        self.lin1 = nn.Linear(32, 32)
        self.tag1 = TagVarname("pre_relu")
        self.relu = nn.ReLU()
        self.tag_relu = TagVarname("post_relu")
        self.lin2 = nn.Linear(32, 32)
        self.tag2 = TagVarname("pre_sin")
        self.tag_out = TagVarname("post_sin")

    def forward(self, x):
        x = self.lin1(x)
        x = self.tag1(x)
        x = self.relu(x)
        x = self.tag_relu(x)
        x = self.lin2(x)
        x = self.tag2(x)
        x = torch.sin(x)
        x = self.tag_out(x)
        return x


class ReusedName(nn.Module):
    idxs_to_names = {0: "hello_world.0", 1: "hello_world.1"}
    hidden_size = 32

    def __init__(self):
        super().__init__()
        self.lin1 = nn.Linear(32, 32)
        self.lin2 = nn.Linear(32, 32)
        self.tag1 = TagVarname("hello_world.0")
        self.tag2 = TagVarname("hello_world.1")

    def forward(self, x):
        x = self.lin1(x)
        x = self.tag1(x)
        x = self.lin2(x)
        x = self.tag2(x)
        return x


class InputRenamer(nn.Module):
    idxs_to_names = {0: "my_output"}
    hidden_size = 32
    expected_input_name = "signature_name"

    def __init__(self):
        super().__init__()
        self.lin = nn.Linear(32, 32)
        self.tag_in = TagVarname("my_input")
        self.tag_out = TagVarname("my_output")

    def forward(self, signature_name):
        x = self.tag_in(signature_name)
        x = self.lin(x)
        x = self.tag_out(x)
        return x


class FunctionalTagging(nn.Module):
    idxs_to_names = {
        0: "lin1.out",
        1: "lin1.relu",
        2: "lin2.out",
        3: "lin2.relu",
    }
    hidden_size = 32

    def __init__(self):
        super().__init__()
        self.lin1 = nn.Linear(32, 32)
        self.lin2 = nn.Linear(32, 32)

    def forward(self, x):
        x = self.lin1(x)
        x = tag(x, "lin1.out")
        x = x.relu()
        x = tag(x, "lin1.relu")
        x = self.lin2(x)
        x = tag(x, "lin2.out")
        x = x.relu()
        x = tag(x, "lin2.relu")
        return x


@pytest.mark.parametrize(
    "arch", [MyModelA, ReusedName, InputRenamer, FunctionalTagging]
)
def test_variable_tagging(arch: Type[nn.Module]):
    torch.manual_seed(0)
    model = arch()
    cmodel = fmot.ConvertedModel(model)
    cmodel.quantize([torch.randn(32, arch.hidden_size) for _ in range(4)])
    graph = cmodel.trace()

    arith = graph.subgraphs["ARITH"]
    nodes = arith.nodes

    for idx, name in arch.idxs_to_names.items():
        assert (
            nodes[idx].outputs[0].name.startswith(name)
        ), f"node {idx} expected to have name {name}, got {nodes[idx].outputs[0]}. DUMP: \n{arith}"

    if hasattr(model, "expected_input_name"):
        assert arith.inputs[0].name == model.expected_input_name

    print(f"SUCCESS:\n{arith}")


def test_reused_name():
    torch.manual_seed(0)
    model = nn.Sequential(
        nn.Linear(32, 32),
        TagVarname("hello"),
        nn.ReLU(),
        TagVarname("hello"),
        nn.Linear(32, 32),
        TagVarname("hello"),
    )
    cmodel = fmot.ConvertedModel(model)
    cmodel.quantize([torch.randn(8, 32) for _ in range(4)])

    graph = cmodel.trace()

    print(graph.subgraphs["ARITH"])

    for i, node in enumerate(graph.subgraphs["ARITH"].nodes):
        out = node.outputs[0]
        assert out.name.startswith("hello")


if __name__ == "__main__":
    test_reused_name()
