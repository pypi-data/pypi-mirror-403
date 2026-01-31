conditional
===========

.. py:module:: qblox_scheduler.backends.qblox.conditional 

.. autoapi-nested-parse::

   Module containing logic to handle conditional playback.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.conditional.ConditionalManager
   qblox_scheduler.backends.qblox.conditional.FeedbackTriggerOperator
   qblox_scheduler.backends.qblox.conditional.FeedbackTriggerCondition




.. py:class:: ConditionalManager

   Class to manage a conditional control flow.


   .. py:attribute:: enable_conditional
      :type:  list
      :value: []


      Reference to initial `FEEDBACK_SET_COND` instruction.


   .. py:attribute:: num_real_time_instructions
      :type:  int
      :value: 0


      Number of real time instructions.


   .. py:attribute:: start_time
      :type:  int
      :value: 0


      Start time of conditional playback.


   .. py:attribute:: end_time
      :type:  int
      :value: 0


      End time of conditional playback.


   .. py:method:: update(operation: qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy) -> None

      Update the conditional manager.

      :param operation: Operation whose information is used to update the conditional manager.
      :type operation: IOperationStrategy
      :param time: Timing



   .. py:method:: reset() -> None

      Reset the conditional manager.



   .. py:property:: duration
      :type: int


      Duration of the conditional playback.


.. py:class:: FeedbackTriggerOperator(*args, **kwds)

   Bases: :py:obj:`enum.Enum`


   Enum for feedback trigger operations.


   .. py:attribute:: OR
      :value: 0


      Any selected counters exceed their thresholds.


   .. py:attribute:: NOR
      :value: 1


      No selected counters exceed their thresholds.


   .. py:attribute:: AND
      :value: 2


      All selected counters exceed their thresholds.


   .. py:attribute:: NAND
      :value: 3


      Any selected counters do not exceed their thresholds.


   .. py:attribute:: XOR
      :value: 4


      An odd number of selected counters exceed their thresholds.


   .. py:attribute:: XNOR
      :value: 5


      An even number of selected counters exceed their thresholds.


.. py:class:: FeedbackTriggerCondition

   Contains all information needed to enable conditional playback.


   .. py:attribute:: enable
      :type:  bool

      Enable/disable conditional playback.


   .. py:attribute:: operator
      :type:  FeedbackTriggerOperator

      Specifies the logic to apply on the triggers that are selected by the mask.
      See :class:`~FeedbackTriggerOperator` for more information.


   .. py:attribute:: addresses
      :type:  dataclasses.InitVar[collections.abc.Sequence[int]]

      Sequence of trigger addresses to condition on. Addresses may
      range from 1 to 15.


   .. py:attribute:: mask
      :type:  int

      Represents a bitwise mask in base-10. It dictates which trigger addresses
      will be monitored. For example, to track addresses 0 and 3, the mask would
      be 1001 in binary, which is 17 in base-10. This mask together with the
      operator will determine the conditional operation.


