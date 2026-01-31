spin_library
============

.. py:module:: qblox_scheduler.operations.spin_library 

.. autoapi-nested-parse::

   Spin qubit specific operations for use with the qblox_scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.spin_library.SpinInit




.. py:class:: SpinInit(qC: str, qT: str, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Initialize a spin qubit system.

   :param qC: The control device element.
   :param qT: The target device element
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


