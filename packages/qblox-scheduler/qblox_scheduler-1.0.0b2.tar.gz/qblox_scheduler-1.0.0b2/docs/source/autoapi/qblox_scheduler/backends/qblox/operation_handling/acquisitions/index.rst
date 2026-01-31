acquisitions
============

.. py:module:: qblox_scheduler.backends.qblox.operation_handling.acquisitions 

.. autoapi-nested-parse::

   Classes for handling acquisitions.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.operation_handling.acquisitions.AcquisitionStrategyPartial
   qblox_scheduler.backends.qblox.operation_handling.acquisitions.SquareAcquisitionStrategy
   qblox_scheduler.backends.qblox.operation_handling.acquisitions.WeightedAcquisitionStrategy
   qblox_scheduler.backends.qblox.operation_handling.acquisitions.TriggerCountAcquisitionStrategy
   qblox_scheduler.backends.qblox.operation_handling.acquisitions.TimetagAcquisitionStrategy
   qblox_scheduler.backends.qblox.operation_handling.acquisitions.ScopedTimetagAcquisitionStrategy




.. py:class:: AcquisitionStrategyPartial(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy`


   Contains the logic shared between all the acquisitions.

   :param operation_info: The operation info that corresponds to this operation.


   .. py:attribute:: _acq_info
      :type:  qblox_scheduler.backends.types.qblox.OpInfo


   .. py:attribute:: bin_mode
      :type:  qblox_scheduler.enums.BinMode


   .. py:attribute:: acq_channel


   .. py:attribute:: qblox_acq_index
      :type:  int | None
      :value: None



   .. py:attribute:: qblox_acq_bin
      :type:  int | None
      :value: None



   .. py:attribute:: bin_idx_register
      :type:  str | None
      :value: None


      The register used to keep track of the bin index, only not None for append
      mode acquisitions.


   .. py:method:: insert_qasm(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Add the assembly instructions for the Q1 sequence processor that corresponds to
      this acquisition. This function calls the appropriate method to generate
      assembly, depending on the bin mode.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



   .. py:method:: reset_bin_idx_reg(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Resets the bin index register.
      This is used whenever the register which keeps track of the bin (for APPEND or
      AVERAGE_APPEND mode) needs to be reset.
      Used at the beginning of the whole program, or beginning of the schedule repetitions.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



   .. py:method:: _acquire_with_immediate_bin_index(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None
      :abstractmethod:


      Adds the assembly to the program for an acquisition with an immediate value for
      the bin index.



   .. py:method:: _acquire_with_register_bin_index(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None
      :abstractmethod:


      Adds the assembly to the program for an acquisition with a register value for
      the bin index, and assembly for incrementing the bin index by 1.



   .. py:property:: operation_info
      :type: qblox_scheduler.backends.types.qblox.OpInfo


      Property for retrieving the operation info.


   .. py:method:: _get_loop_bin_modes_with_schedule_repetitions() -> list[qblox_scheduler.enums.BinMode]

      For QASM compilation, we need information on the outermost Schedule's
      repetitions, and we handle that in the QASMProgram the same way
      as any other loop bin mode. So we prepend the bin mode of the
      outermost Schedule's bin mode to the loop bin modes.



.. py:class:: SquareAcquisitionStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`AcquisitionStrategyPartial`


   Performs a square acquisition (i.e. without acquisition weights).


   .. py:method:: generate_data(wf_dict: dict[str, Any]) -> None

      Returns None as no waveform is needed.



   .. py:method:: _acquire_with_immediate_bin_index(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Adds the assembly to the program for an acquisition with an immediate value for
      the bin index.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



   .. py:method:: _acquire_with_register_bin_index(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Adds the assembly to the program for an acquisition with a register value for
      the bin index, and assembly for incrementing the bin index by 1.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



   .. py:method:: _acquire_square(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram, bin_idx: int | str) -> None

      Adds the instruction for performing acquisitions without weights playback.

      :param qasm_program: The qasm program to add the acquisition to.
      :param bin_idx: The bin_idx to store the result in, can be either an int (for immediates) or
                      a str (for registers).



.. py:class:: WeightedAcquisitionStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`AcquisitionStrategyPartial`


   Performs a weighted acquisition.

   :param operation_info: The operation info that corresponds to this acquisition.


   .. py:attribute:: waveform_index0
      :type:  int | None
      :value: None



   .. py:attribute:: waveform_index1
      :type:  int | None
      :value: None



   .. py:method:: generate_data(wf_dict: dict[str, Any]) -> None

      Generates the waveform data for both acquisition weights.

      :param wf_dict: The dictionary to add the waveform to. N.B. the dictionary is modified in
                      function.



   .. py:method:: _acquire_with_immediate_bin_index(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Adds the assembly to the program for an acquisition with an immediate value for
      the bin index.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



   .. py:method:: _acquire_with_register_bin_index(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Adds the assembly to the program for an acquisition with a register value for
      the bin index, and assembly for incrementing the bin index by 1. Registers will
      be used for the weight indexes and the bin index.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



.. py:class:: TriggerCountAcquisitionStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`AcquisitionStrategyPartial`


   Performs a trigger count acquisition.


   .. py:method:: generate_data(wf_dict: dict[str, Any]) -> None

      Returns None as no waveform is needed.



   .. py:method:: _acquire_with_immediate_bin_index(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Adds the assembly to the program for an acquisition with an immediate value for
      the bin index.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



   .. py:method:: _acquire_with_register_bin_index(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Adds the assembly to the program for an acquisition with a register value for
      the bin index, and assembly for incrementing the bin index by 1.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



.. py:class:: TimetagAcquisitionStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`AcquisitionStrategyPartial`


   Performs a timetag acquisition.


   .. py:attribute:: _fine_start_delay_int


   .. py:attribute:: _fine_end_delay_int


   .. py:method:: generate_data(wf_dict: dict[str, Any]) -> None

      Returns None as no waveform is needed.



   .. py:method:: _acquire_with_immediate_bin_index(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Adds the assembly to the program for an acquisition with an immediate value for
      the bin index.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



   .. py:method:: _acquire_with_register_bin_index(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Adds the assembly to the program for an acquisition with a register value for
      the bin index, and assembly for incrementing the bin index by 1.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



.. py:class:: ScopedTimetagAcquisitionStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo)

   Bases: :py:obj:`TimetagAcquisitionStrategy`


   An acquisition strategy that wraps the emitted Q1ASM of
   ``TimetagAcquisitionStrategy`` in ``set_scope_en`` instructions.


   .. py:method:: _acquire_with_immediate_bin_index(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Adds the assembly to the program for an acquisition with an immediate value for
      the bin index.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



   .. py:method:: _acquire_with_register_bin_index(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Adds the assembly to the program for an acquisition with a register value for
      the bin index, and assembly for incrementing the bin index by 1.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



