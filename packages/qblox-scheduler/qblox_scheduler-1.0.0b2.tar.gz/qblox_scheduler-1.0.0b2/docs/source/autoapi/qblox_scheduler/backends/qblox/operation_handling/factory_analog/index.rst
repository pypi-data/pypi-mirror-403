factory_analog
==============

.. py:module:: qblox_scheduler.backends.qblox.operation_handling.factory_analog 

.. autoapi-nested-parse::

   Functions for producing operation handling strategies for QCM/QRM modules.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.operation_handling.factory_analog.get_operation_strategy
   qblox_scheduler.backends.qblox.operation_handling.factory_analog._get_acquisition_strategy
   qblox_scheduler.backends.qblox.operation_handling.factory_analog._get_pulse_strategy



.. py:function:: get_operation_strategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo, channel_name: str, module_options: qblox_scheduler.backends.types.qblox.ClusterModuleDescription) -> qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy

   Determine and instantiate the correct operation strategy object.

   :param operation_info: The operation for which we are building the strategy.
                          This object contains all the necessary information about the operation.
   :param channel_name: Specifies the channel identifier of the hardware config (e.g. `complex_output_0`).
   :param module_options: The module description the operation will run on

   :returns: :
                 The instantiated strategy object that implements the IOperationStrategy interface.
                 This could be a Q1ASMInjectionStrategy, an acquisition strategy, a pulse strategy,
                 or other specialized strategies depending on the operation type.

   :raises ValueError: If the operation cannot be compiled for the target hardware
       or if an unsupported operation type is encountered.


.. py:function:: _get_acquisition_strategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo) -> qblox_scheduler.backends.qblox.operation_handling.acquisitions.AcquisitionStrategyPartial

   Handles the logic for determining the correct acquisition type.


.. py:function:: _get_pulse_strategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo, channel_name: str, module_options: qblox_scheduler.backends.types.qblox.ClusterModuleDescription) -> qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy

   Handles the logic for determining the correct pulse type.


