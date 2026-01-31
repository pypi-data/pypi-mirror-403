analog
======

.. py:module:: qblox_scheduler.backends.qblox.analog 

.. autoapi-nested-parse::

   Utility classes for Qblox analog modules.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.analog.AnalogSequencerCompiler
   qblox_scheduler.backends.qblox.analog.AnalogModuleCompiler
   qblox_scheduler.backends.qblox.analog.BasebandModuleCompiler
   qblox_scheduler.backends.qblox.analog.RFModuleCompiler




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.analog.logger


.. py:data:: logger

.. py:class:: AnalogSequencerCompiler(parent: AnalogModuleCompiler, index: int, static_hw_properties: qblox_scheduler.backends.types.qblox.StaticAnalogModuleProperties, sequencer_cfg: qblox_scheduler.backends.qblox_backend._SequencerCompilationConfig)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.compiler_abc.SequencerCompiler`


   Class that performs the compilation steps on the sequencer level, for QCM and
   QRM-type modules.

   :param parent: A reference to the module compiler this sequencer belongs to.
   :param index: Index of the sequencer.
   :param static_hw_properties: The static properties of the hardware.
                                This effectively gathers all the differences between the different modules.
   :param sequencer_cfg: The instrument compiler config associated to this device.


   .. py:attribute:: _settings
      :type:  qblox_scheduler.backends.types.qblox.AnalogSequencerSettings


   .. py:attribute:: associated_ext_lo


   .. py:attribute:: _associated_lo_frequency
      :type:  float | None
      :value: None



   .. py:attribute:: downconverter_freq


   .. py:attribute:: mix_lo


   .. py:attribute:: _marker_debug_mode_enable


   .. py:attribute:: _default_marker
      :value: 0



   .. py:property:: settings
      :type: qblox_scheduler.backends.types.qblox.AnalogSequencerSettings


      Gives the current settings. Overridden from the parent class for type hinting.

      :returns: :
                    The settings set to this sequencer.


   .. py:property:: frequency
      :type: float | None


      The frequency used for modulation of the pulses.

      :returns: :
                    The frequency.


   .. py:method:: set_associated_lo_frequency(lo_frequency: float) -> None

      Inform this sequencer of the frequency of the associated LO.

      This is a method to avoid accidentally overwriting it.



   .. py:method:: get_operation_strategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo) -> qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy

      Determines and instantiates the correct strategy object.

      :param operation_info: The operation we are building the strategy for.

      :returns: :
                    The instantiated strategy object.




   .. py:method:: _prepare_acq_settings(acquisitions: list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]) -> None

      Sets sequencer settings that are specific to certain acquisitions.
      For example for a TTL acquisition strategy.

      :param acquisitions: List of the acquisitions assigned to this sequencer.



   .. py:method:: _prepare_thresholded_acquisition_settings(acquisition_infos: list[qblox_scheduler.backends.types.qblox.OpInfo]) -> None


   .. py:method:: _get_integration_length_from_acquisitions() -> int | None

      Get the (validated) integration_length sequencer setting.

      Get the duration of all SSB integration acquisitions assigned to this sequencer
      and validate that they are all the same.



   .. py:method:: prepare() -> None

      Perform necessary operations on this sequencer's data before
      :meth:`~qblox_scheduler.backends.qblox.compiler_abc.SequencerCompiler.compile`
      is called.



   .. py:method:: _update_set_clock_frequency_operations_and_frequency_sweep_domains() -> None


   .. py:method:: _assert_enough_time_between_freq_phase_updates(ordered_op_strategies: list[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]) -> None
      :staticmethod:


      Check whether there is enough time between subsequent frequency or phase updates.



   .. py:method:: _write_pre_wait_sync_instructions(qasm: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Write instructions to the QASM program that must come before the first wait_sync.

      The duration must be equal for all module types.



   .. py:method:: _write_repetition_loop_header(qasm: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Write the Q1ASM that should appear at the start of the repetition loop.

      The duration must be equal for all module types.



   .. py:method:: _insert_qasm(op_strategy: qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy, qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Get Q1ASM instruction(s) from ``op_strategy`` and insert them into ``qasm_program``.

      Optionally wrap pulses and acquisitions in marker pulses depending on the
      ``marker_debug_mode_enable`` setting.



   .. py:method:: _decide_markers(operation: qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy) -> int

      Helper method to decide what markers should be pulled high when enable_marker is
      set to True.  Checks what module and operation are being processed, then builds
      a bit string accordingly.

      Note that with the current qblox-scheduler structure a sequencer cannot have connected
      inputs and outputs simultaneously.  Therefore, the QRM baseband module pulls
      both input or output markers high when doing an operation, as it is impossible
      during compile time to find out what physical port is being used.

      :param operation: The operation currently being processed by the sequence.

      :returns: A bit string passed on to the set_mrk function of the Q1ASM object.




.. py:class:: AnalogModuleCompiler(name: str, total_play_time: float, instrument_cfg: qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.compiler_abc.ClusterModuleCompiler`, :py:obj:`abc.ABC`


   Base class for QCM and QRM-type modules.

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
      :type:  qblox_scheduler.backends.types.qblox.AnalogModuleSettings


   .. py:attribute:: static_hw_properties
      :type:  qblox_scheduler.backends.types.qblox.StaticAnalogModuleProperties


   .. py:attribute:: sequencers
      :type:  dict[str, AnalogSequencerCompiler]


   .. py:method:: _construct_sequencer_compiler(index: int, sequencer_cfg: qblox_scheduler.backends.qblox_backend._SequencerCompilationConfig) -> AnalogSequencerCompiler

      Create an instance of :class:`AnalogSequencerCompiler`.



   .. py:method:: assign_frequencies(sequencer: AnalogSequencerCompiler, external_lo: qblox_scheduler.backends.qblox.instrument_compilers.LocalOscillatorCompiler | None, clock_frequency: float) -> None
      :abstractmethod:


      An abstract method that should be overridden. Meant to assign an IF frequency
      to each sequencer, and an LO frequency to each output (if applicable).

      :param sequencer: Sequencer compiler object whose NCO frequency will be determined and set.
      :param external_lo: Optional LO compiler object representing an external LO, whose LO frequency
                          will be determined and set.
      :param clock_frequency: Clock frequency of the clock assigned to the sequencer compiler.



   .. py:method:: assign_attenuation() -> None
      :abstractmethod:


      An abstract method that should be overridden. Meant to assign
      attenuation settings from the hardware configuration if there is any.



   .. py:method:: prepare(external_los: dict[str, qblox_scheduler.backends.qblox.instrument_compilers.LocalOscillatorCompiler] | None = None, schedule_resources: dict[str, qblox_scheduler.resources.Resource] | None = None, **kwargs) -> None

      Performs the logic needed before being able to start the compilation. In effect,
      this means assigning the pulses and acquisitions to the sequencers and
      calculating the relevant frequencies in case an external local oscillator is
      used.

      :param external_los: Optional LO compiler objects representing external LOs, whose LO frequency
                           will be determined and set.
      :param schedule_resources: Mapping from clock name to clock resource, which contains the clock frequency.
      :param kwargs: Potential keyword arguments for other compiler classes.



   .. py:method:: _configure_input_gains() -> None

      Configures input gain of module settings.
      Loops through all valid channel names and checks for gain values in hw config.



   .. py:method:: _configure_mixer_offsets() -> None

      Configures offset of input, uses calc_from_units_volt found in helper file.
      Raises an exception if a value outside the accepted voltage range is given.



   .. py:method:: _configure_distortion_correction_latency_compensations(distortion_configs: dict[int, Any] | None = None) -> None


   .. py:method:: _configure_dc_latency_comp_for_output(output: int, dc_comp: int) -> None


   .. py:method:: _configure_dc_latency_comp_for_marker(output: int, dc_comp: int) -> None


   .. py:method:: _configure_hardware_distortion_corrections() -> None

      Assign distortion corrections to settings of instrument compiler.



   .. py:method:: _ensure_single_scope_mode_acquisition_sequencer() -> None

      Raises an error if multiple sequencers use scope mode acquisition,
      because that's not supported by the hardware.
      Also, see
      :func:`~qblox_scheduler.instrument_coordinator.components.qblox._AnalogReadoutComponent._determine_scope_mode_acquisition_sequencer_and_qblox_acq_index`
      which also ensures the program that gets uploaded to the hardware satisfies this
      requirement.

      :raises ValueError: Multiple sequencers have to perform trace acquisition. This is not
          supported by the hardware.



.. py:class:: BasebandModuleCompiler(name: str, total_play_time: float, instrument_cfg: qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig)

   Bases: :py:obj:`AnalogModuleCompiler`, :py:obj:`abc.ABC`


   Abstract class with all the shared functionality between the QRM and QCM baseband
   modules.


   .. py:attribute:: _settings_type


   .. py:attribute:: _settings


   .. py:method:: assign_frequencies(sequencer: AnalogSequencerCompiler, external_lo: qblox_scheduler.backends.qblox.instrument_compilers.LocalOscillatorCompiler | None, clock_frequency: float) -> None

      Determines LO/IF frequencies and assigns them, for baseband modules.

      In case of **no** external local oscillator, the NCO is given the same
      frequency as the clock -- unless NCO was permanently disabled via
      `"interm_freq": 0` in the hardware config.

      In case of **an** external local oscillator and `sequencer.mix_lo` is
      ``False``, the LO is given the same frequency as the clock
      (via :func:`.helpers.determine_clock_lo_interm_freqs`).

      :param sequencer: Sequencer compiler object whose NCO frequency will be determined and set.
      :param external_lo: Optional LO compiler object representing an external LO, whose LO frequency
                          will be determined and set.
      :param clock_frequency: Clock frequency of the clock assigned to the sequencer compiler.

      :raises ValueError: If the NCO and/or LO frequencies cannot be determined, are invalid, or are
          inconsistent with the clock frequency.



   .. py:method:: assign_attenuation() -> None

      Meant to assign attenuation settings from the hardware configuration, if there
      is any. For baseband modules there is no attenuation parameters currently.



   .. py:method:: _configure_dc_latency_comp_for_marker(output: int, dc_comp: int) -> None


.. py:class:: RFModuleCompiler(name: str, total_play_time: float, instrument_cfg: qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig)

   Bases: :py:obj:`AnalogModuleCompiler`, :py:obj:`abc.ABC`


   Abstract class with all the shared functionality between the QRM-RF and QCM-RF
   modules.


   .. py:attribute:: _settings
      :type:  qblox_scheduler.backends.types.qblox.RFModuleSettings


   .. py:method:: assign_frequencies(sequencer: AnalogSequencerCompiler, external_lo: qblox_scheduler.backends.qblox.instrument_compilers.LocalOscillatorCompiler | None, clock_frequency: float) -> None

      Determines LO/IF frequencies and assigns them for RF modules.

      :param sequencer: Sequencer compiler object whose NCO frequency will be determined and set.
      :param external_lo: Optional LO compiler object representing an external LO. Not used for RF
                          modules, since they use the LO frequency in the module settings.
      :param clock_frequency: Clock frequency of the clock assigned to the sequencer compiler.

      :raises ValueError: If the NCO and/or LO frequencies cannot be determined, are invalid, or are
          inconsistent with the clock frequency.



   .. py:method:: _get_connected_lo_indices(sequencer: AnalogSequencerCompiler) -> collections.abc.Iterator[int]
      :staticmethod:


      Identify the LO the sequencer is outputting.
      Use the sequencer output to module output correspondence, and then
      use the fact that LOX is connected to module output X.



   .. py:method:: _validate_lo_index(lo_idx: int) -> None


   .. py:method:: _get_lo_frequency(lo_idx: int) -> float | None

      Get the LO frequency from the settings.

      :param lo_idx: The LO index.
      :type lo_idx: int

      :returns: float | None
                    The frequency, or None if it has not been determined yet.

      :raises IndexError: If the derived class instance does not contain an LO with that index.



   .. py:method:: _set_lo_frequency(lo_idx: int, frequency: float) -> None

      Set the LO frequency from the settings.

      :param lo_idx: The LO index.
      :type lo_idx: int
      :param frequency: The frequency.
      :type frequency: float

      :raises IndexError: If the derived class instance does not contain an LO with that index.



   .. py:method:: assign_attenuation() -> None

      Assigns attenuation settings from the hardware configuration.

      Floats that are a multiple of 1 are converted to ints.
      This is needed because the :func:`quantify_core.measurement.control.grid_setpoints`
      converts setpoints to floats when using an attenuation as settable.



   .. py:method:: _configure_dc_latency_comp_for_marker(output: int, dc_comp: int) -> None


