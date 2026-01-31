timetag
=======

.. py:module:: qblox_scheduler.backends.qblox.timetag 

.. autoapi-nested-parse::

   Utility classes for Qblox timetag module.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.timetag.TimetagSequencerCompiler




.. py:class:: TimetagSequencerCompiler(parent: qblox_scheduler.backends.qblox.instrument_compilers.QTMCompiler, index: int, static_hw_properties: qblox_scheduler.backends.types.qblox.StaticHardwareProperties, sequencer_cfg: qblox_scheduler.backends.qblox_backend._SequencerCompilationConfig)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.compiler_abc.SequencerCompiler`


   Class that performs the compilation steps on the sequencer level, for the QTM.

   :param parent: A reference to the module compiler this sequencer belongs to.
   :param index: Index of the sequencer.
   :param static_hw_properties: The static properties of the hardware.
                                This effectively gathers all the differences between the different modules.
   :param sequencer_cfg: The instrument compiler config associated to this device.


   .. py:attribute:: _settings
      :type:  qblox_scheduler.backends.types.qblox.TimetagSequencerSettings


   .. py:property:: settings
      :type: qblox_scheduler.backends.types.qblox.TimetagSequencerSettings


      Gives the current settings. Overridden from the parent class for type hinting.

      :returns: :
                    The settings set to this sequencer.


   .. py:method:: prepare() -> None

      Perform necessary operations on this sequencer's data before
      :meth:`~qblox_scheduler.backends.qblox.compiler_abc.SequencerCompiler.compile`
      is called.



   .. py:method:: _assert_correct_time_ref_used_with_timestamp() -> None

      Assert that the Timestamp operation is present if the user specified the
      appropriate argument for the Timetag acquisition, or vice-versa that there is no
      Timestamp operation present if the user specified another time reference.

      Warn if this is not the case.



   .. py:method:: _assert_fine_delays_executable(ordered_op_strategies: list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]) -> None
      :staticmethod:


      Check whether any operations with a fine delay argument are executable on the
      hardware.

      To avoid undefined behaviour, there must be at least 7ns between consecutive
      Q1ASM instructions with fine delay, OR the time between such instructions must
      be an integer number of nanoseconds.

      Must be called before `SequencerCompiler._replace_digital_pulses`.



   .. py:method:: get_operation_strategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo) -> qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy

      Determines and instantiates the correct strategy object.

      :param operation_info: The operation we are building the strategy for.

      :returns: :
                    The instantiated strategy object.




   .. py:method:: _prepare_acq_settings(acquisitions: list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]) -> None

      Sets sequencer settings that are specific to certain acquisitions.
      For example for a TTL acquisition strategy.

      :param acquisitions: List of the acquisitions assigned to this sequencer.



   .. py:method:: _prepare_thresholded_trigger_count_settings(acquisitions: list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]) -> None


   .. py:method:: _prepare_dual_thresholded_trigger_count_settings(acquisitions: list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]) -> None


   .. py:method:: _write_pre_wait_sync_instructions(qasm: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Write instructions to the QASM program that must come before the first wait_sync.

      The duration must be equal for all module types.



   .. py:method:: _write_repetition_loop_header(qasm: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Write the Q1ASM that should appear at the start of the repetition loop.

      The duration must be equal for all module types.



   .. py:method:: _insert_qasm(op_strategy: qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy, qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Get Q1ASM instruction(s) from ``op_strategy`` and insert them into ``qasm_program``.



