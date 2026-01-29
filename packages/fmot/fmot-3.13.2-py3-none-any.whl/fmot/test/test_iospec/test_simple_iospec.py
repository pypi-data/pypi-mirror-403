import torch
from torch import nn, Tensor
import fmot
from fmot.iospec import iospec_from_fqir
from tempfile import NamedTemporaryFile


def test_simple_model():
    model = nn.Sequential(nn.Linear(32, 32), nn.Sigmoid())
    cmodel = fmot.ConvertedModel(model, batch_dim=0, seq_dim=1)
    cmodel.quantize([torch.randn(8, 10, 32) for _ in range(10)])
    graph = cmodel.trace()

    iospec = iospec_from_fqir(graph)
    print(iospec)

    with NamedTemporaryFile(suffix=".yaml") as f:
        iospec.write_spec_to_file(f.name)

    assert len(iospec.latched_input_names()) == 0


def test_latched_model():
    class MyLatchedModel(nn.Module):
        def forward(self, x, config):
            y = x * config
            return y

    model = MyLatchedModel()
    cmodel = fmot.ConvertedModel(model, batch_dim=0, seq_dim=1)
    cmodel.quantize(
        [(torch.randn(8, 10, 32), torch.randn(8, 10, 32)) for _ in range(10)]
    )
    graph = cmodel.trace()

    iospec = iospec_from_fqir(graph, latch_input_names=["config"])
    print(iospec)
    assert len(iospec.simple_sequences) == 2

    with NamedTemporaryFile(suffix=".yaml") as f:
        iospec.write_spec_to_file(f.name)

    assert len(iospec.latched_input_names()) == 1
    assert iospec.latched_input_names()[0] == "config"


if __name__ == "__main__":
    test_simple_model()
    print()
    test_latched_model()
