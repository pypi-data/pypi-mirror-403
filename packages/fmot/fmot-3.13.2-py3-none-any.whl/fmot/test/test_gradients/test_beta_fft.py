import torch
from fmot.beta import signal24
from fmot.nn import STFT, ISTFT
from fmot.precisions import int24, int16
from fmot import ConvertedModel


class STFTWrapper(torch.nn.Module):
    def __init__(self, layer):
        super().__init__()
        self.layer = layer

    def forward(self, x):
        # pull out the cast-16 versions of re / im
        _, (re, im) = self.layer(x)
        return re, im


def _measure_stft_grads(input: torch.Tensor, model: torch.nn.Module):
    input.requires_grad = True

    re, im = model(input)
    loss = (re.abs() + im.abs()).pow(2).mean()
    loss.backward()
    grad = input.grad.clone()
    input.grad = None

    return grad


def test_stft_grads(hop=128, n_stages=0):
    i16_stft = STFT(
        n_fft=2 * hop,
        hop_size=hop,
        n_stages=n_stages,
        window_fn=torch.hann_window(2 * hop),
    )
    i24_stft = STFTWrapper(
        signal24.STFT(
            n_fft=2 * hop,
            hop_size=hop,
            n_stages=n_stages,
            window_fn=torch.hann_window(2 * hop),
            act_precision=int24,
            weight_precision=int16,
        )
    )

    # full-precision gradient check
    x = torch.randn(8, 100, hop)

    grad16 = _measure_stft_grads(x, i16_stft)
    grad24 = _measure_stft_grads(x, i24_stft)

    gdiff = (grad16 - grad24).pow(2).mean().sqrt()
    print(f"full-precision gradient difference (white noise): {gdiff}")

    x_sine = torch.sin(torch.arange(100 * hop) * 2 * torch.pi / 100).reshape(
        1, 100, hop
    )

    grad16 = _measure_stft_grads(x_sine, i16_stft)
    grad24 = _measure_stft_grads(x_sine, i24_stft)

    gdiff = (grad16 - grad24).pow(2).mean().sqrt()
    print(f"full-precision gradient difference (sine): {gdiff}")

    cmodel16 = ConvertedModel(i16_stft, batch_dim=0, seq_dim=1)
    cmodel24 = ConvertedModel(i24_stft, batch_dim=0, seq_dim=1)

    calib = [torch.randn(8, 10, hop) for _ in range(4)] + [x_sine]

    cmodel16.quantize(calib)
    cmodel24.quantize(calib)

    grad_fp = _measure_stft_grads(x_sine, i16_stft)
    grad_i16_quant = _measure_stft_grads(x_sine, cmodel16)
    grad_i24_quant = _measure_stft_grads(x_sine, cmodel24)

    gdiff_i16 = (grad_fp - grad_i16_quant).pow(2).mean().sqrt()
    gdiff_i24 = (grad_fp - grad_i24_quant).pow(2).mean().sqrt()
    print(f"quant-16 gradient difference (sine): {gdiff_i16}")
    print(f"quant-24 gradient difference (sine): {gdiff_i24}")


def _measure_istft_grads(re: torch.Tensor, im: torch.Tensor, model: torch.nn.Module):
    re.requires_grad = True
    im.requires_grad = True

    out = model(re, im)
    loss = out.pow(2).mean()
    loss.backward()
    grad_re = re.grad.clone()
    grad_im = im.grad.clone()
    re.grad = None
    im.grad = None

    return grad_re, grad_im


def test_istft_grads(hop=128, n_stages=0):
    istft16 = ISTFT(
        2 * hop, hop, n_stages=n_stages, window_fn=torch.hann_window(2 * hop)
    )
    istft24 = signal24.ISTFT(
        2 * hop,
        hop,
        n_stages=n_stages,
        window_fn=torch.hann_window(2 * hop),
        act_precision=int24,
        weight_precision=int16,
    )

    x = torch.randn(8, 100, 2 * hop)
    f = torch.fft.rfft(x, dim=-1)
    re = f.real
    im = f.imag

    grad16_re, grad16_im = _measure_istft_grads(re, im, istft16)
    grad24_re, grad24_im = _measure_istft_grads(re, im, istft24)

    re_error = (grad16_re - grad24_re).pow(2).mean().sqrt()
    im_error = (grad16_im - grad24_im).pow(2).mean().sqrt()

    print(f"F.P. re grad difference (white noise): {re_error}")
    print(f"F.P. im grad difference (white noise): {im_error}")

    cmodel16 = ConvertedModel(istft16, batch_dim=0, seq_dim=1)
    cmodel24 = ConvertedModel(istft24, batch_dim=0, seq_dim=1)

    calib = []
    for _ in range(4):
        x = torch.randn(8, 10, 2 * hop)
        f = torch.fft.rfft(x, dim=-1)
        calib.append((f.real, f.imag))

    cmodel16.quantize(calib)
    cmodel24.quantize(calib)

    qgrad16_re, qgrad16_im = _measure_istft_grads(re, im, cmodel16)
    qgrad24_re, qgrad24_im = _measure_istft_grads(re, im, cmodel24)

    re24_error = (grad16_re - qgrad24_re).pow(2).mean().sqrt()
    im24_error = (grad16_im - qgrad24_im).pow(2).mean().sqrt()
    re16_error = (grad16_re - qgrad16_re).pow(2).mean().sqrt()
    im16_error = (grad16_im - qgrad16_im).pow(2).mean().sqrt()
    print(
        f"quant-24 grad difference (white-noise): ({re24_error:.3E}, {im24_error:.3E})"
    )
    print(
        f"quant-16 grad difference (white-noise): ({re16_error:.3E}, {im16_error:.3E})"
    )


if __name__ == "__main__":
    print("STFT test")
    test_stft_grads(n_stages=4)
    print("ISTFT test")
    test_istft_grads(n_stages=4)
