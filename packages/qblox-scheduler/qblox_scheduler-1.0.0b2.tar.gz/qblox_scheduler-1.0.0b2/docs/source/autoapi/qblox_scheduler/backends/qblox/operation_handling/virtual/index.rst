virtual
=======

.. py:module:: qblox_scheduler.backends.qblox.operation_handling.virtual 

.. autoapi-nested-parse::

   Classes for handling operations that are neither pulses nor acquisitions.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.operation_handling.virtual.IdleStrategy
   qblox_scheduler.backends.qblox.operation_handling.virtual.NcoPhaseShiftStrategy
   qblox_scheduler.backends.qblox.operation_handling.virtual.NcoResetClockPhaseStrategy
   qblox_scheduler.backends.qblox.operation_handling.virtual.NcoSetClockFrequencyStrategy
   qblox_scheduler.backends.qblox.operation_handling.virtual.AwgOffsetStrategy
   qblox_scheduler.backends.qblox.operation_handling.virtual.ResetFeedbackTriggersStrategy
   qblox_scheduler.backends.qblox.operation_handling.virtual.UpdateParameterStrategy
   qblox_scheduler.backends.qblox.operation_handling.virtual.LoopStrategy
   qblox_scheduler.backends.qblox.operation_handling.virtual.ConditionalStrategy
   qblox_scheduler.backends.qblox.operation_handling.virtual.ControlFlowReturnStrategy
   qblox_scheduler.backends.qblox.operation_handling.virtual.TimestampStrategy




.. py:class:: IdleStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy`


   Defines the behavior for an operation that does not produce any output.

   :param operation_info: The operation info that corresponds to this operation.
   :type operation_info: qblox_scheduler.backends.types.qblox.OpInfo


   .. py:attribute:: _op_info


   .. py:property:: operation_info
      :type: qblox_scheduler.backends.types.qblox.OpInfo


      Property for retrieving the operation info.


   .. py:method:: generate_data(wf_dict: dict[str, Any]) -> None

      Returns None as no waveforms are generated in this strategy.



   .. py:method:: insert_qasm(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Add the assembly instructions for the Q1 sequence processor that corresponds to
      this operation.

      Not an abstractmethod, since it is allowed to use the IdleStrategy directly
      (e.g. for IdlePulses), but can be overridden in subclass to add some assembly
      instructions despite not outputting any data.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



.. py:class:: NcoPhaseShiftStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`IdleStrategy`


   Strategy for operation that does not produce any output, but rather applies a
   phase shift to the NCO. Implemented as ``set_ph_delta`` and an ``upd_param`` of 8 ns,
   leading to a total duration of 8 ns before the next command can be issued.


   .. py:method:: insert_qasm(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Inserts the instructions needed to shift the NCO phase by a specific amount.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



.. py:class:: NcoResetClockPhaseStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`IdleStrategy`


   Strategy for operation that does not produce any output, but rather resets
   the phase of the NCO.


   .. py:method:: insert_qasm(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Inserts the instructions needed to reset the NCO phase.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



.. py:class:: NcoSetClockFrequencyStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`IdleStrategy`


   Strategy for operation that does not produce any output, but rather sets
   the frequency of the NCO. Implemented as ``set_freq`` and an ``upd_param`` of 4 ns,
   leading to a total duration of 4 ns before the next command can be issued.


   .. py:method:: insert_qasm(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Inserts the instructions needed to set the NCO frequency.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



.. py:class:: AwgOffsetStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`IdleStrategy`


   Strategy for compiling a DC voltage offset instruction. The generated Q1ASM contains
   only the ``set_awg_offs`` instruction and no ``upd_param`` instruction.


   .. py:method:: insert_qasm(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Add the Q1ASM instruction for a DC voltage offset.

      :param qasm_program: The QASMProgram to add the assembly instructions to.
      :type qasm_program: QASMProgram



.. py:class:: ResetFeedbackTriggersStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`IdleStrategy`


   Strategy for resetting the count of feedback trigger addresses.


   .. py:method:: insert_qasm(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Add the assembly instructions for the Q1 sequence processor that corresponds to
      this pulse.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



.. py:class:: UpdateParameterStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`IdleStrategy`


   Strategy for compiling an "update parameters" real-time instruction.


   .. py:method:: insert_qasm(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Add the ``upd_param`` assembly instruction for the Q1 sequence processor.

      :param qasm_program: The QASMProgram to add the assembly instructions to.
      :type qasm_program: QASMProgram



.. py:class:: LoopStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`IdleStrategy`


   Strategy for compiling a "Loop" control flow instruction.

   Empty as it is used for isinstance.


.. py:class:: ConditionalStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo, trigger_condition: qblox_scheduler.backends.qblox.conditional.FeedbackTriggerCondition)

   Bases: :py:obj:`IdleStrategy`


   Strategy for compiling a "Conditional" control flow instruction.


   .. py:attribute:: trigger_condition


.. py:class:: ControlFlowReturnStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`IdleStrategy`


   Strategy for compiling "ControlFlowReturn" control flow instruction.

   Empty as it is used for isinstance.


.. py:class:: TimestampStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`IdleStrategy`


   Strategy for compiling
   :class:`~qblox_scheduler.operations.pulse_library.Timestamp`.


   .. py:method:: insert_qasm(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Inserts the instructions needed insert a time reference.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



