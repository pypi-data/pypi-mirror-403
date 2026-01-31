pulse_compensation_library
==========================

.. py:module:: qblox_scheduler.operations.pulse_compensation_library 

.. autoapi-nested-parse::

   Pulse compensation operations for use with the qblox_scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.pulse_compensation_library.PulseCompensation




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.pulse_compensation_library.Port


.. py:data:: Port

   Port on the hardware; this is an alias to str.

.. py:class:: PulseCompensation(body: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.schedule.Schedule, qubits: str | collections.abc.Iterable[str] | None = None, max_compensation_amp: dict[Port, float] | None = None, time_grid: float | None = None, sampling_rate: float | None = None)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Apply pulse compensation to an operation or schedule.

   Inserts a pulse at the end of the operation or schedule set in ``body`` for each port.
   The compensation pulses are calculated so that the integral of all pulses
   (including the compensation pulses) are zero for each port.
   Moreover, the compensating pulses are square pulses, and start just after the last
   pulse on each port individually, and their maximum amplitude is the one
   specified in the ``max_compensation_amp``. Their duration is divisible by ``duration_grid``.
   The clock is assumed to be the baseband clock; any other clock is not allowed.

   :param body: Operation to be pulse-compensated
   :param qubits: For circuit-level operations, this is a list of device element names.
   :param max_compensation_amp: Dictionary for each port the maximum allowed amplitude for the compensation pulse.
   :param time_grid: Grid time of the duration of the compensation pulse.
   :param sampling_rate: Sampling rate for pulse integration calculation.


   .. py:property:: body
      :type: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule


      Body of a pulse compensation.


   .. py:property:: max_compensation_amp
      :type: dict[Port, float]


      For each port the maximum allowed amplitude for the compensation pulse.


   .. py:property:: time_grid
      :type: float


      Grid time of the duration of the compensation pulse.


   .. py:property:: sampling_rate
      :type: float


      Sampling rate for pulse integration calculation.


