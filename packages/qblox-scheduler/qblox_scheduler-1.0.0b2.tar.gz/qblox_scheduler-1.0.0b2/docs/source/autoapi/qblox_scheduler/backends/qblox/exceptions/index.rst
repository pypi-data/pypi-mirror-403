exceptions
==========

.. py:module:: qblox_scheduler.backends.qblox.exceptions 

.. autoapi-nested-parse::

   Exceptions used by Qblox backend.



Module Contents
---------------

.. py:exception:: InvalidQuantumDeviceConfigurationError

   Bases: :py:obj:`TypeError`


   Exception thrown if the quantum device configuration is invalid.


.. py:exception:: NcoOperationTimingError

   Bases: :py:obj:`ValueError`


   Exception thrown if there are timing errors for NCO operations.


.. py:exception:: FineDelayTimingError(error_type: Literal['within_op', 'between_op'], operation_info: qblox_scheduler.backends.types.qblox.OpInfo, fine_start_delay: int, fine_end_delay: int, operation_start_time: int, operation_duration: int, last_digital_pulse_end_ps: int)

   Bases: :py:obj:`ValueError`


   Exception thrown if there are timing errors for fine delays.

   Note that all units are in picoseconds.


