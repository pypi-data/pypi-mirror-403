schedule
========

.. py:module:: qblox_scheduler.helpers.schedule 

.. autoapi-nested-parse::

   Schedule helper functions.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.helpers.schedule.get_pulse_uuid
   qblox_scheduler.helpers.schedule.get_acq_uuid
   qblox_scheduler.helpers.schedule._generate_acq_info_by_uuid
   qblox_scheduler.helpers.schedule.get_acq_info_by_uuid
   qblox_scheduler.helpers.schedule._is_acquisition_binned_average
   qblox_scheduler.helpers.schedule._is_acquisition_binned_append
   qblox_scheduler.helpers.schedule._is_acquisition_binned_average_append



.. py:function:: get_pulse_uuid(pulse_info: dict[str, Any], excludes: list[str] | None = None) -> int

   Return an unique identifier for a pulse.

   :param pulse_info: The pulse information dictionary.
   :param excludes: A list of keys to exclude.

   :returns: :
                 The uuid hash.



.. py:function:: get_acq_uuid(acq_info: dict[str, Any]) -> int

   Return an unique identifier for a acquisition protocol.

   :param acq_info: The acquisition information dictionary.

   :returns: :
                 The uuid hash.



.. py:function:: _generate_acq_info_by_uuid(operation: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableScheduleBase, acqid_acqinfo_dict: dict) -> None

.. py:function:: get_acq_info_by_uuid(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule) -> dict[int, dict[str, Any]]

   Return a lookup dictionary of unique identifiers of acquisition information.

   :param schedule: The schedule.


.. py:function:: _is_acquisition_binned_average(protocol: str, bin_mode: qblox_scheduler.enums.BinMode) -> bool

.. py:function:: _is_acquisition_binned_append(protocol: str, bin_mode: qblox_scheduler.enums.BinMode) -> bool

.. py:function:: _is_acquisition_binned_average_append(protocol: str, bin_mode: qblox_scheduler.enums.BinMode) -> bool

