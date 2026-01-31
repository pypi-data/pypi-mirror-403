# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2025, Qblox B.V.
"""Utility functions for type casting."""

from collections.abc import Callable

import numpy as np

from qblox_scheduler.backends.qblox import constants
from qblox_scheduler.operations.expressions import DType
from qblox_scheduler.operations.loop_domains import LinearDomain


def _cast_amplitude_to_signed_int(
    amplitude: float, bits: int = constants.REGISTER_SIZE_BITS
) -> int:
    if np.abs(amplitude) > 1.0:
        raise ValueError("Amplitude must be in the range [-1.0, 1.0].")
    max_gain = 1 << (bits - 1)
    return max(-max_gain, min(round(amplitude * max_gain), max_gain - 1))


def _cast_hz_to_signed_int(value: float) -> int:
    return round(value * constants.NCO_FREQ_STEPS_PER_HZ)


def _cast_deg_to_signed_int(value: float) -> int:
    if value < 0.0 or value > 360.0:  # noqa: PLR2004
        raise ValueError("Phase must be in the range [0.0, 360.0].")
    return round(value * constants.NCO_PHASE_STEPS_PER_DEG)


SIGNED_INT_CASTING_FNS: dict[DType, Callable[[float], int]] = {
    DType.NUMBER: int,
    DType.AMPLITUDE: _cast_amplitude_to_signed_int,
    DType.FREQUENCY: _cast_hz_to_signed_int,
    DType.PHASE: _cast_deg_to_signed_int,
}


def _get_safe_step_size(start: int, stop: int, num: int) -> int:
    if num == 0:
        raise ValueError("Number of steps must be strictly positive.")
    if num == 1:
        return stop - start

    if stop > start:
        return (stop - start) // (num - 1)
    else:
        # We want to return a signed number but round towards 0.
        return -((start - stop) // (num - 1))


def get_safe_step_size(domain: LinearDomain) -> int:
    """
    Get a step size that ensures the final value will not overflow in a sweep.

    Parameters
    ----------
    domain
        The domain to calculate a step size for.

    Returns
    -------
    int
        The step size as a signed integer.

    Raises
    ------
    ValueError
        When the domain is complex.

    """
    start = SIGNED_INT_CASTING_FNS[domain.dtype](np.real(domain.start))
    stop = SIGNED_INT_CASTING_FNS[domain.dtype](np.real(domain.stop))
    return _get_safe_step_size(start, stop, domain.num)
