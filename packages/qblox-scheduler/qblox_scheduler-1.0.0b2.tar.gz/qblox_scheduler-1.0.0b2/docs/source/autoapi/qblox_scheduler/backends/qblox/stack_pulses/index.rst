stack_pulses
============

.. py:module:: qblox_scheduler.backends.qblox.stack_pulses 

.. autoapi-nested-parse::

   Pulse stacking algorithm for Qblox backend.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.stack_pulses.PulseInterval
   qblox_scheduler.backends.qblox.stack_pulses.PulseParameters
   qblox_scheduler.backends.qblox.stack_pulses.PortClock



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.stack_pulses.stack_pulses
   qblox_scheduler.backends.qblox.stack_pulses._construct_pulses_by_port_clock
   qblox_scheduler.backends.qblox.stack_pulses._construct_pulses_by_interval
   qblox_scheduler.backends.qblox.stack_pulses._stack_pulses_by_interval
   qblox_scheduler.backends.qblox.stack_pulses._stack_arbitrary_pulses
   qblox_scheduler.backends.qblox.stack_pulses._stack_square_pulses
   qblox_scheduler.backends.qblox.stack_pulses._create_schedulable



.. py:class:: PulseInterval

   Represents an interval of (possibly) overlapping pulses.


   .. py:attribute:: start_time
      :type:  float


   .. py:attribute:: end_time
      :type:  float


   .. py:attribute:: pulse_keys
      :type:  set[str]


.. py:class:: PulseParameters

   Represents information about a specific pulse. Used for calculating intervals.


   .. py:attribute:: time
      :type:  float


   .. py:attribute:: is_end
      :type:  bool


   .. py:attribute:: schedulable_key
      :type:  str


.. py:class:: PortClock

   Bases: :py:obj:`tuple`


   .. py:attribute:: port


   .. py:attribute:: clock


.. py:function:: stack_pulses(schedule: qblox_scheduler.schedules.TimeableSchedule, config) -> qblox_scheduler.schedules.TimeableSchedule

   Processes a given schedule by identifying and stacking overlapping pulses.
   The function first defines intervals of overlapping pulses and then
   stacks the pulses within these intervals.

   :param schedule: The schedule containing the pulses to stack.

   :returns: :
                 The schedule with stacked pulses.



.. py:function:: _construct_pulses_by_port_clock(schedule: qblox_scheduler.schedules.TimeableSchedule) -> collections.defaultdict[str, list[PulseParameters]]

   Construct a dictionary of pulses by port and clock.


.. py:function:: _construct_pulses_by_interval(sorted_pulses: list[PulseParameters]) -> list[PulseInterval]

   Constructs a list of `PulseInterval` objects representing time intervals and active pulses.

   Given a sorted list of `PulseParameters` objects, this function identifies distinct intervals
   where pulses are active. Each `PulseInterval` records the start time, end time, and the set of
   active pulses during that interval. Pulses are added to or removed from the set based on their
   `is_end` attribute, indicating whether the pulse is starting or ending at a given time.


   Example Input/Output:
   ---------------------
       If the input list has pulses with start and end times as:
           [PulseParameters(time=1, schedulable_key='A', is_end=False),
            PulseParameters(time=3, schedulable_key='A', is_end=True),
            PulseParameters(time=2, schedulable_key='B', is_end=False)]
       The output will be:
           [PulseInterval(start_time=1, end_time=2, active_pulses={'A'}),
            PulseInterval(start_time=2, end_time=3, active_pulses={'A', 'B'})]

   See: https://softwareengineering.stackexchange.com/questions/363091/split-overlapping-ranges-into-all-unique-ranges for algo.



.. py:function:: _stack_pulses_by_interval(schedule: qblox_scheduler.schedules.TimeableSchedule, pulses_by_interval: list[PulseInterval]) -> qblox_scheduler.schedules.TimeableSchedule

.. py:function:: _stack_arbitrary_pulses(interval: PulseInterval, schedule: qblox_scheduler.schedules.TimeableSchedule, old_schedulable_keys: set[str]) -> None

.. py:function:: _stack_square_pulses(interval: PulseInterval, schedule: qblox_scheduler.schedules.TimeableSchedule, old_schedulable_keys: set[str]) -> None

.. py:function:: _create_schedulable(schedule: qblox_scheduler.schedules.TimeableSchedule, start_time: float, pulse: qblox_scheduler.operations.Operation | qblox_scheduler.schedules.TimeableSchedule | None) -> None

