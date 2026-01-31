# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Python dataclasses for compilation to Qblox hardware."""

from __future__ import annotations

import math
import warnings
from reprlib import Repr
from typing import Any, Optional

from pydantic import Field, field_validator, model_validator

from qblox_scheduler.backends.qblox.constants import (
    DEFAULT_MIXER_AMP_RATIO,
    DEFAULT_MIXER_PHASE_ERROR_DEG,
    FIR_COEFF_RESOLUTION,
    MAX_MIXER_AMP_RATIO,
    MAX_MIXER_PHASE_ERROR_DEG,
    MIN_MIXER_AMP_RATIO,
    MIN_MIXER_PHASE_ERROR_DEG,
)
from qblox_scheduler.backends.qblox.enums import LoCalEnum, SidebandCalEnum
from qblox_scheduler.backends.types.common import (
    HardwareDistortionCorrection,
    MixerCorrections,
    ValidationWarning,
)
from qblox_scheduler.structure.model import DataStructure

RealInputGain = int
"""
Input gain settings for a real input connected to a port-clock combination.

This gain value will be set on the QRM input ports
that are connected to this port-clock combination.

.. admonition:: Example
    :class: dropdown

    .. code-block:: python

        hardware_compilation_config.hardware_options.input_gain = {
            "q0:res-q0.ro": RealInputGain(2),
        }
"""


class ComplexInputGain(DataStructure):
    """
    Input gain settings for a complex input connected to a port-clock combination.

    This gain value will be set on the QRM input ports
    that are connected to this port-clock combination.

    .. admonition:: Example
        :class: dropdown

        .. code-block:: python

            hardware_compilation_config.hardware_options.input_gain = {
                "q0:res-q0.ro": ComplexInputGain(
                    gain_I=2,
                    gain_Q=3
                ),
            }
    """

    gain_I: int
    """Gain setting on the input receiving the I-component data for this port-clock combination."""
    gain_Q: int
    """Gain setting on the input receiving the Q-component data for this port-clock combination."""


OutputAttenuation = int
"""
Output attenuation setting for a port-clock combination.

This attenuation value will be set on each control-hardware output
port that is connected to this port-clock combination.

.. admonition:: Example
    :class: dropdown

    .. code-block:: python

        hardware_compilation_config.hardware_options.output_att = {
            "q0:res-q0.ro": OutputAttenuation(10),
        }
"""


InputAttenuation = int
"""
Input attenuation setting for a port-clock combination.

This attenuation value will be set on each control-hardware output
port that is connected to this port-clock combination.

.. admonition:: Example
    :class: dropdown

    .. code-block:: python

        hardware_compilation_config.hardware_options.input_att = {
            "q0:res-q0.ro": InputAttenuation(10),
        }
"""


class QbloxMixerCorrections(MixerCorrections):
    """
    Mixer correction settings with defaults set to None, and extra mixer correction
    settings for _automated_ mixer correction.

    These settings will be set on each control-hardware output
    port that is connected to this port-clock combination.

    .. admonition:: Example
        :class: dropdown

        .. code-block:: python

            hardware_compilation_config.hardware_options.mixer_corrections = {
                "q0:res-q0.ro": {
                    auto_lo_cal="on_lo_interm_freq_change",
                    auto_sideband_cal="on_interm_freq_change"
                },
            }
    """

    dc_offset_i: Optional[float] = None  # type: ignore  # (optional due to AMC)
    """The DC offset on the I channel used for this port-clock combination."""
    dc_offset_q: Optional[float] = None  # type: ignore  # (optional due to AMC)
    """The DC offset on the Q channel used for this port-clock combination."""
    amp_ratio: float = Field(
        default=DEFAULT_MIXER_AMP_RATIO, ge=MIN_MIXER_AMP_RATIO, le=MAX_MIXER_AMP_RATIO
    )
    """The mixer gain ratio used for this port-clock combination."""
    phase_error: float = Field(
        default=DEFAULT_MIXER_PHASE_ERROR_DEG,
        ge=MIN_MIXER_PHASE_ERROR_DEG,
        le=MAX_MIXER_PHASE_ERROR_DEG,
    )
    """The mixer phase error used for this port-clock combination."""
    auto_lo_cal: LoCalEnum = LoCalEnum.OFF
    """
    Setting that controls whether the mixer is calibrated upon changing the LO and/or
    intermodulation frequency.
    """

    auto_sideband_cal: SidebandCalEnum = SidebandCalEnum.OFF
    """
    Setting that controls whether the mixer is calibrated upon changing the
    intermodulation frequency.
    """

    @model_validator(mode="before")
    @classmethod
    def warn_if_mixed_auto_and_manual_calibration(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Warn if there is mixed usage of automatic mixer calibration (the auto_*
        settings) and manual mixer correction settings.
        """
        # This is a "before" mode pydantic validator because we use
        # validate_assignment=True, which means an "after" mode validator would fall
        # into an infinite recursion loop.
        if data.get("auto_lo_cal", LoCalEnum.OFF) != LoCalEnum.OFF and not (
            data.get("dc_offset_i") is None and data.get("dc_offset_q") is None
        ):
            warnings.warn(
                f"Setting `auto_lo_cal={data['auto_lo_cal']}` will overwrite settings "
                f"`dc_offset_i={data.get('dc_offset_i')}` and "
                f"`dc_offset_q={data.get('dc_offset_q')}`. To suppress this warning, do not "
                "set either `dc_offset_i` or `dc_offset_q` for this port-clock.",
                ValidationWarning,
            )
            data["dc_offset_i"] = None
            data["dc_offset_q"] = None

        if data.get("auto_sideband_cal", SidebandCalEnum.OFF) != SidebandCalEnum.OFF and not (
            data.get("amp_ratio") is None and data.get("phase_error") is None
        ):
            warnings.warn(
                f"Setting `auto_sideband_cal={data['auto_sideband_cal']}` will "
                f"overwrite settings `amp_ratio={data.get('amp_ratio')}` and "
                f"`phase_error={data.get('phase_error')}`. To suppress this warning, do not "
                "set either `amp_ratio` or `phase_error` for this port-clock.",
                ValidationWarning,
            )
            data["amp_ratio"] = DEFAULT_MIXER_AMP_RATIO
            data["phase_error"] = DEFAULT_MIXER_PHASE_ERROR_DEG

        return data


class QbloxHardwareDistortionCorrection(HardwareDistortionCorrection):
    """A hardware distortion correction specific to the Qblox backend."""

    exp0_coeffs: Optional[list[float]] = None
    """Coefficients of the exponential overshoot/undershoot correction 1."""
    exp1_coeffs: Optional[list[float]] = None
    """Coefficients of the exponential overshoot/undershoot correction 2."""
    exp2_coeffs: Optional[list[float]] = None
    """Coefficients of the exponential overshoot/undershoot correction 3."""
    exp3_coeffs: Optional[list[float]] = None
    """Coefficients of the exponential overshoot/undershoot correction 4."""
    fir_coeffs: Optional[list[float]] = None
    """Coefficients for the FIR filter."""

    @field_validator("fir_coeffs", mode="after")
    @classmethod
    def fir_coeffs_sum_to_1(cls, value: Optional[list[float]]) -> Optional[list[float]]:
        """Validate whether the FIR coefficients sum up to 1."""
        if value is None:
            return value

        if not math.isclose(sum(value), 1, abs_tol=FIR_COEFF_RESOLUTION):
            # Use reprlib to cut off long lists for displaying.
            raise ValueError(
                "FIR coefficient values do not sum up to 1.\n"
                f"sum({Repr().repr(value)})={sum(value)}"
            )
        return value


class DigitizationThresholds(DataStructure):
    """The settings that determine when an analog voltage is counted as a pulse."""

    analog_threshold: Optional[float] = None
    """
    For QTM modules only, this is the voltage threshold above which an input signal is
    registered as high.
    """


__all__ = [
    "ComplexInputGain",
    "DigitizationThresholds",
    "InputAttenuation",
    "OutputAttenuation",
    "QbloxHardwareDistortionCorrection",
    "QbloxMixerCorrections",
    "RealInputGain",
]
