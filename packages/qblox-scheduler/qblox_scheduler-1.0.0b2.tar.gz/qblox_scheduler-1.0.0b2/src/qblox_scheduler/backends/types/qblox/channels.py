# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Python dataclasses for compilation to Qblox hardware."""

from __future__ import annotations

from typing import Optional

from qblox_scheduler.backends.qblox.enums import DistortionCorrectionLatencyEnum
from qblox_scheduler.structure.model import DataStructure


class ComplexChannelDescription(DataStructure):
    """
    Information needed to specify a complex input/output in the
    :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.
    """

    marker_debug_mode_enable: bool = False
    """
    Setting to send 4 ns trigger pulse on the marker
    located next to the I/O port along with each operation.
    The marker will be pulled high at the same time as the module starts playing or acquiring.
    """
    mix_lo: bool = True
    """Whether IQ mixing with a local oscillator is enabled for this channel.
    Effectively always ``True`` for RF modules."""
    downconverter_freq: Optional[float] = None
    """
    Downconverter frequency that should be taken into account w
    hen determining the modulation frequencies for this channel.
    Only relevant for users with custom Qblox downconverter hardware.
    """
    distortion_correction_latency_compensation: int = DistortionCorrectionLatencyEnum.NO_DELAY_COMP
    """
    Delay compensation setting that either
    delays the signal by the amount chosen by the settings or not.
    """


class RealChannelDescription(DataStructure):
    """
    Information needed to specify a real input/output in the
    :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.
    """

    marker_debug_mode_enable: bool = False
    """
    Setting to send 4 ns trigger pulse on the marker located
    next to the I/O port along with each operation.
    The marker will be pulled high at the same time as the module starts playing or acquiring.
    """
    mix_lo: bool = True
    """Whether IQ mixing with a local oscillator is enabled for this channel.
    Effectively always ``True`` for RF modules."""
    distortion_correction_latency_compensation: int = DistortionCorrectionLatencyEnum.NO_DELAY_COMP
    """
    Delay compensation setting that either
    delays the signal by the amount chosen by the settings or not.
    """


class DigitalChannelDescription(DataStructure):
    """
    Information needed to specify a digital (marker) output
    (for :class:`~.qblox_scheduler.operations.pulse_library.MarkerPulse`) in the
    :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.
    """

    distortion_correction_latency_compensation: int = DistortionCorrectionLatencyEnum.NO_DELAY_COMP
    """
    Delay compensation setting that either
    delays the signal by the amount chosen by the settings or not.
    """


__all__ = ["ComplexChannelDescription", "DigitalChannelDescription", "RealChannelDescription"]
