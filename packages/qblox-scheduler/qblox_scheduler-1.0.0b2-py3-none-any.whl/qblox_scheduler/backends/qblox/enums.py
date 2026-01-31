# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Enums used by Qblox backend."""

from __future__ import annotations

import warnings
from enum import Enum, EnumMeta


class _DeprecatedEnum(EnumMeta):
    def __call__(cls, *args, **kwargs):  # noqa: ANN204
        if len(args) == 1:
            item = args[0]
            if (
                item.lower() == "bypassed"
                or item.lower() == "enabled"
                or item.lower() == "delay_comp"
            ):
                warnings.warn(
                    "QbloxFilterConfig and QbloxFilterMarkerDelay have been renamed to "
                    "FilterConfig and FilterMarkerDelay, "
                    "and will be deprecated in qblox_scheduler v2.0",
                    FutureWarning,
                    stacklevel=2,
                )
        return EnumMeta.__call__(cls, *args, **kwargs)

    def __getattribute__(cls, item):  # noqa: ANN001, ANN204
        if item.lower() == "bypassed" or item.lower() == "enabled" or item.lower() == "delay_comp":
            warnings.warn(
                "QbloxFilterConfig and QbloxFilterMarkerDelay have been renamed to "
                "FilterConfig and FilterMarkerDelay, "
                "and will be deprecated in qblox_scheduler v2.0",
                FutureWarning,
                stacklevel=2,
            )
        return EnumMeta.__getattribute__(cls, item)

    def __getitem__(cls, item):  # noqa: ANN001, ANN204
        if item.lower() == "bypassed" or item.lower() == "enabled" or item.lower() == "delay_comp":
            warnings.warn(
                "QbloxFilterConfig and QbloxFilterMarkerDelay have been renamed to "
                "FilterConfig and FilterMarkerDelay, "
                "and will be deprecated in qblox_scheduler v2.0",
                FutureWarning,
                stacklevel=2,
            )
        return EnumMeta.__getitem__(cls, item)


class ChannelMode(str, Enum):
    """Enum for the channel mode of the Sequencer."""

    COMPLEX = "complex"
    REAL = "real"
    DIGITAL = "digital"


class FilterConfig(str, Enum):
    """Configuration of a filter."""

    BYPASSED = "bypassed"
    ENABLED = "enabled"
    DELAY_COMP = "delay_comp"


class FilterMarkerDelay(str, Enum):
    """Marker delay setting of a filter."""

    BYPASSED = "bypassed"
    DELAY_COMP = "delay_comp"


class QbloxFilterConfig(str, Enum, metaclass=_DeprecatedEnum):
    """Deprecated."""

    BYPASSED = "bypassed"
    ENABLED = "enabled"
    DELAY_COMP = "delay_comp"


class QbloxFilterMarkerDelay(str, Enum, metaclass=_DeprecatedEnum):
    """Deprecated."""

    BYPASSED = "bypassed"
    DELAY_COMP = "delay_comp"


class DistortionCorrectionLatencyEnum(int, Enum):
    """Settings related to distortion corrections."""

    NO_DELAY_COMP = 0
    """Setting for no distortion correction delay compensation"""
    EXP0 = 2
    """Setting for delay compensation equal to exponential overshoot or undershoot correction"""
    EXP1 = 4
    """Setting for delay compensation equal to exponential overshoot or undershoot correction"""
    EXP2 = 8
    """Setting for delay compensation equal to exponential overshoot or undershoot correction"""
    EXP3 = 16
    """Setting for delay compensation equal to exponential overshoot or undershoot correction"""
    FIR = 32
    """Setting for delay compensation equal to FIR filter"""

    def __int__(self) -> int:
        """Enable direct conversion to int."""
        return self.value

    def __index__(self) -> int:
        """Support index operations."""
        return self.value

    def __and__(self, other: DistortionCorrectionLatencyEnum | int) -> int:
        """Support bitwise AND operations."""
        if isinstance(other, Enum):
            return self.value & other.value
        return self.value & other

    def __rand__(self, other: DistortionCorrectionLatencyEnum | int) -> int:
        """Support bitwise AND operations, other order."""
        return self.__and__(other)

    def __or__(self, other: DistortionCorrectionLatencyEnum | int) -> int:
        """Support bitwise OR operations."""
        if isinstance(other, Enum):
            return self.value | other.value
        return self.value | other

    def __ror__(self, other: DistortionCorrectionLatencyEnum | int) -> int:
        """Support bitwise OR operations, other order."""
        return self.__or__(other)


class LoCalEnum(str, Enum):
    """Settings related to the LO part of automatic mixer corrections."""

    OFF = "off"
    ON_LO_FREQ_CHANGE = "on_lo_freq_change"
    ON_LO_INTERM_FREQ_CHANGE = "on_lo_interm_freq_change"


class SidebandCalEnum(str, Enum):
    """Settings related to the NCO part of automatic mixer corrections."""

    OFF = "off"
    ON_INTERM_FREQ_CHANGE = "on_interm_freq_change"


class TimetagTraceType(str, Enum):
    """Types trace acquisition possible for a QTM."""

    SCOPE = "scope"
    TIMETAG = "timetag"
