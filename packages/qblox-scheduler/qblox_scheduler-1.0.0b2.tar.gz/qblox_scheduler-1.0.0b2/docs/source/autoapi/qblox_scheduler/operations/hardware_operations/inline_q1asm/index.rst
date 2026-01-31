inline_q1asm
============

.. py:module:: qblox_scheduler.operations.hardware_operations.inline_q1asm 

.. autoapi-nested-parse::

   Qblox-specific operation which can be used to inject Q1ASM directly into a TimeableSchedule.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.hardware_operations.inline_q1asm.InlineQ1ASM
   qblox_scheduler.operations.hardware_operations.inline_q1asm.Q1ASMOpInfo




.. py:class:: InlineQ1ASM(program: str, duration: float, port: str, clock: str, *, waveforms: dict | None = None, safe_labels: bool = True)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Initialize an InlineQ1ASM operation.

   This method sets up an operation that contains inline Q1ASM code
    to be injected directly into a Schedule.

   All comments in the program will be prefixed with an '[inline]' prefix
   to help identify the inline assembly within the sequencer program.


   When using safe labels, then all labels included in the input program
   will get a prefix of 'inj<digits>_'.
   By default, safe labels are always used.
   Labels in comments will not be modified.

   :param program: The Q1ASM program to be injected.
   :param duration: The duration of the operation in seconds.
   :param port: The port on which the operation is to be executed.
   :param clock: The clock associated with the operation.
   :param waveforms: Dictionary containing waveform information, by default None.
   :param safe_labels: Flag to indicate if safe labels should be used, by default True.

   :returns: None

   .. rubric:: Notes

   .. warning::

       When using safe_labels=False then all labels in the sequencer program are accessible from
       inside the inline Q1ASM injection, and so can be jumped to or overwritten.  Disabling this
       feature is available for debugging and advanced compilation strategies only.


   .. py:attribute:: _name
      :value: 'InlineQ1ASM'



   .. py:attribute:: program


   .. py:attribute:: _duration


   .. py:attribute:: port


   .. py:attribute:: clock


   .. py:attribute:: waveforms


   .. py:attribute:: safe_labels
      :value: True



   .. py:property:: name
      :type: str


      Return the name of the operation.


   .. py:property:: duration
      :type: float


      The duration of this operation.


   .. py:method:: get_used_port_clocks() -> set[tuple[str, str]]

      Extracts which port-clock combinations are used in this operation.

      :returns: :
                    All (port, clock) combinations this operation uses.




.. py:class:: Q1ASMOpInfo(inline_q1asm: InlineQ1ASM, operation_start_time: float)

   Bases: :py:obj:`qblox_scheduler.backends.types.qblox.OpInfo`


   Structure describing an inline Q1ASM operation and containing all the information
   required to play it.


