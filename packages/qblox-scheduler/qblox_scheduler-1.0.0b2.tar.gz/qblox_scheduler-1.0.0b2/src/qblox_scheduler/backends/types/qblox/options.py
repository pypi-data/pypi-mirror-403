# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Python dataclasses for compilation to Qblox hardware."""

# ruff: noqa: TC001

from __future__ import annotations

from collections.abc import Callable
from typing import Literal, Optional, Union

from pydantic import Field, field_validator

from qblox_scheduler.backends.types.common import HardwareOptions, SoftwareDistortionCorrection
from qblox_scheduler.structure.model import DataStructure

from .calibration import (
    ComplexInputGain,
    DigitizationThresholds,
    InputAttenuation,
    OutputAttenuation,
    QbloxHardwareDistortionCorrection,
    QbloxMixerCorrections,
    RealInputGain,
)


class SequencerOptions(DataStructure):
    """
    Configuration options for a sequencer.

    For allowed values, also see `Cluster QCoDeS parameters
    <https://docs.qblox.com/en/main/api_reference/sequencer.html#cluster-qcodes-parameters>`__.

    .. admonition:: Example
        :class: dropdown

        .. code-block:: python

            hardware_compilation_config.hardware_options.sequencer_options = {
                "q0:res-q0.ro": {
                    "init_offset_awg_path_I": 0.1,
                    "init_offset_awg_path_Q": -0.1,
                    "init_gain_awg_path_I": 0.9,
                    "init_gain_awg_path_Q": 1.0,
                    "ttl_acq_threshold": 0.5
                    "qasm_hook_func": foo
                }
            }
    """

    init_offset_awg_path_I: float = Field(default=0.0, ge=-1.0, le=1.0)
    """Specifies what value the sequencer offset for AWG path_I will be reset to
    before the start of the experiment."""
    init_offset_awg_path_Q: float = Field(default=0.0, ge=-1.0, le=1.0)
    """Specifies what value the sequencer offset for AWG path_Q will be reset to
    before the start of the experiment."""
    init_gain_awg_path_I: float = Field(default=1.0, ge=-1.0, le=1.0)
    """Specifies what value the sequencer gain for AWG path_I will be reset to
    before the start of the experiment."""
    init_gain_awg_path_Q: float = Field(default=1.0, ge=-1.0, le=1.0)
    """Specifies what value the sequencer gain for AWG path_Q will be reset to
    before the start of the experiment."""
    ttl_acq_threshold: Optional[float] = None
    """
    For QRM modules only, the threshold value with which to compare the input ADC values
    of the selected input path.
    """
    qasm_hook_func: Optional[Callable] = None
    """
    Function to inject custom qasm instructions after the compiler inserts the
    footer and the stop instruction in the generated qasm program.
    """

    @field_validator(
        "init_offset_awg_path_I",
        "init_offset_awg_path_Q",
        "init_gain_awg_path_I",
        "init_gain_awg_path_Q",
    )
    @classmethod
    def _init_setting_limits(cls, init_setting: float) -> float:
        # if connectivity contains a hardware config with latency corrections
        if init_setting < -1.0 or init_setting > 1.0:
            raise ValueError(
                f"Trying to set init gain/awg setting to {init_setting} "
                f"in the SequencerOptions. Must be between -1.0 and 1.0."
            )
        return init_setting


class QbloxHardwareOptions(HardwareOptions):
    """
    Datastructure containing the hardware options for each port-clock combination.

    .. admonition:: Example
        :class: dropdown

        Here, the HardwareOptions datastructure is created by parsing a
        dictionary containing the relevant information.

        .. jupyter-execute::

            import pprint
            from qblox_scheduler.schemas.examples.utils import (
                load_json_example_scheme
            )

        .. jupyter-execute::

            from qblox_scheduler.backends.types.qblox import (
                QbloxHardwareOptions
            )
            qblox_hw_options_dict = load_json_example_scheme(
                "qblox_hardware_config_transmon.json")["hardware_options"]
            pprint.pprint(qblox_hw_options_dict)

        The dictionary can be parsed using the :code:`model_validate` method.

        .. jupyter-execute::

            qblox_hw_options = QbloxHardwareOptions.model_validate(qblox_hw_options_dict)
            qblox_hw_options
    """

    input_gain: Optional[dict[str, Union[RealInputGain, ComplexInputGain]]] = None
    """
    Dictionary containing the input gain settings (values) that should be applied
    to the inputs that are connected to a certain port-clock combination (keys).
    """
    output_att: Optional[dict[str, OutputAttenuation]] = None
    """
    Dictionary containing the attenuation settings (values) that should be applied
    to the outputs that are connected to a certain port-clock combination (keys).
    """
    input_att: Optional[dict[str, InputAttenuation]] = None
    """
    Dictionary containing the attenuation settings (values) that should be applied
    to the inputs that are connected to a certain port-clock combination (keys).
    """
    mixer_corrections: Optional[dict[str, QbloxMixerCorrections]] = None  # type: ignore
    """
    Dictionary containing the qblox-specific mixer corrections (values) that should be
    used for signals on a certain port-clock combination (keys).
    """
    sequencer_options: Optional[dict[str, SequencerOptions]] = None
    """
    Dictionary containing the options (values) that should be set
    on the sequencer that is used for a certain port-clock combination (keys).
    """
    distortion_corrections: Optional[  # type: ignore
        dict[
            str,
            Union[
                SoftwareDistortionCorrection,
                QbloxHardwareDistortionCorrection,
                list[QbloxHardwareDistortionCorrection],
            ],
        ]
    ] = None
    digitization_thresholds: Optional[dict[str, DigitizationThresholds]] = None
    """
    Dictionary containing the digitization threshold settings for QTM modules. These are
    the settings that determine the voltage thresholds above which input signals are
    registered as high.
    """
    source_mode: Optional[dict[str, Literal["v_source", "i_source", "ground", "open"]]] = None
    """
    Dictionary containing the sourcing behavior mode (values) that should be applied
    to a certain channel path (keys) [QSM modules].
    """
    measure_mode: Optional[
        dict[str, Literal["automatic", "coarse", "fine_nanoampere", "fine_picoampere"]]
    ] = None
    """
    Dictionary containing the measurement precision mode (values) that should be applied
    to a certain channel path (keys) [QSM modules].
    """
    slew_rate: Optional[dict[str, float]] = None
    """
    Dictionary containing the maximum rate in volt/second (values) at which a certain
    channel path (keys) can linearly change its output voltage or current [QSM modules].
    """
    integration_time: Optional[dict[str, float]] = None
    """
    Dictionary containing the integration time in seconds (values) that should be applied
    to a certain channel path (keys) [QSM modules].
    """
    safe_voltage_range: Optional[dict[str, tuple[float, float]]] = None
    """
    Dictionary containing the voltage limits -min, +max (values) that should be applied
    to a certain channel path (keys) to protect the device against accidental overvolting
    [QSM modules].
    """


__all__ = ["QbloxHardwareOptions", "SequencerOptions"]
