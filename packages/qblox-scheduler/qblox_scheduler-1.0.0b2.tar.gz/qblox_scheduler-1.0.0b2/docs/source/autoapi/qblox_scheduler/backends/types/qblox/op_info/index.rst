op_info
=======

.. py:module:: qblox_scheduler.backends.types.qblox.op_info 

.. autoapi-nested-parse::

   Python dataclasses for compilation to Qblox hardware.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.qblox.op_info.OpInfo




.. py:class:: OpInfo

   Bases: :py:obj:`dataclasses_json.DataClassJsonMixin`


   Data structure describing a pulse or acquisition and containing all the information
   required to play it.


   .. py:attribute:: name
      :type:  str

      Name of the operation that this pulse/acquisition is part of.


   .. py:attribute:: data
      :type:  dict

      The pulse/acquisition info taken from the ``data`` property of the
      pulse/acquisition in the schedule.


   .. py:attribute:: timing
      :type:  float

      The start time of this pulse/acquisition.
      Note that this is a combination of the start time "t_abs" of the schedule
      operation, and the t0 of the pulse/acquisition which specifies a time relative
      to "t_abs".


   .. py:property:: duration
      :type: float


      The duration of the pulse/acquisition.


   .. py:property:: is_acquisition
      :type: bool


      Returns ``True`` if this is an acquisition, ``False`` otherwise.


   .. py:property:: is_real_time_io_operation
      :type: bool


      Returns ``True`` if the operation is a non-idle pulse (i.e., it has a
      waveform), ``False`` otherwise.


   .. py:property:: is_offset_instruction
      :type: bool


      Returns ``True`` if the operation describes a DC offset operation,
      corresponding to the Q1ASM instruction ``set_awg_offset``.


   .. py:property:: is_parameter_instruction
      :type: bool


      Return ``True`` if the instruction is a parameter, like a voltage offset.

      From the Qblox documentation: "parameter operation instructions" are latched and
      only updated when the upd_param, play, acquire, acquire_weighed or acquire_ttl
      instructions are executed.

      Please refer to
      https://docs.qblox.com/en/main/cluster/q1_sequence_processor.html#q1-instructions
      for the full list of these instructions.


   .. py:property:: is_parameter_update
      :type: bool


      Return ``True`` if the operation is a parameter update, corresponding to the
      Q1ASM instruction ``upd_param``.


   .. py:property:: is_loop
      :type: bool


      Return ``True`` if the operation is a loop, corresponding to the Q1ASM
      instruction ``loop``.


   .. py:property:: is_control_flow_end
      :type: bool


      Return ``True`` if the operation is a control flow end.


   .. py:method:: substitute(substitutions: dict[qblox_scheduler.operations.expressions.Expression, qblox_scheduler.operations.expressions.Expression | int | float | complex]) -> OpInfo

      Substitute matching expressions in operand, possibly evaluating a result.



