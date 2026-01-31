q1asm_injection_strategy
========================

.. py:module:: qblox_scheduler.backends.qblox.operation_handling.q1asm_injection_strategy 

.. autoapi-nested-parse::

   Classes for handling operations that are neither pulses nor acquisitions.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.operation_handling.q1asm_injection_strategy.Q1ASMInjectionStrategy




.. py:class:: Q1ASMInjectionStrategy(operation_info: qblox_scheduler.operations.hardware_operations.inline_q1asm.Q1ASMOpInfo)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy`


   Strategy for compiling an "inline Q1ASM" instruction block.


   .. py:attribute:: _op_info


   .. py:property:: operation_info
      :type: qblox_scheduler.backends.types.qblox.OpInfo


      Property for retrieving the operation info.


   .. py:method:: generate_data(wf_dict: dict[str, Any]) -> None

      Generates the waveform data and adds them to the wf_dict
      (if not already present).
      This is either the awg data, or the acquisition weights.

      :param wf_dict: The dictionary to add the waveform to.
                      N.B. the dictionary is modified in function.



   .. py:method:: insert_qasm(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Add the inline Q1ASM program for the Q1 sequence processor.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



