# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""The module contains definitions related to transmon elements."""

from __future__ import annotations

import math
from collections.abc import Hashable
from typing import Any, ClassVar, Literal

import numpy as np

from qblox_scheduler.backends.graph_compilation import (
    DeviceCompilationConfig,
    OperationCompilationConfig,
)
from qblox_scheduler.device_under_test.device_element import DeviceElement
from qblox_scheduler.operations import (
    composite_factories,
    measurement_factories,
    pulse_factories,
    pulse_library,
)
from qblox_scheduler.structure.model import Numbers, Parameter, SchedulerSubmodule
from qblox_scheduler.structure.types import NDArray


class Ports(SchedulerSubmodule):
    """Submodule containing the ports."""

    microwave: str = ""
    """Name of the element's microwave port."""

    flux: str = ""
    """Name of the element's flux port."""

    readout: str = ""
    """Name of the element's readout port."""

    def _fill_defaults(self) -> None:
        if self.parent:
            if not self.microwave:
                self.microwave = f"{self.parent.name}:mw"
            if not self.flux:
                self.flux = f"{self.parent.name}:fl"
            if not self.readout:
                self.readout = f"{self.parent.name}:res"


class ClocksFrequencies(SchedulerSubmodule):
    """Submodule containing the clock frequencies specifying the transitions to address."""

    f01: float = Parameter(
        label="Qubit frequency",
        unit="Hz",
        initial_value=math.nan,
        vals=Numbers(min_value=0, max_value=1e12, allow_nan=True),
    )
    """Frequency of the 01 clock."""

    f12: float = Parameter(
        label="Frequency of the |1>-|2> transition",
        unit="Hz",
        initial_value=math.nan,
        vals=Numbers(min_value=0, max_value=1e12, allow_nan=True),
    )
    """Frequency of the 12 clock."""

    readout: float = Parameter(
        label="Readout frequency",
        unit="Hz",
        initial_value=math.nan,
        vals=Numbers(min_value=0, max_value=1e12, allow_nan=True),
    )
    """Frequency of the ro clock."""


class IdlingReset(SchedulerSubmodule):
    """Submodule containing parameters for doing a reset by idling."""

    duration: float = Parameter(
        initial_value=200e-6,
        unit="s",
        vals=Numbers(min_value=0, max_value=1),
    )
    """Duration of the passive qubit reset (initialization by relaxation)."""


class RxyDRAG(SchedulerSubmodule):
    """
    Submodule containing parameters for performing an Rxy operation.

    The Rxy operation uses a DRAG pulse.
    """

    amp180: float = Parameter(
        label=r"$\pi-pulse amplitude$",
        initial_value=math.nan,
        vals=Numbers(min_value=-10, max_value=10, allow_nan=True),
    )
    r"""Amplitude required to perform a $\pi$ pulse."""

    beta: float = Parameter(
        initial_value=0.0,
        vals=Numbers(min_value=-1, max_value=1),
    )
    """Ratio between the Gaussian Derivative (D) and Gaussian (G) components of the DRAG pulse."""

    duration: float = Parameter(
        initial_value=20e-9,
        unit="s",
        vals=Numbers(min_value=0, max_value=1),
    )
    """Duration of the control pulse."""

    reference_magnitude: ReferenceMagnitude | None = None

    def __init__(
        self,
        name: str,
        parent: DeviceElement | None = None,
        *,
        reference_magnitude_dBm: float = math.nan,
        reference_magnitude_V: float = math.nan,
        reference_magnitude_A: float = math.nan,
        **data: Any,  # noqa: ANN401
    ) -> None:
        super().__init__(parent=parent, name=name, **data)

        self.reference_magnitude = ReferenceMagnitude(
            parent=self,  # type: ignore[reportCallIssue]
            name="reference_magnitude",
            dBm=reference_magnitude_dBm,
            V=reference_magnitude_V,
            A=reference_magnitude_A,
        )


class PulseCompensationModule(SchedulerSubmodule):
    """Submodule containing parameters for performing a PulseCompensation operation."""

    max_compensation_amp: float = Parameter(
        initial_value=math.nan,
        vals=Numbers(min_value=0, allow_nan=True),
    )
    r"""Maximum amplitude for the pulse compensation."""

    time_grid: float = Parameter(
        initial_value=math.nan,
        vals=Numbers(min_value=0, allow_nan=True),
    )
    r"""Time grid for the duration of the compensating pulse."""

    sampling_rate: float = Parameter(
        initial_value=math.nan,
        vals=Numbers(min_value=0, allow_nan=True),
    )
    r"""Sampling rate of the pulses."""


class DispersiveMeasurement(SchedulerSubmodule):
    """
    Submodule containing parameters to perform a measurement.

    The measurement that is performed is using
    :func:`~qblox_scheduler.operations.measurement_factories.dispersive_measurement_transmon`.
    """

    def __init__(
        self,
        name: str,
        parent: DeviceElement | None = None,
        *,
        reference_magnitude_dBm: float = math.nan,
        reference_magnitude_V: float = math.nan,
        reference_magnitude_A: float = math.nan,
        **data: Any,  # noqa: ANN401
    ) -> None:
        super().__init__(parent=parent, name=name, **data)

        self.reference_magnitude = ReferenceMagnitude(
            parent=self,  # type: ignore[reportCallIssue]
            name="reference_magnitude",
            dBm=reference_magnitude_dBm,
            V=reference_magnitude_V,
            A=reference_magnitude_A,
        )

    pulse_type: Literal["SquarePulse"] = Parameter(
        initial_value="SquarePulse",
    )
    """Envelope function that defines the shape of the readout pulse prior to modulation."""

    pulse_amp: float = Parameter(
        initial_value=0.25,
        vals=Numbers(min_value=0, max_value=1),
    )
    """Amplitude of the readout pulse."""

    pulse_duration: float = Parameter(
        initial_value=300e-9,
        unit="s",
        vals=Numbers(min_value=0, max_value=1),
    )
    """Duration of the readout pulse."""

    acq_channel: Hashable = Parameter(
        initial_value=0,
    )
    """Acquisition channel of to this device element."""

    acq_delay: float = Parameter(
        initial_value=0.0,
        unit="s",
        # in principle the values should be a few 100 ns but the validator is here
        # only to protect against silly typos that lead to out of memory errors.
        vals=Numbers(min_value=0, max_value=100e-6),
    )
    """Delay between the start of the readout pulse and the start of
    the acquisition. Note that some hardware backends do not support
    starting a pulse and the acquisition in the same clock cycle making 0
    delay an invalid value."""

    integration_time: float = Parameter(
        initial_value=1e-6,
        unit="s",
        # in principle the values should be a few us but the validator is here
        # only to protect against silly typos that lead to out of memory errors.
        vals=Numbers(min_value=0, max_value=100e-6),
    )
    """Integration time for the readout acquisition."""

    reset_clock_phase: bool = Parameter(
        initial_value=True,
    )
    """The phase of the measurement's NCO clock will be reset by the control hardware
    at the start of each measurement if ``reset_clock_phase=True``."""

    acq_weights_a: NDArray | None = Parameter(
        default_factory=lambda: np.array([], dtype=np.float64),
    )
    """The weights for the I path. Used when specifying the
    ``"NumericalSeparatedWeightedIntegration"`` or the
    ``"NumericalWeightedIntegration"`` acquisition protocol."""

    acq_weights_b: NDArray | None = Parameter(
        default_factory=lambda: np.array([], dtype=np.float64),
    )
    """The weights for the Q path. Used when specifying the
    ``"NumericalSeparatedWeightedIntegration"`` or the
    ``"NumericalWeightedIntegration"`` acquisition protocol."""

    acq_weights_sampling_rate: float = Parameter(
        initial_value=1e9,
        unit="Hz",
        vals=Numbers(min_value=1, max_value=10e9),
    )
    """The sample rate of the weights arrays, in Hertz. Used when specifying the
    ``"NumericalSeparatedWeightedIntegration"`` or the
    ``"NumericalWeightedIntegration"`` acquisition protocol."""

    acq_weight_type: Literal["SSB", "Numerical"] = Parameter(
        initial_value="SSB",
    )

    acq_rotation: float = Parameter(
        initial_value=0.0,
    )
    """The phase rotation in degrees required to perform thresholded acquisition.
    Note that rotation is performed before the threshold. For more details see
    :class:`~qblox_scheduler.operations.acquisition_library.ThresholdedAcquisition`."""

    acq_threshold: float = Parameter(
        initial_value=0.0,
    )
    """The threshold value against which the rotated and integrated result
    is compared against. For more details see
    :class:`~qblox_scheduler.operations.acquisition_library.ThresholdedAcquisition`."""

    num_points: int = Parameter(
        initial_value=1,
        vals=Numbers(min_value=1),
    )
    """Number of data points to be acquired during the measurement.

    This parameter defines how many discrete data points will be collected
    in the course of a single measurement sequence. """

    reference_magnitude: ReferenceMagnitude | None = None


class ReferenceMagnitude(SchedulerSubmodule):
    """
    Submodule which describes an amplitude / power reference level.

    The reference level is with respect to which pulse amplitudes are defined.
    This can be specified in units of "V", "dBm" or "A".

    Only one unit parameter may have a defined value at a time. If we call the
    set method for any given unit parameter, all other unit parameters will be
    automatically set to nan.
    """

    dBm: float = Parameter(
        initial_value=math.nan,
        unit="dBm",
        vals=Numbers(allow_nan=True),
    )
    V: float = Parameter(
        initial_value=math.nan,
        unit="V",
        vals=Numbers(allow_nan=True),
    )
    A: float = Parameter(
        initial_value=math.nan,
        unit="A",
        vals=Numbers(allow_nan=True),
    )

    unit_params: ClassVar[frozenset[str]] = frozenset({"dBm", "V", "A"})

    def __setattr__(self, name: str, value: Any) -> None:  # noqa: ANN401
        """Ensure only one unit parameter is defined."""
        if name in self.unit_params and not math.isnan(value):
            super().__setattr__(name, value)
            for param in self.unit_params - {name}:
                super().__setattr__(param, math.nan)
            return

        super().__setattr__(name, value)

    def get_val_unit(self) -> tuple[float, str]:
        """
        Get the value of the amplitude reference and its unit, if one is defined.

        If a value is defined for more than one unit, raise an exception.

        Returns
        -------
        value
            The value of the amplitude reference
        unit
            The unit in which this value is specified

        """
        value_and_unit = math.nan, ""
        for param_name, param_value in self:
            if param_name in ("name", "parent"):
                continue  # TODO: Fix once these don't have a name.
            if isinstance(param_value, float) and not math.isnan(param_value):
                if math.isnan(value_and_unit[0]):
                    unit = type(self).get_unit(param_name) or ""
                    value_and_unit = param_value, unit
                else:
                    raise ValueError(
                        "ReferenceMagnitude values defined for multiple units. Only "
                        "one unit may be defined at a time."
                    )
        return value_and_unit


class BasicTransmonElement(DeviceElement):
    """
    A device element representing a single fixed-frequency transmon qubit.

    The qubit is coupled to a readout resonator.


    .. admonition:: Examples

        Qubit parameters can be set through submodule attributes

        .. jupyter-execute::

            from qblox_scheduler import BasicTransmonElement

            device_element = BasicTransmonElement("q3")

            device_element.rxy.amp180 = 0.1
            device_element.measure.pulse_amp = 0.25
            device_element.measure.pulse_duration = 300e-9
            device_element.measure.acq_delay = 430e-9
            device_element.measure.integration_time = 1e-6
            ...

    Parameters
    ----------
    name
        The name of the transmon element.
    kwargs
        Can be used to pass submodule initialization data by using submodule name
        as keyword and as argument a dictionary containing the submodule parameter
        names and their value.

    """

    element_type: Literal["BasicTransmonElement"] = "BasicTransmonElement"  # type: ignore[reportIncompatibleVariableOverride]

    reset: IdlingReset
    rxy: RxyDRAG
    measure: DispersiveMeasurement
    pulse_compensation: PulseCompensationModule
    ports: Ports
    clock_freqs: ClocksFrequencies

    def _generate_config(self) -> dict[str, dict[str, OperationCompilationConfig]]:
        """
        Generate part of the device configuration specific to a single qubit.

        This method is intended to be used when this object is part of a
        device object containing multiple elements.
        """
        device_element_config = {
            self.name: {
                "reset": OperationCompilationConfig(
                    factory_func=pulse_library.IdlePulse,
                    factory_kwargs={
                        "duration": self.reset.duration,
                    },
                ),
                # example of a pulse with a parametrized mapping, using a factory
                "Rxy": OperationCompilationConfig(
                    factory_func=pulse_factories.rxy_drag_pulse,
                    factory_kwargs={
                        "amp180": self.rxy.amp180,
                        "beta": self.rxy.beta,
                        "port": self.ports.microwave,
                        "clock": f"{self.name}.01",
                        "duration": self.rxy.duration,
                        "reference_magnitude": pulse_library.ReferenceMagnitude.from_parameter(
                            self.rxy.reference_magnitude
                        ),
                    },
                    gate_info_factory_kwargs=[
                        "theta",
                        "phi",
                    ],  # the keys from the gate info to pass to the factory function
                ),
                "Rz": OperationCompilationConfig(
                    factory_func=pulse_factories.phase_shift,
                    factory_kwargs={
                        "clock": f"{self.name}.01",
                    },
                    gate_info_factory_kwargs=[
                        "theta",
                    ],  # the keys from the gate info to pass to the factory function
                ),
                "H": OperationCompilationConfig(
                    factory_func=composite_factories.hadamard_as_y90z,
                    factory_kwargs={
                        "qubit": self.name,
                    },
                ),
                "pulse_compensation": OperationCompilationConfig(
                    factory_func=None,
                    factory_kwargs={
                        "port": self.ports.microwave,
                        "clock": f"{self.name}.01",
                        "max_compensation_amp": self.pulse_compensation.max_compensation_amp,
                        "time_grid": self.pulse_compensation.time_grid,
                        "sampling_rate": self.pulse_compensation.sampling_rate,
                    },
                ),
                # the measurement also has a parametrized mapping, and uses a
                # factory function.
                "measure": OperationCompilationConfig(
                    factory_func=measurement_factories.dispersive_measurement_transmon,
                    factory_kwargs={
                        "port": self.ports.readout,
                        "clock": f"{self.name}.ro",
                        "pulse_type": self.measure.pulse_type,
                        "pulse_amp": self.measure.pulse_amp,
                        "pulse_duration": self.measure.pulse_duration,
                        "acq_delay": self.measure.acq_delay,
                        "acq_duration": self.measure.integration_time,
                        "acq_channel": self.measure.acq_channel,
                        "acq_protocol_default": "SSBIntegrationComplex",
                        "reset_clock_phase": self.measure.reset_clock_phase,
                        "reference_magnitude": pulse_library.ReferenceMagnitude.from_parameter(
                            self.measure.reference_magnitude
                        ),
                        "acq_weights_a": self.measure.acq_weights_a,
                        "acq_weights_b": self.measure.acq_weights_b,
                        "acq_weights_sampling_rate": self.measure.acq_weights_sampling_rate,
                        "acq_rotation": self.measure.acq_rotation,
                        "acq_threshold": self.measure.acq_threshold,
                        "num_points": self.measure.num_points,
                        "freq": None,
                    },
                    gate_info_factory_kwargs=[
                        "acq_channel_override",
                        "coords",
                        "acq_index",
                        "bin_mode",
                        "acq_protocol",
                        "feedback_trigger_label",
                    ],
                ),
            }
        }
        return device_element_config

    def generate_device_config(self) -> DeviceCompilationConfig:
        """
        Generate a valid device config.

        The config will be used for the qblox-scheduler making use of the
        :func:`~.circuit_to_device.compile_circuit_to_device_with_config_validation` function.

        This enables the settings of this device element to be used in isolation.

        .. note:

            This config is only valid for single qubit experiments.
        """
        cfg_dict = {
            "elements": self._generate_config(),
            "clocks": {
                f"{self.name}.01": self.clock_freqs.f01,
                f"{self.name}.12": self.clock_freqs.f12,
                f"{self.name}.ro": self.clock_freqs.readout,
            },
            "edges": {},
        }
        dev_cfg = DeviceCompilationConfig.model_validate(cfg_dict)

        return dev_cfg
