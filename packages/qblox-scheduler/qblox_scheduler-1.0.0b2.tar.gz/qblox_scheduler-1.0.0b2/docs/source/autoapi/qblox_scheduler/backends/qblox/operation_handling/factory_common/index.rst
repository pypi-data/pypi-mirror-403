factory_common
==============

.. py:module:: qblox_scheduler.backends.qblox.operation_handling.factory_common 

.. autoapi-nested-parse::

   Functions for producing common operation handling strategies.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.operation_handling.factory_common.try_get_pulse_strategy_common



.. py:function:: try_get_pulse_strategy_common(operation_info: qblox_scheduler.backends.types.qblox.OpInfo) -> qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy | None

   Handles the logic for determining the correct pulse type.

   Returns ``None`` if no matching strategy class is found.


