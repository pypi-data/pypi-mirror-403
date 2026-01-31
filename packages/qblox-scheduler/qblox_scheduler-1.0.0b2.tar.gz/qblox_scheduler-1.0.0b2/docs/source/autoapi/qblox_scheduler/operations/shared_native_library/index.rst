shared_native_library
=====================

.. py:module:: qblox_scheduler.operations.shared_native_library 

.. autoapi-nested-parse::

   Module containing shared native operations.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.shared_native_library.SpectroscopyOperation




.. py:class:: SpectroscopyOperation(qubit: str, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Spectroscopy operation to find energy between computational basis states.

   Spectroscopy operations can be supported by various qubit types, but not all of
   them. They are typically translated into a spectroscopy pulse by the quantum
   device. The frequency is taken from a clock of the device element.

   :param qubit: The target device element.


