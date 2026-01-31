measurement_factories
=====================

.. py:module:: qblox_scheduler.operations.measurement_factories 

.. autoapi-nested-parse::

   A module containing factory functions for measurements on the quantum-device layer.

   These factories are used to take a parametrized representation of on a operation
   and use that to create an instance of the operation itself.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.measurement_factories._dispersive_measurement
   qblox_scheduler.operations.measurement_factories.dispersive_measurement_transmon
   qblox_scheduler.operations.measurement_factories.dispersive_measurement_spin
   qblox_scheduler.operations.measurement_factories.optical_measurement



.. py:function:: _dispersive_measurement(pulse_amp: float, pulse_duration: float, port: str, gate_pulse_amp: float | None, gate_port: str | None, clock: str, acq_duration: float, acq_delay: float, acq_channel: collections.abc.Hashable, acq_channel_override: collections.abc.Hashable | None, coords: dict | None, acq_index: int | None, acq_protocol: str | None, pulse_type: Literal['SquarePulse'], bin_mode: qblox_scheduler.enums.BinMode | None, acq_protocol_default: str, reset_clock_phase: bool, reference_magnitude: qblox_scheduler.operations.pulse_library.ReferenceMagnitude | None, acq_weights_a: list[complex] | numpy.ndarray | None, acq_weights_b: list[complex] | numpy.ndarray | None, acq_weights_sampling_rate: float | None, feedback_trigger_label: str | None, acq_rotation: float | None, acq_threshold: float | None, num_points: float | None, freq: float | None) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generator function for a standard dispersive measurement.

   A dispersive measurement (typically) consists of a pulse being applied to the device
   followed by an acquisition protocol to interpret the signal coming back from the
   device.

   :param pulse_amp: The amplitude of the pulse.
   :param pulse_duration: The duration of the pulse.
   :param port: The port for the pulse.
   :param gate_pulse_amp: Optional amplitude for the gate pulse.
   :param gate_port: Optional port for the gate pulse.
   :param clock: The clock for the pulse.
   :param acq_duration: The duration of the acquisition.
   :param acq_delay: The delay before the acquisition starts.
   :param acq_channel: The acquisition channel.
   :param acq_channel_override: An optional override for the acquisition channel.
   :param coords: Coords.
   :param acq_index: The index of the acquisition.
   :param acq_protocol: The acquisition protocol to use.
   :param pulse_type: The type of pulse to use. Default is "SquarePulse".
   :param bin_mode: The binning mode for the acquisition. Default is BinMode.AVERAGE.
   :param acq_protocol_default: The default acquisition protocol to use. Default is "SSBIntegrationComplex".
   :param reset_clock_phase: Whether to reset the clock phase. Default is True.
   :param reference_magnitude: An optional reference magnitude.
   :param acq_weights_a: Optional acquisition weights A.
   :param acq_weights_b: Optional acquisition weights B.
   :param acq_weights_sampling_rate: The sampling rate for the acquisition weights.
   :param feedback_trigger_label: Optional feedback trigger label.
   :param acq_rotation: Optional acquisition rotation.
   :param acq_threshold: Optional acquisition threshold.
   :param num_points: Optional number of points for the acquisition.
   :param freq: Optional frequency to override clock for this operation.

   :returns: :
                 The resulting schedule for the dispersive measurement.



.. py:function:: dispersive_measurement_transmon(pulse_amp: float, pulse_duration: float, port: str, clock: str, acq_duration: float, acq_delay: float, acq_channel: collections.abc.Hashable, acq_channel_override: collections.abc.Hashable | None, coords: dict | None, acq_index: int | None, acq_protocol: str | None, pulse_type: Literal['SquarePulse'] = 'SquarePulse', bin_mode: qblox_scheduler.enums.BinMode | None = None, acq_protocol_default: str = 'SSBIntegrationComplex', reset_clock_phase: bool = True, reference_magnitude: qblox_scheduler.operations.pulse_library.ReferenceMagnitude | None = None, acq_weights_a: list[complex] | numpy.ndarray | None = None, acq_weights_b: list[complex] | numpy.ndarray | None = None, acq_weights_sampling_rate: float | None = None, feedback_trigger_label: str | None = None, acq_rotation: float | None = None, acq_threshold: float | None = None, num_points: float | None = None, freq: float | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Creates a dispersive measurement schedule for a transmon qubit.

   :param pulse_amp: The amplitude of the pulse.
   :param pulse_duration: The duration of the pulse.
   :param port: The port for the pulse.
   :param clock: The clock for the pulse.
   :param acq_duration: The duration of the acquisition.
   :param acq_delay: The delay before the acquisition starts.
   :param acq_channel: The acquisition channel.
   :param acq_channel_override: An optional override for the acquisition channel.
   :param coords: Coords.
   :param acq_index: The index of the acquisition.
   :param acq_protocol: The acquisition protocol to use.
   :param pulse_type: The type of pulse to use. Default is "SquarePulse".
   :param bin_mode: The binning mode for the acquisition. Default is the protocol default.
   :param acq_protocol_default: The default acquisition protocol to use. Default is "SSBIntegrationComplex".
   :param reset_clock_phase: Whether to reset the clock phase. Default is True.
   :param reference_magnitude: An optional reference magnitude.
   :param acq_weights_a: Optional acquisition weights A.
   :param acq_weights_b: Optional acquisition weights B.
   :param acq_weights_sampling_rate: The sampling rate for the acquisition weights.
   :param feedback_trigger_label: Optional feedback trigger label.
   :param acq_rotation: Optional acquisition rotation.
   :param acq_threshold: Optional acquisition threshold.
   :param num_points: Optional number of points for the acquisition.
   :param freq: Optional frequency to override clock for this operation.

   :returns: :
                 The resulting schedule for the dispersive measurement.



.. py:function:: dispersive_measurement_spin(pulse_amp: float, pulse_duration: float, port: str, gate_pulse_amp: float | None, gate_port: str | None, clock: str, acq_duration: float, acq_delay: float, acq_channel: collections.abc.Hashable, acq_channel_override: collections.abc.Hashable | None, coords: dict | None, acq_index: int | None, acq_protocol: str | None, pulse_type: Literal['SquarePulse'] = 'SquarePulse', bin_mode: qblox_scheduler.enums.BinMode | None = None, acq_protocol_default: str = 'SSBIntegrationComplex', reset_clock_phase: bool = True, reference_magnitude: qblox_scheduler.operations.pulse_library.ReferenceMagnitude | None = None, acq_weights_a: list[complex] | numpy.ndarray | None = None, acq_weights_b: list[complex] | numpy.ndarray | None = None, acq_weights_sampling_rate: float | None = None, feedback_trigger_label: str | None = None, acq_rotation: float | None = None, acq_threshold: float | None = None, num_points: float | None = None, freq: float | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Creates a dispersive measurement schedule for a spin qubit.

   :param pulse_amp: The amplitude of the pulse.
   :param pulse_duration: The duration of the pulse.
   :param port: The port for the pulse.
   :param clock: The clock for the pulse.
   :param acq_duration: The duration of the acquisition.
   :param acq_delay: The delay before the acquisition starts.
   :param acq_channel: The acquisition channel.
   :param acq_channel_override: An optional override for the acquisition channel.
   :param coords: Coords.
   :param acq_index: The index of the acquisition.
   :param acq_protocol: The acquisition protocol to use.
   :param pulse_type: The type of pulse to use. Default is "SquarePulse".
   :param bin_mode: The binning mode for the acquisition. Default is the protocol default.
   :param acq_protocol_default: The default acquisition protocol to use. Default is "SSBIntegrationComplex".
   :param reset_clock_phase: Whether to reset the clock phase. Default is True.
   :param reference_magnitude: An optional reference magnitude.
   :param acq_weights_a: Optional acquisition weights A.
   :param acq_weights_b: Optional acquisition weights B.
   :param acq_weights_sampling_rate: The sampling rate for the acquisition weights.
   :param feedback_trigger_label: Optional feedback trigger label.
   :param acq_rotation: Optional acquisition rotation.
   :param acq_threshold: Optional acquisition threshold.
   :param num_points: Optional number of points for the acquisition.
   :param gate_pulse_amp: Optional amplitude for the gate pulse.
   :param gate_port: Optional port for the gate pulse.
   :param freq: Optional frequency to override clock for this operation.

   :returns: :
                 The resulting schedule for the dispersive measurement.



.. py:function:: optical_measurement(pulse_amplitudes: list[float], pulse_durations: list[float], pulse_ports: list[str], pulse_clocks: list[str], acq_duration: float, acq_delay: float, acq_port: str, acq_clock: str, acq_channel: collections.abc.Hashable, acq_channel_override: collections.abc.Hashable | None, coords: dict | None, acq_index: int | None, bin_mode: qblox_scheduler.enums.BinMode | None, acq_protocol: Literal['Trace', 'TriggerCount', 'Timetag', 'TimetagTrace'] | None, acq_protocol_default: Literal['Trace', 'TriggerCount'], pulse_type: Literal['SquarePulse'], acq_time_source: qblox_scheduler.enums.TimeSource | None = None, acq_time_ref: qblox_scheduler.enums.TimeRef | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generator function for an optical measurement with multiple excitation pulses.

   An optical measurement generates a square pulse in the optical range and uses
   either the Trace acquisition to return the output of a photon detector as a
   function of time or the TriggerCount acquisition to return the number of photons
   that are collected.

   All pulses can have different amplitudes, durations, ports and clocks. All pulses
   start simultaneously. The acquisition can have an ``acq_delay`` with respect to the
   pulses. A negative ``acq_delay`` causes the acquisition to be scheduled at time 0
   and the pulses at the positive time ``-acq_delay``.

   :param pulse_amplitudes: list of amplitudes of the corresponding pulses
   :param pulse_durations: list of durations of the corresponding pulses
   :param pulse_ports: Port names, where the corresponding pulses are applied
   :param pulse_clocks: Clock names of the corresponding pulses
   :param acq_duration: Duration of the acquisition
   :param acq_delay: Delay between the start of the readout pulse and the start of the acquisition:
                     acq_delay = t0_pulse - t0_acquisition.
   :param acq_port: Port name of the acquisition
   :param acq_clock: Clock name of the acquisition
   :param acq_channel: Default acquisition channel of the device element
   :param acq_channel_override: Acquisition channel of the operation
   :param coords: Coords.
   :param acq_index: Acquisition index as defined in the TimeableSchedule
   :param bin_mode: Describes what is done when data is written to a register that already
                    contains a value. Options are "append" which appends the result to the
                    list. "average" which stores the count value of the new result and the
                    old register value is not currently implemented. ``None`` internally
                    resolves to ``BinMode.APPEND``.
   :param acq_protocol: Acquisition protocol. "Trace" returns a time trace of the collected signal.
                        "TriggerCount" returns the number of times the trigger threshold is surpassed.
   :param acq_protocol_default: Acquisition protocol if ``acq_protocol`` is None
   :param pulse_type: Shape of the pulse to be generated
   :param acq_time_source: Selects the timetag data source for this acquisition type.
   :param acq_time_ref: Selects the time reference that the timetag is recorded in relation to.

   :returns: :
                 Operation with the generated pulses and acquisition

   :raises ValueError: If first four function arguments do not have the same length.
   :raises NotImplementedError: If an unknown ``pulse_type`` or ``acq_protocol`` are used.


