bin_mode_compat
===============

.. py:module:: qblox_scheduler.backends.qblox.operation_handling.bin_mode_compat 

.. autoapi-nested-parse::

   Functionality to determine if the bin mode is compatible with the acquisition protocol.



Module Contents
---------------

.. py:data:: QRM_COMPATIBLE_BIN_MODES

.. py:data:: QTM_COMPATIBLE_BIN_MODES

.. py:exception:: IncompatibleBinModeError(module_type: str, protocol: str, bin_mode: qblox_scheduler.enums.BinMode, operation_info: qblox_scheduler.backends.types.qblox.OpInfo | None = None)

   Bases: :py:obj:`Exception`


   Compiler exception to be raised when a bin mode is incompatible with the acquisition protocol
   for the module type.


