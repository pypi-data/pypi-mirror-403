# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Python dataclasses for compilation to Qblox hardware."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from qblox_scheduler.backends.qblox.enums import ChannelMode


@dataclass(frozen=True)
class BoundedParameter:
    """Specifies a certain parameter with a fixed max and min in a certain unit."""

    min_val: float
    """Min value allowed."""
    max_val: float
    """Max value allowed."""
    units: str
    """Units in which the parameter is specified."""


@dataclass(frozen=True)
class StaticHardwareProperties:
    """Specifies the fixed hardware properties needed in the backend."""

    instrument_type: str
    """The type of instrument."""

    max_acquisition_bin_count: int
    """Number of available acquisition bins."""

    def _get_connected_io_indices(self, mode: str, channel_idx: str) -> tuple[int, ...]:
        """Return the connected input/output indices associated to this channel name."""
        idx = int(channel_idx)
        return (2 * idx, 2 * idx + 1) if mode == ChannelMode.COMPLEX else (idx,)

    def _get_connected_output_indices(self, channel_name: str) -> tuple[int, ...]:
        """Return the connected output indices associated to this channel name."""
        mode, io, idx = channel_name.split("_")
        return self._get_connected_io_indices(mode, idx) if "output" in io else ()

    def _get_connected_input_indices(
        self, channel_name: str, channel_name_measure: Union[list[str], None]
    ) -> tuple[int, ...]:
        """Return the connected input indices associated to this channel name."""
        mode, io, idx = channel_name.split("_")
        if "input" in io:
            if channel_name_measure is None:
                return self._get_connected_io_indices(mode, idx)
        elif channel_name_measure is not None:
            if len(channel_name_measure) == 1:
                mode_measure, _, idx_measure = channel_name_measure[0].split("_")
                return self._get_connected_io_indices(mode_measure, idx_measure)
            else:
                # Edge case for compatibility with hardware config version 0.1 (SE-427)
                return (0, 1)

        return ()


@dataclass(frozen=True)
class StaticAnalogModuleProperties(StaticHardwareProperties):
    """Specifies the fixed hardware properties needed in the backend for QRM/QCM modules."""

    max_awg_output_voltage: Optional[float]
    """Maximum output voltage of the awg."""
    mixer_dc_offset_range: BoundedParameter
    """Specifies the range over which the dc offsets can be set that are used for mixer
    calibration."""
    channel_name_to_digital_marker: dict[str, int]
    """A mapping from channel_name to digital marker setting.
    Specifies which marker bit needs to be set at start if the
    output (as a string ex. `complex_output_0`) contains a pulse."""
    default_markers: dict[str, int] | None = None
    """The default markers value to set at the beginning of programs and reset marker pulses to.
    A mapping from channel name to marker.
    Important for RF instruments that use the set_mrk command to enable/disable the RF output."""


@dataclass(frozen=True)
class StaticTimetagModuleProperties(StaticHardwareProperties):
    """Specifies the fixed hardware properties needed in the backend for QTM modules."""


@dataclass(frozen=True)
class StaticDCModuleProperties(StaticHardwareProperties):
    """Specifies the fixed hardware properties needed in the backend for QSM modules."""


__all__ = [
    "BoundedParameter",
    "StaticAnalogModuleProperties",
    "StaticDCModuleProperties",
    "StaticHardwareProperties",
    "StaticTimetagModuleProperties",
]
