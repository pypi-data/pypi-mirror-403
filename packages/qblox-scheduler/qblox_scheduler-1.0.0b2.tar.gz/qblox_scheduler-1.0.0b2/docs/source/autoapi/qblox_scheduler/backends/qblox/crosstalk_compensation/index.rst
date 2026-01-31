crosstalk_compensation
======================

.. py:module:: qblox_scheduler.backends.qblox.crosstalk_compensation 

.. autoapi-nested-parse::

   Module containing logic to handle crosstalk compensation.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.crosstalk_compensation.crosstalk_compensation
   qblox_scheduler.backends.qblox.crosstalk_compensation._get_unique_port_clocks
   qblox_scheduler.backends.qblox.crosstalk_compensation._calculate_compensation_matrix
   qblox_scheduler.backends.qblox.crosstalk_compensation._construct_crosstalk_matrix
   qblox_scheduler.backends.qblox.crosstalk_compensation.is_pulse
   qblox_scheduler.backends.qblox.crosstalk_compensation._apply_compensation_to_operation
   qblox_scheduler.backends.qblox.crosstalk_compensation._add_compensation_operation



.. py:function:: crosstalk_compensation(schedule: qblox_scheduler.schedules.TimeableSchedule, config: qblox_scheduler.backends.graph_compilation.CompilationConfig) -> qblox_scheduler.schedules.TimeableSchedule

   Apply crosstalk compensation to the given schedule based on the provided configuration.
   It adds compensation operations to port clocks affected by crosstalk.
   It also adjusts the amplitude of the original operation.

   :param schedule: The schedule to which cross-talk compensation will be applied.
   :param config: The configuration containing hardware options.

   :returns: TimeableSchedule:
                 The schedule with crosstalk compensation applied.



.. py:function:: _get_unique_port_clocks(crosstalk: dict[str, dict[str, float]]) -> list[str]

.. py:function:: _calculate_compensation_matrix(crosstalk: dict[str, dict[str, complex]], port_clock_list: list[str]) -> numpy.ndarray

.. py:function:: _construct_crosstalk_matrix(crosstalk: dict[str, dict[str, complex]], port_clock_list: list[str]) -> numpy.ndarray

.. py:function:: is_pulse(operation: qblox_scheduler.operations.Operation) -> bool

   Check if the operation is a pulse.

   :param operation: The operation to check.

   :returns: :
                 True if the operation is a pulse, False otherwise.



.. py:function:: _apply_compensation_to_operation(schedule: qblox_scheduler.schedules.TimeableSchedule, operation: qblox_scheduler.operations.Operation, schedulable: qblox_scheduler.schedules.Schedulable, port_clock_list: list[str], compensation_matrix: numpy.ndarray) -> None

.. py:function:: _add_compensation_operation(schedule: qblox_scheduler.schedules.TimeableSchedule, original_operation: qblox_scheduler.operations.Operation, original_schedulable: qblox_scheduler.schedules.Schedulable, target_port_clock: str, compensation_value: float, index: int) -> None

