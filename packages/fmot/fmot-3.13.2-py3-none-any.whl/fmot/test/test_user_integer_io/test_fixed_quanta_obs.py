from fmot.qat.nn.quantizers import FixedQuantaObserver
import pytest


@pytest.mark.parametrize(
    ["limits", "bitwidth", "expected_quanta", "clipping_tolerance"],
    [
        # at i16, with clipping tolerance we select -15
        [(-1, 1), 16, -15, 1],
        # at i16, without clipping tolerance we select -14
        [(-1, 1), 16, -14, 0],
        # at i8, clipping tolerance is disabled. We will select -6
        [(-1, 1), 8, -6, 1],
        # presenting an asymmetric input range, we will select -7
        [(-1, 1 - 1 / 128), 8, -7, 1],
    ],
)
def test_from_limits(limits, bitwidth, expected_quanta, clipping_tolerance):
    obs = FixedQuantaObserver.from_limits(
        *limits, bitwidth=bitwidth, i16_clipping_tolerance=clipping_tolerance
    )
    quanta = obs.calculate_quanta(bitwidth, verbose=False)
    assert quanta == expected_quanta
