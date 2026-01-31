trace_schedules
===============

.. py:module:: qblox_scheduler.schedules.trace_schedules 

.. autoapi-nested-parse::

   Contains various examples of trace schedules.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules.trace_schedules.trace_schedule
   qblox_scheduler.schedules.trace_schedules.trace_schedule_circuit_layer
   qblox_scheduler.schedules.trace_schedules.two_tone_trace_schedule



.. py:function:: trace_schedule(pulse_amp: float, pulse_duration: float, pulse_delay: float, frequency: float, acquisition_delay: float, integration_time: float, port: str, clock: str, init_duration: float = 0.0002, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule to perform raw trace acquisition.

   :param pulse_amp: The amplitude of the pulse in Volt.
   :param pulse_duration: The duration of the pulse in seconds.
   :param pulse_delay: The pulse delay in seconds.
   :param frequency: The frequency of the pulse and of the data acquisition in Hertz.
   :param acquisition_delay: The start of the data acquisition with respect to the start of the pulse in
                             seconds.
   :param integration_time: The time in seconds to integrate.
   :param port: The location on the device where the
                pulse should be applied.
   :param clock: The reference clock used to track the pulse frequency.
   :param init_duration: The relaxation time or dead time.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 The Raw Trace acquisition TimeableSchedule.



.. py:function:: trace_schedule_circuit_layer(qubit_name: str, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a simple schedule at circuit layer to perform raw trace acquisition.

   :param qubit_name: Name of a device element.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 The Raw Trace acquisition TimeableSchedule.



.. py:function:: two_tone_trace_schedule(qubit_pulse_amp: float, qubit_pulse_duration: float, qubit_pulse_frequency: float, qubit_pulse_port: str, qubit_pulse_clock: str, ro_pulse_amp: float, ro_pulse_duration: float, ro_pulse_delay: float, ro_pulse_port: str, ro_pulse_clock: str, ro_pulse_frequency: float, ro_acquisition_delay: float, ro_integration_time: float, init_duration: float = 0.0002, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing a two-tone raw trace acquisition.

   :param qubit_pulse_amp: The amplitude of the pulse in Volt.
   :param qubit_pulse_duration: The duration of the pulse in seconds.
   :param qubit_pulse_frequency: The pulse frequency in Hertz.
   :param qubit_pulse_port: The location on the device where the
                            qubit pulse should be applied.
   :param qubit_pulse_clock: The reference clock used to track the
                             pulse frequency.
   :param ro_pulse_amp: The amplitude of the readout pulse in Volt.
   :param ro_pulse_duration: The duration of the readout pulse in seconds.
   :param ro_pulse_delay: The time between the end of the pulse and the start
                          of the readout pulse.
   :param ro_pulse_port: The location on the device where the
                         readout pulse should be applied.
   :param ro_pulse_clock: The reference clock used to track the
                          readout pulse frequency.
   :param ro_pulse_frequency: The readout pulse frequency in Hertz.
   :param ro_acquisition_delay: The start of the data acquisition with respect to
                                the start of the pulse in seconds.
   :param ro_integration_time: The integration time of the data acquisition in seconds.
   :param init_duration: The relaxation time or dead time.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 The Two-tone Trace acquisition TimeableSchedule.



