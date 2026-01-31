compiler_abc
============

.. py:module:: qblox_scheduler.backends.qblox.compiler_abc 

.. autoapi-nested-parse::

   Compiler base and utility classes for Qblox backend.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.compiler_abc.InstrumentCompiler
   qblox_scheduler.backends.qblox.compiler_abc._AcquisitionGroup
   qblox_scheduler.backends.qblox.compiler_abc.SequencerCompiler
   qblox_scheduler.backends.qblox.compiler_abc._ModuleSettingsType
   qblox_scheduler.backends.qblox.compiler_abc.ClusterModuleCompiler




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.compiler_abc.logger
   qblox_scheduler.backends.qblox.compiler_abc.T
   qblox_scheduler.backends.qblox.compiler_abc._SequencerT_co


.. py:data:: logger

.. py:class:: InstrumentCompiler(name: str, total_play_time: float, instrument_cfg: qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig | qblox_scheduler.backends.qblox_backend._ClusterCompilationConfig | qblox_scheduler.backends.qblox_backend._LocalOscillatorCompilationConfig)

   Bases: :py:obj:`abc.ABC`


   Abstract base class that defines a generic instrument compiler.

   The subclasses that inherit from this are meant to implement the compilation
   steps needed to compile the lists of
   :class:`~qblox_scheduler.backends.types.qblox.OpInfo` representing the
   pulse and acquisition information to device-specific instructions.

   Each device that needs to be part of the compilation process requires an
   associated ``InstrumentCompiler``.

   :param name: Name of the `QCoDeS` instrument this compiler object corresponds to.
   :param total_play_time: Total time execution of the schedule should go on for. This parameter is
                           used to ensure that the different devices, potentially with different clock
                           rates, can work in a synchronized way when performing multiple executions of
                           the schedule.
   :param instrument_cfg: The compilation config referring to this device.


   .. py:attribute:: name


   .. py:attribute:: total_play_time


   .. py:attribute:: instrument_cfg


   .. py:method:: prepare(**kwargs) -> None

      Method that can be overridden to implement logic before the main compilation
      starts. This step is to extract all settings for the devices that are dependent
      on settings of other devices. This step happens after instantiation of the
      compiler object but before the start of the main compilation.



   .. py:method:: compile(debug_mode: bool, repetitions: int) -> object
      :abstractmethod:


      An abstract method that should be overridden in a subclass to implement the
      actual compilation. It should turn the pulses and acquisitions added to the
      device into device-specific instructions.

      :param debug_mode: Debug mode can modify the compilation process,
                         so that debugging of the compilation process is easier.
      :param repetitions: Number of times execution of the schedule is repeated.

      :returns: :
                    A data structure representing the compiled program. The type is
                    dependent on implementation.




.. py:class:: _AcquisitionGroup

   Data to store for each acquisition group.


   .. py:attribute:: root
      :type:  qblox_scheduler.backends.qblox.qblox_acq_index_manager.AcqFullyAppendLoopNode


   .. py:attribute:: node
      :type:  qblox_scheduler.backends.qblox.qblox_acq_index_manager.AcqFullyAppendLoopNode


   .. py:attribute:: acq_strategies
      :type:  list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]


   .. py:method:: _current_loop_bin_modes() -> list[qblox_scheduler.enums.BinMode | None]


   .. py:method:: is_compatible(loop_bin_modes: list[qblox_scheduler.enums.BinMode]) -> bool

      Checks whether an acquisition with the loop_bin_modes (the argument)
      is compatible with the group, if the acquisition was added to the current node.
      An acquisition is compatible with a group if for all loops in the group
      and for the acquisitions the same bin mode is applied.



   .. py:method:: update_loop_bin_modes(loop_bin_modes: list[qblox_scheduler.enums.BinMode]) -> None

      Update the tree with the new loop bin modes.
      This is needed to be called, because when iterating the operations,
      we do not know beforehand which loops are using which bin modes,
      it is determined by the acquisition inside of them.
      So when we find a new acquisition, we update all loop bin modes in the tree.



   .. py:method:: add_acquisition(strategy: qblox_scheduler.backends.qblox.operation_handling.acquisitions.AcquisitionStrategyPartial) -> None

      Add acquisition to the group at the current node.
      Note, this function does not check whether the acquisition is compatible with the group.
      First, check that with the `is_compatible` function.



   .. py:property:: number_of_acq_indices
      :type: int


      Number of total acquisition indices in the group.


.. py:data:: T

.. py:class:: SequencerCompiler(parent: ClusterModuleCompiler, index: int, static_hw_properties: qblox_scheduler.backends.types.qblox.StaticHardwareProperties, sequencer_cfg: qblox_scheduler.backends.qblox_backend._SequencerCompilationConfig)

   Bases: :py:obj:`abc.ABC`


   Class that performs the compilation steps on the sequencer level.

   Abstract base class for different sequencer types.

   :param parent: A reference to the module compiler this sequencer belongs to.
   :param index: Index of the sequencer.
   :param static_hw_properties: The static properties of the hardware.
                                This effectively gathers all the differences between the different modules.
   :param sequencer_cfg: The instrument compiler config associated to this instrument.


   .. py:attribute:: _settings
      :type:  qblox_scheduler.backends.types.qblox.SequencerSettings


   .. py:attribute:: parent


   .. py:attribute:: index


   .. py:attribute:: port


   .. py:attribute:: clock


   .. py:attribute:: op_strategies
      :type:  list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]
      :value: []



   .. py:attribute:: static_hw_properties


   .. py:attribute:: register_manager


   .. py:attribute:: qasm_hook_func


   .. py:attribute:: latency_correction


   .. py:attribute:: distortion_correction


   .. py:attribute:: qblox_acq_index_manager


   .. py:property:: connected_output_indices
      :type: tuple[int, Ellipsis]


      Return the connected output indices associated with the output name
      specified in the hardware config.

      For the baseband modules, output index 'n' corresponds to physical module
      output 'n+1'.

      For RF modules, output indices '0' and '1' (or: '2' and '3') correspond to
      'path_I' and 'path_Q' of some sequencer, and both these paths are routed to the
      **same** physical module output '1' (or: '2').


   .. py:property:: connected_input_indices
      :type: tuple[int, Ellipsis]


      Return the connected input indices associated with the input name specified
      in the hardware config.

      For the baseband modules, input index 'n' corresponds to physical module input
      'n+1'.

      For RF modules, input indices '0' and '1' correspond to 'path_I' and 'path_Q' of
      some sequencer, and both paths are connected to physical module input '1'.


   .. py:property:: portclock
      :type: tuple[str, str]


      A tuple containing the unique port and clock combination for this sequencer.

      :returns: :
                    The portclock.


   .. py:property:: settings
      :type: qblox_scheduler.backends.types.qblox.SequencerSettings


      Gives the current settings.

      :returns: :
                    The settings set to this sequencer.


   .. py:property:: name
      :type: str


      The name assigned to this specific sequencer.

      :returns: :
                    The name.


   .. py:property:: has_data
      :type: bool


      Whether or not the sequencer has any data (meaning pulses or acquisitions)
      assigned to it or not.

      :returns: :
                    Has data been assigned to this sequencer?


   .. py:method:: get_operation_strategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo) -> qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy
      :abstractmethod:


      Determines and instantiates the correct strategy object.

      :param operation_info: The operation we are building the strategy for.

      :returns: :
                    The instantiated strategy object.




   .. py:method:: _get_unique_value_or_raise(values: collections.abc.Iterable[T], setting_name: str) -> T

      Exception that occurs when multiple different values are derived for a setting.



   .. py:method:: add_operation_strategy(op_strategy: qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy) -> None

      Adds the operation strategy to the sequencer compiler.

      :param op_strategy: The operation strategy.



   .. py:method:: _generate_awg_dict() -> dict[str, Any]

      Generates the dictionary that contains the awg waveforms in the
      format accepted by the driver.

      .. rubric:: Notes

      The final dictionary to be included in the json that is uploaded to the module
      is of the form:

      .. code-block::

          program
          awg
              waveform_name
                  data
                  index
          acq
              waveform_name
                  data
                  index

      This function generates the awg dictionary.

      :returns: :
                    The awg dictionary.

      :raises ValueError: I or Q amplitude is being set outside of maximum range.
      :raises RuntimeError: When the total waveform size specified for a port-clock combination exceeds
          the waveform sample limit of the hardware.



   .. py:method:: _generate_weights_dict() -> dict[str, Any]

      Generates the dictionary that corresponds that contains the acq weights
      waveforms in the format accepted by the driver.

      .. rubric:: Notes

      The final dictionary to be included in the json that is uploaded to the module
      is of the form:

      .. code-block::

          program
          awg
              waveform_name
                  data
                  index
          acq
              waveform_name
                  data
                  index

      This function generates the acq dictionary.

      :returns: :
                    The acq dictionary.

      :raises NotImplementedError: Currently, only two one dimensional waveforms can be used as acquisition
          weights. This exception is raised when either or both waveforms contain
          both a real and imaginary part.



   .. py:method:: _validate_awg_dict(wf_dict: dict[str, Any]) -> None


   .. py:method:: _prepare_acq_settings(acquisitions: list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]) -> None
      :abstractmethod:


      Sets sequencer settings that are specific to certain acquisitions.
      For example for a TTL acquisition strategy.

      :param acquisitions: List of the acquisitions assigned to this sequencer.



   .. py:method:: _validate_thresholded_trigger_count_metadata_by_acq_channel(acquisitions: list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]) -> None

      Validate that all thresholds are the same for **single** threshold ThresholdedTriggerCount
      acquisitions on this sequencer.

      :returns: :
                    The threshold, if ThresholdedTriggerCount acquisition is scheduled,
                    or None, if it is not scheduled.

      :raises RuntimeError: If different thresholds are found.



   .. py:method:: generate_qasm_program(ordered_op_strategies: list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy], total_sequence_time: float, align_qasm_fields: bool, repetitions: int) -> str

      Generates a QASM program for a sequencer. Requires the awg and acq dicts to
      already have been generated.

      Example of a program generated by this function:

      .. code-block::

                  wait_sync     4
                  set_mrk       1
                  move          10,R0         # iterator for loop with label start
          start:
                  wait          4
                  set_awg_gain  22663,10206  # setting gain for 9056793381316377208
                  play          0,1,4
                  wait          176
                  loop          R0,@start
                  set_mrk       0
                  upd_param     4
                  stop


      :param ordered_op_strategies: A sorted list of operations, in order of execution.
      :param total_sequence_time: Total time the program needs to play for. If the sequencer would be done
                                  before this time, a wait is added at the end to ensure synchronization.
      :param align_qasm_fields: If True, make QASM program more human-readable by aligning its fields.
      :param repetitions: Number of times to repeat execution of the schedule.

      :returns: :
                    The generated QASM program.

      :Warns: **RuntimeWarning** -- When number of instructions in the generated QASM program exceeds the
              maximum supported number of instructions for sequencers in the type of
              module.

      :raises RuntimeError: Upon ``total_sequence_time`` exceeding :attr:`.QASMProgram.elapsed_time`.



   .. py:method:: _assert_total_play_time_on_nco_grid() -> None

      Raises an error if the total play time does not align with the NCO grid time.

      Method is implemented on the base class instead of the `AnalogSequencerCompiler`
      subclass because it is called by `generate_qasm_program`.



   .. py:class:: ParseOperationStatus(*args, **kwds)

      Bases: :py:obj:`enum.Enum`


      Return status of the stack.


      .. py:attribute:: COMPLETED_ITERATION

         The iterator containing operations is exhausted.


      .. py:attribute:: EXITED_CONTROL_FLOW

         The end of a control flow scope is reached.



   .. py:method:: _parse_operations(operations_iter: collections.abc.Iterator[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy], qasm: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> ParseOperationStatus

      Handle control flow and insert Q1ASM.



   .. py:method:: _insert_qasm(op_strategy: qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy, qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None
      :abstractmethod:


      Get Q1ASM instruction(s) from ``op_strategy`` and insert them into ``qasm_program``.



   .. py:method:: _write_pre_wait_sync_instructions(qasm: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None
      :abstractmethod:


      Write instructions to the QASM program that must come before the first wait_sync.

      The duration must be equal for all module types.



   .. py:method:: _write_repetition_loop_header(qasm: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None
      :abstractmethod:


      Write the Q1ASM that should appear at the start of the repetition loop.

      The duration must be equal for all module types.



   .. py:method:: _get_ordered_operations() -> list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]

      Get the class' operation strategies in order of scheduled execution.



   .. py:method:: _create_acq_groups(op_strategies: collections.abc.Iterable[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]) -> list[_AcquisitionGroup]
      :staticmethod:



   .. py:method:: _initialize_acquisitions_fully_append_with_average_append_bin_mode(qasm: qblox_scheduler.backends.qblox.qasm_program.QASMProgram, op_strategies: list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]) -> None


   .. py:method:: _initialize_acquisitions(qasm: qblox_scheduler.backends.qblox.qasm_program.QASMProgram, op_strategies: list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy], repetitions: int) -> None

      Adds the instructions to initialize the registers needed to use the append
      bin mode to the program. This should be added in the header.

      :param qasm: The program to add the instructions to.
      :param op_strategies: An operations list including all the acquisitions to consider.
      :param repetitions: TimeableSchedule repetitions.



   .. py:method:: _allocate_acquisition_memory_and_bin_register(protocol: str, bin_mode: qblox_scheduler.enums.BinMode, acq_data: dict, acq_channel: collections.abc.Hashable, repetitions: int, op_info: qblox_scheduler.backends.types.qblox.OpInfo) -> tuple[int, int, str | None]


   .. py:method:: _get_latency_correction_ns(latency_correction: float) -> int


   .. py:method:: _remove_redundant_update_parameters() -> None

      Removing redundant update parameter instructions.
      If multiple update parameter instructions happen at the same time,
      directly after each other in order, then it's safe to only keep one of them.

      Also, real time io operations act as update parameter instructions too.
      If a real time io operation happen ((just after or just before) and at the same time)
      as an update parameter instruction, then the update parameter instruction is redundant.



   .. py:method:: _validate_update_parameters_alignment() -> None


   .. py:method:: _replace_digital_pulses(op_strategies: list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy], module_options: qblox_scheduler.backends.types.qblox.ClusterModuleDescription) -> list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]
      :staticmethod:


      Replaces MarkerPulse operations by explicit high and low operations.



   .. py:method:: _generate_waveforms_and_program_dict(program: str, waveforms_dict: dict[str, Any], weights_dict: dict[str, Any] | None = None, acq_decl_dict: dict[str, Any] | None = None) -> dict[str, Any]
      :staticmethod:


      Generates the full waveforms and program dict that is to be uploaded to the
      sequencer from the program string and the awg and acq dicts, by combining them
      and assigning the appropriate keys.

      :param program: The compiled QASM program as a string.
      :param waveforms_dict: The dictionary containing all the awg data and indices. This is expected to
                             be of the form generated by the ``generate_awg_dict`` method.
      :param weights_dict: The dictionary containing all the acq data and indices. This is expected to
                           be of the form generated by the ``generate_acq_dict`` method.
      :param acq_decl_dict: The dictionary containing all the acq declarations. This is expected to be
                            of the form generated by the ``generate_acq_decl_dict`` method.

      :returns: :
                    The combined program.




   .. py:method:: _dump_waveforms_and_program_json(wf_and_pr_dict: dict[str, Any], label: str | None = None) -> str
      :staticmethod:


      Takes a combined waveforms and program dict and dumps it as a json file.

      :param wf_and_pr_dict: The dict to dump as a json file.
      :param label: A label that is appended to the filename.

      :returns: :
                    The full absolute path where the json file is stored.




   .. py:method:: prepare() -> None

      Perform necessary operations on this sequencer's data before
      :meth:`~SequencerCompiler.compile` is called.



   .. py:method:: _prepare_threshold_settings(operations: list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]) -> None

      Derive sequencer settings for trigger count thresholding.

      :param operations: List of the acquisitions assigned to this sequencer.



   .. py:method:: compile(sequence_to_file: bool, align_qasm_fields: bool, repetitions: int = 1) -> qblox_scheduler.backends.types.qblox.SequencerSettings | None

      Performs the full sequencer level compilation based on the assigned data and
      settings. If no data is assigned to this sequencer, the compilation is skipped
      and None is returned instead.

      :param sequence_to_file: Dump waveforms and program dict to JSON file, filename stored in
                               `SequencerCompiler.settings.seq_fn`.
      :param align_qasm_fields: If True, make QASM program more human-readable by aligning its fields.
      :param repetitions: Number of times execution the schedule is repeated.

      :returns: :
                    The compiled program.
                    If no data is assigned to this sequencer, the
                    compilation is skipped and None is returned instead.




   .. py:method:: _validate_thresholded_acquisitions(operations: list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy], protocol: str) -> None

      All thresholded acquisitions on a single sequencer must have the same label and the same
      threshold settings.



.. py:data:: _SequencerT_co

   A generic SequencerCompiler type for typehints in :class:`ClusterModuleCompiler`.

   Covariant so that subclasses of ClusterModuleCompiler can use subclassses of
   :class:`SequencerCompiler` in their typehints.

.. py:class:: _ModuleSettingsType

   Bases: :py:obj:`Protocol`


   A typehint for the various module settings (e.g.
   :class:`~qblox_scheduler.backends.types.qblox.BasebandModuleSettings`) classes.


   .. py:method:: to_dict() -> dict[str, Any]

      Convert the settings to a dictionary.



.. py:class:: ClusterModuleCompiler(name: str, total_play_time: float, instrument_cfg: qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig)

   Bases: :py:obj:`InstrumentCompiler`, :py:obj:`Generic`\ [\ :py:obj:`_SequencerT_co`\ ], :py:obj:`abc.ABC`


   Base class for all cluster modules, and an interface for those modules to the
   :class:`~qblox_scheduler.backends.qblox.instrument_compilers.ClusterCompiler`.

   This class is defined as an abstract base class since the distinctions between the
   different devices are defined in subclasses.
   Effectively, this base class contains the functionality shared by all Qblox
   devices and serves to avoid repeated code between them.

   :param name: Name of the `QCoDeS` instrument this compiler object corresponds to.
   :param total_play_time: Total time execution of the schedule should go on for. This parameter is
                           used to ensure that the different devices, potentially with different clock
                           rates, can work in a synchronized way when performing multiple executions of
                           the schedule.
   :param instrument_cfg: The instrument compiler config referring to this device.


   .. py:attribute:: _settings
      :type:  _ModuleSettingsType


   .. py:attribute:: static_hw_properties
      :type:  qblox_scheduler.backends.types.qblox.StaticHardwareProperties


   .. py:attribute:: instrument_cfg
      :type:  qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig


   .. py:attribute:: _op_infos
      :type:  dict[tuple[str, str], list[qblox_scheduler.backends.types.qblox.OpInfo]]


   .. py:attribute:: portclock_to_path


   .. py:attribute:: sequencers
      :type:  dict[str, _SequencerT_co]


   .. py:property:: portclocks
      :type: list[str]


      Returns all the port-clock combinations that this device can target.


   .. py:property:: supports_acquisition
      :type: bool

      :abstractmethod:


      Specifies whether the device can perform acquisitions.


   .. py:property:: max_number_of_instructions
      :type: int

      :abstractmethod:


      The maximum number of Q1ASM instructions supported by this module type.


   .. py:method:: add_op_info(port: str, clock: str, op_info: qblox_scheduler.backends.types.qblox.OpInfo) -> None

      Assigns a certain pulse or acquisition to this device.

      :param port: The port this waveform is sent to (or acquired from).
      :param clock: The clock for modulation of the pulse or acquisition. Can be a BasebandClock.
      :param op_info: Data structure containing all the information regarding this specific
                      pulse or acquisition operation.



   .. py:property:: _portclocks_with_data
      :type: set[tuple[str, str]]


      All the port-clock combinations associated with at least one pulse and/or
      acquisition.

      :returns: :
                    A set containing all the port-clock combinations that are used by this
                    InstrumentCompiler.


   .. py:method:: _construct_all_sequencer_compilers() -> None

      Constructs :class:`~SequencerCompiler` objects for each port and clock combination
      belonging to this device.

      :raises ValueError: Attempting to use more sequencers than available.



   .. py:method:: _construct_sequencer_compiler(index: int, sequencer_cfg: qblox_scheduler.backends.qblox_backend._SequencerCompilationConfig) -> _SequencerT_co
      :abstractmethod:


      Create the sequencer object of the correct sequencer type belonging to the module.



   .. py:method:: distribute_data() -> None

      Distributes the pulses and acquisitions assigned to this module over the
      different sequencers based on their portclocks. Raises an exception in case
      the device does not support acquisitions.



   .. py:method:: compile(debug_mode: bool, repetitions: int = 1, sequence_to_file: bool | None = None) -> dict[str, Any]

      Performs the actual compilation steps for this module, by calling the sequencer
      level compilation functions and combining them into a single dictionary.

      :param debug_mode: Debug mode can modify the compilation process,
                         so that debugging of the compilation process is easier.
      :param repetitions: Number of times execution the schedule is repeated.
      :param sequence_to_file: Dump waveforms and program dict to JSON file, filename stored in
                               `SequencerCompiler.settings.seq_fn`.

      :returns: :
                    The compiled program corresponding to this module.
                    It contains an entry for every sequencer under the key `"sequencers"`,
                    acquisition channels data, and
                    acquisition hardware mapping under the key `"acq_hardware_mapping"`,
                    and the `"repetitions"` is an integer with
                    the number of times the defined schedule is repeated.
                    All the other generic settings are under the key `"settings"`.
                    If the device is not actually used,
                    and an empty program is compiled, None is returned instead.




