composite_factories
===================

.. py:module:: qblox_scheduler.operations.composite_factories 

.. autoapi-nested-parse::

   A module containing factory functions for composite gates, which are replaced by schedules.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.composite_factories.hadamard_as_y90z
   qblox_scheduler.operations.composite_factories.cnot_as_h_cz_h



.. py:function:: hadamard_as_y90z(qubit: str) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a :class:`~.schedules.schedule.TimeableSchedule` Y90 * Z
   (equivalent to a Hadamard gate).

   :param qubit: Device element to which the Hadamard gate is applied.

   :returns: :
                 TimeableSchedule.



.. py:function:: cnot_as_h_cz_h(control_qubit: str, target_qubit: str) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a :class:`~.schedules.schedule.TimeableSchedule` for a CNOT gate using a CZ gate
   interleaved with Hadamard gates on the target qubit.

   :param control_qubit: Qubit acting as the control qubit.
   :param target_qubit: Qubit acting as the target qubit.

   :returns: TimeableSchedule
                 TimeableSchedule for the CNOT gate.



