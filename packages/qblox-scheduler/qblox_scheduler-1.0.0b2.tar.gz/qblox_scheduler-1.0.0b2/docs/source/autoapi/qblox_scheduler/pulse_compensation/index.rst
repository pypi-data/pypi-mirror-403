pulse_compensation
==================

.. py:module:: qblox_scheduler.pulse_compensation 

.. autoapi-nested-parse::

   Compiler for the qblox_scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.pulse_compensation.SumEnd
   qblox_scheduler.pulse_compensation.CompensationPulseParams



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.pulse_compensation._merge_sum_and_end
   qblox_scheduler.pulse_compensation._determine_sum_and_end_of_all_pulses
   qblox_scheduler.pulse_compensation._determine_compensation_pulse
   qblox_scheduler.pulse_compensation.process_compensation_pulses



.. py:class:: SumEnd

   Class to store the sum and end as floats.


   .. py:attribute:: sum
      :type:  float
      :value: 0.0



   .. py:attribute:: end
      :type:  float
      :value: 0.0



   .. py:method:: merge(other: SumEnd) -> SumEnd

      Merge two `SumEnd` objects together: `sum` are added, `end` are maxed.



.. py:function:: _merge_sum_and_end(pulses_sum_end_1: dict[qblox_scheduler.operations.pulse_compensation_library.Port, SumEnd], pulses_sum_end_2: dict[qblox_scheduler.operations.pulse_compensation_library.Port, SumEnd]) -> dict[qblox_scheduler.operations.pulse_compensation_library.Port, SumEnd]

.. py:function:: _determine_sum_and_end_of_all_pulses(operation: qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.operations.operation.Operation, sampling_rate: float, time_offset: float, ports: set[str], is_conditional: bool) -> dict[qblox_scheduler.operations.pulse_compensation_library.Port, SumEnd]

   Calculates the sum (or integral) of the amplitudes of all pulses in the operation,
   and the end time of the last pulse in the operation.
   The function assumes there is no operation which need to be pulse compensated inside.
   The function also assumes that the absolute timings are already calculated in the schedule.

   :param operation: The schedule or operation to calculate sum and end of pulses.
   :param sampling_rate: Sampling rate of the pulses.
   :param time_offset: Time offset for the operation with regards to the start of the whole schedule.
   :param ports: Set of ports for which we need to calculate the pulse compensations.
   :param is_conditional: Boolean variable to identify if a conditional operation is encountered during recursion.

   :returns: :
                 The sum and end time of all the pulses as a `SumEnd`.



.. py:class:: CompensationPulseParams

   Class to store start, duration and amp in floats.


   .. py:attribute:: start
      :type:  float


   .. py:attribute:: duration
      :type:  float


   .. py:attribute:: amp
      :type:  float


.. py:function:: _determine_compensation_pulse(operation: qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.operations.operation.Operation, max_compensation_amp: dict[qblox_scheduler.operations.pulse_compensation_library.Port, float], time_grid: float, sampling_rate: float) -> dict[qblox_scheduler.operations.pulse_compensation_library.Port, CompensationPulseParams]

   Calculates the timing and the amplitude of a compensation pulse for each port.
   The `duration` and `amp` are calculated, with the requirements, that
   if a compensation square pulse is inserted in the schedule at `start` with duration `duration`,
   and amplitude `amp`, then
   * the integral of all pulses in the operation would equal to 0,
   * the duration of the compensation pulse is divisible by `time_grid`,
   * the compensation pulse is the last pulse in the operation, and
   * the compensation pulse starts just after the previous pulse.
   The function assumes there is no operation which needs to be pulse compensated inside.
   The clock is assumed to be the baseband clock.

   :param operation: The original operation or schedule to compensate for.
   :param max_compensation_amp: The maximum amplitude of the compensation pulse.
   :param time_grid: Time grid the compensation pulse needs to be on.
   :param sampling_rate: Sampling rate of the pulses.

   :returns: :
                 The start, duration and amp of a compensation pulse
                 with the given requirements as a `CompensationPulseParams` for each port.



.. py:function:: process_compensation_pulses(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, config: qblox_scheduler.backends.graph_compilation.CompilationConfig | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule
                 process_compensation_pulses(schedule: qblox_scheduler.operations.operation.Operation, config: qblox_scheduler.backends.graph_compilation.CompilationConfig | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.operations.operation.Operation

   Replaces ``PulseCompensation`` with a subschedule with an additional compensation pulse.

   :param schedule: The schedule which contains potential ``PulseCompensation`` in it.
   :param config: Compilation config for
                  :class:`~qblox_scheduler.backends.graph_compilation.ScheduleCompiler`.

   :returns: :
                 The start, duration and amp of a compensation pulse
                 with the given requirements as a `CompensationPulseParams` for each port.



