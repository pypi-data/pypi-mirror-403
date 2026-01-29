import torch
from fmot.nn import CumulativeFlattenedLinear


def test_docstring(plot=False):
    ch_per_timestep = 16
    seq_length = 32
    in_channels = ch_per_timestep * seq_length
    out_channels = 1

    model = torch.nn.Sequential(
        torch.nn.Flatten(), torch.nn.Linear(in_channels, out_channels)
    )
    converted = CumulativeFlattenedLinear(seq_length, 0, ch_per_timestep, out_channels)

    print(converted)

    print(in_channels)
    print(converted.n_keep)
    print(converted.in_channels)

    # can load the state-dict from the linear layer
    converted.load_state_dict(model[1].state_dict())

    x = torch.randn(8, ch_per_timestep, seq_length)
    with torch.no_grad():
        y0 = model(x)
        y1 = converted(x)

    print(y0.shape)
    print(y1.shape)

    if plot:
        import matplotlib.pyplot as plt

        plt.axhline(y0[0], color="orange", label="Flatten->Linear")
        plt.plot(y1[0, 0], label="CumulativeFlattenedLinear")
        plt.plot(seq_length - 1, y1[0, 0, -1], "o")
        plt.grid()
        plt.legend()
        plt.xlabel("step")
        plt.show()


if __name__ == "__main__":
    test_docstring()
