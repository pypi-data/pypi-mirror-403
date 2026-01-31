# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""
Device elements for NV centers.

Currently only for the electronic qubit,
but could be extended for other qubits (eg. carbon qubit).
"""

from __future__ import annotations

import math
from collections.abc import Hashable
from typing import Literal

from qblox_scheduler.backends.graph_compilation import (
    DeviceCompilationConfig,
    OperationCompilationConfig,
)
from qblox_scheduler.device_under_test.device_element import DeviceElement
from qblox_scheduler.device_under_test.transmon_element import (
    PulseCompensationModule,  # noqa: TC001
)
from qblox_scheduler.enums import TimeRef, TimeSource
from qblox_scheduler.operations import (
    measurement_factories,
    pulse_factories,
    pulse_library,
)
from qblox_scheduler.structure.model import Numbers, Parameter, SchedulerSubmodule
from qblox_scheduler.structure.types import (
    Amplitude,
    Delay,
    Duration,
    Frequency,
)


class Ports(SchedulerSubmodule):
    """Submodule containing the ports."""

    microwave: str = Parameter(
        label="Name of microwave port",
        initial_value="",
    )
    """Name of the element's microwave port."""

    optical_control: str = Parameter(
        label="Name of optical control port",
        initial_value="",
    )
    """Port to control the device element with optical pulses."""

    optical_readout: str = Parameter(
        label="Name of optical readout port",
        initial_value="",
    )
    """Port to readout photons from the device element."""

    def _fill_defaults(self) -> None:
        if self.parent:
            if not self.microwave:
                self.microwave = f"{self.parent.name}:mw"
            if not self.optical_control:
                self.optical_control = f"{self.parent.name}:optical_control"
            if not self.optical_readout:
                self.optical_readout = f"{self.parent.name}:optical_readout"


class ClockFrequencies(SchedulerSubmodule):
    """Submodule with clock frequencies specifying the transitions to address."""

    f01: Frequency = Parameter(
        label="Microwave frequency in resonance with transition between 0 and 1",
        unit="Hz",
        initial_value=math.nan,
    )
    """Microwave frequency to resonantly drive the electron spin state of a
    negatively charged diamond NV center from the 0-state to 1-state
    :cite:t:`DOHERTY20131`."""

    spec: Frequency = Parameter(
        label="Spectroscopy frequency",
        unit="Hz",
        initial_value=math.nan,
    )
    """Parameter that is swept for a spectroscopy measurement. It does not track
    properties of the device element."""

    ge0: Frequency = Parameter(
        label="f_{ge0}",
        unit="Hz",
        initial_value=math.nan,
    )
    """Transition frequency from the m_s=0 state to the E_x,y state."""

    ge1: Frequency = Parameter(
        label="f_{ge1}",
        unit="Hz",
        initial_value=math.nan,
    )
    """Transition frequency from the m_s=+-1 state to any of the A_1, A_2, or
    E_1,2 states."""

    ionization: Frequency = Parameter(
        label="Frequency of ionization laser",
        unit="Hz",
        initial_value=math.nan,
    )
    """Frequency of the green ionization laser for manipulation of the NVs charge state."""


class SpectroscopyOperationNV(SchedulerSubmodule):
    """
    Convert the SpectroscopyOperation into a hermite, square, or gaussian microwave pulse.

    This class contains parameters with a certain amplitude and duration for
    spin-state manipulation.

    The modulation frequency of the pulse is determined by the clock ``spec`` in
    :class:`~.ClockFrequencies`.
    """

    amplitude: Amplitude = Parameter(
        label="Amplitude of spectroscopy pulse",
        initial_value=math.nan,
    )
    """Amplitude of spectroscopy pulse."""

    duration: Duration = Parameter(
        label="Duration of spectroscopy pulse",
        initial_value=8e-6,
        unit="s",
    )
    """Duration of the MW pulse."""

    pulse_shape: Literal["SquarePulse", "SkewedHermitePulse", "GaussPulse"] = Parameter(
        label="Shape of the pulse",
        initial_value="SquarePulse",
    )
    """Shape of the MW pulse."""


class ResetSpinpump(SchedulerSubmodule):
    r"""
    Submodule containing parameters to run the spinpump laser with a square pulse.

    This should reset the NV to the :math:`|0\rangle` state.
    """

    amplitude: Amplitude = Parameter(
        initial_value=math.nan,
    )
    """Amplitude of reset pulse."""

    duration: Duration = Parameter(
        initial_value=50e-6,
        unit="s",
    )
    """Duration of reset pulse."""


class Measure(SchedulerSubmodule):
    r"""
    Submodule containing parameters to read out the spin state of the NV center.

    Excitation with a readout laser from the :math:`|0\rangle` to an excited state.
    Acquisition of photons when decaying back into the :math:`|0\rangle` state.
    """

    pulse_amplitude: Amplitude = Parameter(
        initial_value=math.nan,
    )
    """Amplitude of readout pulse."""

    pulse_duration: Duration = Parameter(
        initial_value=20e-6,
        unit="s",
    )
    """Readout pulse duration."""

    acq_duration: Duration = Parameter(
        initial_value=50e-6,
        unit="s",
    )
    """Duration of the acquisition."""

    acq_delay: Delay = Parameter(
        initial_value=0.0,
        unit="s",
    )
    """Delay between the start of the readout pulse and the start of the acquisition."""

    acq_channel: Hashable = Parameter(
        initial_value=0,
    )
    """Acquisition channel of this device element."""

    # Optional timetag-related parameters.

    time_source: TimeSource = Parameter(
        initial_value=TimeSource.FIRST,
    )
    """
    Optional time source, in case the
    :class:`~qblox_scheduler.operations.acquisition_library.Timetag` acquisition
    protocols are used. Please see that protocol for more information.
    """

    time_ref: TimeRef = Parameter(
        initial_value=TimeRef.START,
    )
    """
    Optional time reference, in case
    :class:`~qblox_scheduler.operations.acquisition_library.Timetag` or
    :class:`~qblox_scheduler.operations.acquisition_library.TimetagTrace`
    acquisition protocols are used. Please see those protocols for more information.
    """


class ChargeReset(SchedulerSubmodule):
    """
    Submodule containing parameters to run an ionization laser square pulse to reset the NV.

    After resetting, the qubit should be in its negatively charged state.
    """

    amplitude: Amplitude = Parameter(
        initial_value=math.nan,
    )
    """Amplitude of charge reset pulse."""

    duration: Duration = Parameter(
        initial_value=20e-6,
        unit="s",
    )
    """Duration of the charge reset pulse."""


class CRCount(SchedulerSubmodule):
    """
    Submodule containing parameters to run the ionization laser and the spin pump laser.

    This uses a photon count to perform a charge and resonance count.
    """

    readout_pulse_amplitude: Amplitude = Parameter(
        initial_value=math.nan,
    )
    """Amplitude of readout pulse."""

    spinpump_pulse_amplitude: Amplitude = Parameter(
        initial_value=math.nan,
    )
    """Amplitude of spin-pump pulse."""

    readout_pulse_duration: Duration = Parameter(
        initial_value=20e-6,
        unit="s",
    )
    """Readout pulse duration."""

    spinpump_pulse_duration: Duration = Parameter(
        initial_value=20e-6,
        unit="s",
    )
    """Spin-pump pulse duration."""

    acq_duration: Duration = Parameter(
        initial_value=50e-6,
        unit="s",
    )
    """Duration of the acquisition."""

    acq_delay: Delay = Parameter(
        initial_value=0.0,
        unit="s",
    )
    """Delay between the start of the readout pulse and the start of the acquisition."""

    acq_channel: Hashable = Parameter(
        initial_value=0,
    )
    """Default acquisition channel of this device element."""


class RxyNV(SchedulerSubmodule):
    """
    Submodule containing parameters to perform an Rxy operation
    using a Hermite or Gaussian pulse.
    """

    amp180: Amplitude = Parameter(
        initial_value=math.nan,
    )
    r"""Amplitude of :math:`\pi` pulse."""

    skewness: float = Parameter(
        initial_value=0.0,
        vals=Numbers(min_value=-1, max_value=1),
    )
    """First-order amplitude to the Hermite pulse envelope."""

    duration: Duration = Parameter(
        initial_value=20e-9,
        unit="s",
    )
    """Duration of the pi pulse."""

    pulse_shape: Literal["SkewedHermitePulse", "GaussPulse"] = Parameter(
        label="Shape of the pulse",
        initial_value="SkewedHermitePulse",
    )
    """Shape of the pi pulse."""


class BasicElectronicNVElement(DeviceElement):
    """
    A device element representing an electronic qubit in an NV center.

    The submodules contain the necessary device element parameters to translate higher-level
    operations into pulses. Please see the documentation of these classes.

    .. admonition:: Examples

        Qubit parameters can be set through submodule attributes

        .. jupyter-execute::

            from qblox_scheduler import BasicElectronicNVElement

            device_element = BasicElectronicNVElement("q2")

            device_element.rxy.amp180 = 0.1
            device_element.measure.pulse_amplitude = 0.25
            device_element.measure.pulse_duration = 300e-9
            device_element.measure.acq_delay = 430e-9
            device_element.measure.acq_duration = 1e-6
            ...

    """

    element_type: Literal["BasicElectronicNVElement"] = "BasicElectronicNVElement"  # type: ignore[reportIncompatibleVariableOverride]

    spectroscopy_operation: SpectroscopyOperationNV
    ports: Ports
    clock_freqs: ClockFrequencies
    reset: ResetSpinpump
    charge_reset: ChargeReset
    measure: Measure
    pulse_compensation: PulseCompensationModule
    cr_count: CRCount
    rxy: RxyNV

    def _generate_config(self) -> dict[str, dict[str, OperationCompilationConfig]]:
        """
        Generate part of the device configuration specific to a single qubit.

        This method is intended to be used when this object is part of a
        device object containing multiple elements.
        """
        device_element_config = {
            self.name: {
                "spectroscopy_operation": OperationCompilationConfig(
                    factory_func=pulse_factories.nv_spec_pulse_mw,
                    factory_kwargs={
                        "duration": self.spectroscopy_operation.duration,
                        "amplitude": self.spectroscopy_operation.amplitude,
                        "port": self.ports.microwave,
                        "clock": f"{self.name}.spec",
                        "pulse_shape": self.spectroscopy_operation.pulse_shape,
                    },
                ),
                "reset": OperationCompilationConfig(
                    factory_func=pulse_library.SquarePulse,
                    factory_kwargs={
                        "duration": self.reset.duration,
                        "amp": self.reset.amplitude,
                        "port": self.ports.optical_control,
                        "clock": f"{self.name}.ge1",
                    },
                ),
                "charge_reset": OperationCompilationConfig(
                    factory_func=pulse_library.SquarePulse,
                    factory_kwargs={
                        "duration": self.charge_reset.duration,
                        "amp": self.charge_reset.amplitude,
                        "port": self.ports.optical_control,
                        "clock": f"{self.name}.ionization",
                    },
                ),
                "measure": OperationCompilationConfig(
                    factory_func=measurement_factories.optical_measurement,
                    factory_kwargs={
                        "pulse_amplitudes": [self.measure.pulse_amplitude],
                        "pulse_durations": [self.measure.pulse_duration],
                        "pulse_ports": [self.ports.optical_control],
                        "pulse_clocks": [f"{self.name}.ge0"],
                        "acq_duration": self.measure.acq_duration,
                        "acq_delay": self.measure.acq_delay,
                        "acq_channel": self.measure.acq_channel,
                        "acq_port": self.ports.optical_readout,
                        "acq_clock": f"{self.name}.ge0",
                        "acq_time_source": self.measure.time_source,
                        "acq_time_ref": self.measure.time_ref,
                        "pulse_type": "SquarePulse",
                        "acq_protocol_default": "TriggerCount",
                    },
                    gate_info_factory_kwargs=[
                        "acq_channel_override",
                        "coords",
                        "acq_index",
                        "bin_mode",
                        "acq_protocol",
                    ],
                ),
                "pulse_compensation": OperationCompilationConfig(
                    factory_func=None,
                    factory_kwargs={
                        "port": self.ports.microwave,
                        "clock": f"{self.name}.f_larmor",
                        "max_compensation_amp": self.pulse_compensation.max_compensation_amp,
                        "time_grid": self.pulse_compensation.time_grid,
                        "sampling_rate": self.pulse_compensation.sampling_rate,
                    },
                ),
                "cr_count": OperationCompilationConfig(
                    factory_func=measurement_factories.optical_measurement,
                    factory_kwargs={
                        "pulse_amplitudes": [
                            self.cr_count.readout_pulse_amplitude,
                            self.cr_count.spinpump_pulse_amplitude,
                        ],
                        "pulse_durations": [
                            self.cr_count.readout_pulse_duration,
                            self.cr_count.spinpump_pulse_duration,
                        ],
                        "pulse_ports": [
                            self.ports.optical_control,
                            self.ports.optical_control,
                        ],
                        "pulse_clocks": [
                            f"{self.name}.ge0",
                            f"{self.name}.ge1",
                        ],
                        "acq_duration": self.cr_count.acq_duration,
                        "acq_delay": self.cr_count.acq_delay,
                        "acq_channel": self.cr_count.acq_channel,
                        "acq_port": self.ports.optical_readout,
                        "acq_clock": f"{self.name}.ge0",
                        "pulse_type": "SquarePulse",
                        "acq_protocol_default": "TriggerCount",
                    },
                    gate_info_factory_kwargs=[
                        "acq_channel_override",
                        "coords",
                        "acq_index",
                        "bin_mode",
                        "acq_protocol",
                    ],
                ),
                "Rxy": OperationCompilationConfig(
                    factory_func=pulse_factories.rxy_pulse,
                    factory_kwargs={
                        "amp180": self.rxy.amp180,
                        "skewness": self.rxy.skewness,
                        "port": self.ports.microwave,
                        "clock": f"{self.name}.spec",
                        "duration": self.rxy.duration,
                        "pulse_shape": self.rxy.pulse_shape,
                    },
                    gate_info_factory_kwargs=[
                        "theta",
                        "phi",
                    ],
                ),
            }
        }
        return device_element_config

    def generate_device_config(self) -> DeviceCompilationConfig:
        """
        Generate a valid device config for the qblox-scheduler.

        This makes use of the
        :func:`~.circuit_to_device.compile_circuit_to_device_with_config_validation` function.

        This enables the settings of this qubit to be used in isolation.

        .. note:

            This config is only valid for single qubit experiments.
        """
        cfg_dict = {
            "elements": self._generate_config(),
            "clocks": {
                f"{self.name}.f01": self.clock_freqs.f01,
                f"{self.name}.spec": self.clock_freqs.spec,
                f"{self.name}.ge0": self.clock_freqs.ge0,
                f"{self.name}.ge1": self.clock_freqs.ge1,
                f"{self.name}.ionization": self.clock_freqs.ionization,
            },
            "edges": {},
        }
        dev_cfg = DeviceCompilationConfig.model_validate(cfg_dict)

        return dev_cfg
