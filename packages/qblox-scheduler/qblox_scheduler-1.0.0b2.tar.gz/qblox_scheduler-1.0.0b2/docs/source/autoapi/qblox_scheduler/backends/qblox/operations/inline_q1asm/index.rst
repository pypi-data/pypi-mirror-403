inline_q1asm
============

.. py:module:: qblox_scheduler.backends.qblox.operations.inline_q1asm 

.. autoapi-nested-parse::

   Qblox-specific operation which can be used to inject Q1ASM directly into a TimeableSchedule.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.operations.inline_q1asm.InlineQ1ASM




.. py:class:: InlineQ1ASM(program: str, duration: float, port: str, clock: str, *, waveforms: dict | None = None, safe_labels: bool = True)

   Bases: :py:obj:`qblox_scheduler.operations.hardware_operations.InlineQ1ASM`


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


