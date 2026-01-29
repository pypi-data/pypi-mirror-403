from typing import Tuple, List
import torch
import fmot
from typing import List
from fmot.nn.atomics import GMACv2


class Multiply(torch.nn.Module):
    def __init__(self, act_precision=24):
        super().__init__()
        self.gmac = GMACv2(bits_out=act_precision)

    def forward(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        out = self.gmac([x], [y], [])
        return out


class Multiply_Vanilla(torch.nn.Module):
    def forward(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        out = x * y
        return out


class CastToPrecision(torch.nn.Module):
    def __init__(self, act_precision=16):
        super().__init__()
        self.gmac = GMACv2(bits_out=act_precision, scalar_multipliers=torch.tensor([1]))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.gmac([], [], [x])
        return out


class _MIMO_Faulty_Sequencer(fmot.nn.MIMOSequencer, fmot.nn.SuperStructure):
    def __init__(self, dim: int, num_states: int = 8, act_precision=24):
        self.dim = dim
        self.num_states = num_states

        state_shapes = []
        for _ in range(self.num_states):
            state_shapes.append([self.dim])

        super().__init__(
            num_inputs=1,
            num_outputs=1,
            state_shapes=state_shapes,
            return_hidden_state=True,
        )

        self.mul_1 = Multiply(act_precision=act_precision)
        self.cast_16 = CastToPrecision(16)

    def step(
        self, inputs_t: List[torch.Tensor], state: List[torch.Tensor]
    ) -> Tuple[List[torch.Tensor], List[torch.Tensor]]:
        (x,) = inputs_t

        for s_i in state:
            out_1 = self.mul_1(x, s_i)

        return [self.cast_16(out_1)], state


class _Faulty_Sequencer(fmot.nn.Sequencer, fmot.nn.SuperStructure):
    def __init__(self, dim: int, num_states: int = 8, act_precision=24):
        self.dim = dim
        self.num_states = num_states

        state_shapes = []
        for _ in range(self.num_states):
            state_shapes.append([self.dim])

        super().__init__(
            state_shapes=state_shapes,
        )

        self.mul_1 = Multiply(act_precision=act_precision)
        self.add_1 = GMACv2(bits_out=24, scalar_multipliers=torch.tensor([1, 1]))
        self.cast_16 = CastToPrecision(16)

    def step(
        self, input_t: torch.Tensor, state: List[torch.Tensor]
    ) -> Tuple[List[torch.Tensor], List[torch.Tensor]]:
        x = input_t

        new_state = []
        for s_i in state:
            out_1 = self.mul_1(x, s_i)
            new_state.append(self.add_1([], [], [x, s_i]))

        return self.cast_16(out_1), new_state


class ExampleModelMIMO(fmot.nn.SuperStructure):
    def __init__(self, dim, num_states, act_precision=24):
        super().__init__()
        self.seq = _MIMO_Faulty_Sequencer(
            dim=dim, num_states=num_states, act_precision=act_precision
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        ac1,fe1 : tensors of shape (batch, num_frames, hop_size)
        """
        inputs = [x]

        out, _ = self.seq(inputs)
        aec_out = out
        return aec_out[0]


class ExampleModelSISO(torch.nn.Module):
    def __init__(self, dim, num_states, act_precision=24):
        super().__init__()
        self.seq = _Faulty_Sequencer(
            dim=dim, num_states=num_states, act_precision=act_precision
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        ac1,fe1 : tensors of shape (batch, num_frames, hop_size)
        """

        out, _ = self.seq(x)
        return out


if __name__ == "__main__":
    device = "cpu"
    dim = 32
    aec_femto = ExampleModelSISO(dim=dim, num_states=1, act_precision=16)
    aec_femto = aec_femto.to(device)
    cmodel = fmot.ConvertedModel(aec_femto, batch_dim=0, seq_dim=1)
    calib_data = [torch.randn(2, 5, dim).to(device), torch.randn(2, 5, dim).to(device)]
    cmodel.quantize(calib_data)
    fqir_graph = cmodel.trace()
    print(fqir_graph)
