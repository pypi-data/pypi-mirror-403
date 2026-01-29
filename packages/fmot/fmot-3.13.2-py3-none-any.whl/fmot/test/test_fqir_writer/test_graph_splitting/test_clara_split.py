import fmot
from fmot.fqir.writer import get_fqir_between
from pathlib import Path
import pytest
import numpy as np

NOISY_NAMES = ["re_noisy", "im_noisy", "igain"]
MASKED_NAMES = ["re_masked", "im_masked", "igain"]


def test_clara_split():
    clara_path = Path(__file__).parent / "clara.pt"

    if not clara_path.exists():
        pytest.skip(reason="clara.pt not distributed with fmot")

    clara = fmot.load(clara_path)
    stft = get_fqir_between(clara, inputs=[0], outputs=NOISY_NAMES)
    denoiser = get_fqir_between(clara, inputs=NOISY_NAMES, outputs=MASKED_NAMES)
    istft = get_fqir_between(clara, inputs=MASKED_NAMES, outputs=[0])


def scramble_clara_weights():
    clara_path = Path(__file__).parent / "clara.pt"

    clara = fmot.load(clara_path)

    for p in clara.subgraphs["ARITH"].parameters:
        low = np.min(p.value)
        high = np.max(p.value)
        if low == high:
            low = high - 1
        p.value = np.random.randint(low=low, high=high, size=p.shape)

    fmot.save(clara, clara_path)


if __name__ == "__main__":
    scramble_clara_weights()
    test_clara_split()
