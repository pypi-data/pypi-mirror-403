instrument_compilers
====================

.. py:module:: qblox_scheduler.backends.qblox.instrument_compilers 

.. autoapi-nested-parse::

   Compiler classes for Qblox backend.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.instrument_compilers.LocalOscillatorCompiler
   qblox_scheduler.backends.qblox.instrument_compilers.QCMCompiler
   qblox_scheduler.backends.qblox.instrument_compilers.QRMCompiler
   qblox_scheduler.backends.qblox.instrument_compilers.QCMRFCompiler
   qblox_scheduler.backends.qblox.instrument_compilers.QRMRFCompiler
   qblox_scheduler.backends.qblox.instrument_compilers.QRCCompiler
   qblox_scheduler.backends.qblox.instrument_compilers.QTMCompiler
   qblox_scheduler.backends.qblox.instrument_compilers.QSMCompiler
   qblox_scheduler.backends.qblox.instrument_compilers.ClusterCompiler




.. py:class:: LocalOscillatorCompiler(name: str, total_play_time: float, instrument_cfg: qblox_scheduler.backends.qblox_backend._LocalOscillatorCompilationConfig)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.compiler_abc.InstrumentCompiler`


   Implementation of an
   :class:`~qblox_scheduler.backends.qblox.compiler_abc.InstrumentCompiler`
   that compiles for a generic LO. The main
   difference between this class and the other compiler classes is that it doesn't take
   pulses and acquisitions.


   :param name: QCoDeS name of the device it compiles for.
   :param total_play_time: Total time execution of the schedule should go on for. This parameter is
                           used to ensure that the different devices, potentially with different clock
                           rates, can work in a synchronized way when performing multiple executions of
                           the schedule.
   :param instrument_cfg: The compiler config referring to this instrument.


   .. py:attribute:: freq_param_name
      :value: 'frequency'



   .. py:attribute:: _frequency


   .. py:attribute:: power_param_name
      :value: 'power'



   .. py:attribute:: _power


   .. py:property:: frequency
      :type: float | None


      Getter for the frequency.

      :returns: :
                    The current frequency.


   .. py:method:: compile(debug_mode: bool, repetitions: int = 1) -> dict[str, Any] | None

      Compiles the program for the LO InstrumentCoordinator component.

      :param debug_mode: Debug mode can modify the compilation process,
                         so that debugging of the compilation process is easier.
      :param repetitions: Number of times execution the schedule is repeated.

      :returns: :
                    Dictionary containing all the information the InstrumentCoordinator
                    component needs to set the parameters appropriately.




.. py:class:: QCMCompiler(name: str, total_play_time: float, instrument_cfg: qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.analog.BasebandModuleCompiler`


   QCM specific implementation of the qblox compiler.


   .. py:attribute:: _settings_type


   .. py:attribute:: supports_acquisition
      :value: False


      Specifies whether the device can perform acquisitions.


   .. py:attribute:: max_number_of_instructions
      :value: 16384


      The maximum number of Q1ASM instructions supported by this module type.


   .. py:attribute:: static_hw_properties
      :type:  qblox_scheduler.backends.types.qblox.StaticAnalogModuleProperties


   .. py:method:: _configure_hardware_distortion_corrections() -> None

      Assign distortion corrections to settings of instrument compiler.



   .. py:method:: _get_distortion_configs_per_output() -> dict[int, dict]


   .. py:method:: _configure_filter(filt: qblox_scheduler.backends.types.qblox.QbloxRealTimeFilter, coefficient: float, marker_debug_mode_enable: bool) -> None


.. py:class:: QRMCompiler(name: str, total_play_time: float, instrument_cfg: qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.analog.BasebandModuleCompiler`


   QRM specific implementation of the qblox compiler.


   .. py:attribute:: _settings_type


   .. py:attribute:: supports_acquisition
      :value: True


      Specifies whether the device can perform acquisitions.


   .. py:attribute:: max_number_of_instructions
      :value: 12288


      The maximum number of Q1ASM instructions supported by this module type.


   .. py:attribute:: static_hw_properties
      :type:  qblox_scheduler.backends.types.qblox.StaticAnalogModuleProperties


.. py:class:: QCMRFCompiler(name: str, total_play_time: float, instrument_cfg: qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.analog.RFModuleCompiler`


   QCM-RF specific implementation of the qblox compiler.


   .. py:attribute:: supports_acquisition
      :value: False


      Specifies whether the device can perform acquisitions.


   .. py:attribute:: max_number_of_instructions
      :value: 16384


      The maximum number of Q1ASM instructions supported by this module type.


   .. py:attribute:: static_hw_properties
      :type:  qblox_scheduler.backends.types.qblox.StaticAnalogModuleProperties


.. py:class:: QRMRFCompiler(name: str, total_play_time: float, instrument_cfg: qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.analog.RFModuleCompiler`


   QRM-RF specific implementation of the qblox compiler.


   .. py:attribute:: supports_acquisition
      :value: True


      Specifies whether the device can perform acquisitions.


   .. py:attribute:: max_number_of_instructions
      :value: 12288


      The maximum number of Q1ASM instructions supported by this module type.


   .. py:attribute:: static_hw_properties
      :type:  qblox_scheduler.backends.types.qblox.StaticAnalogModuleProperties


.. py:class:: QRCCompiler(name: str, total_play_time: float, instrument_cfg: qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.analog.RFModuleCompiler`


   QRC specific implementation of the qblox compiler.


   .. py:attribute:: supports_acquisition
      :value: True


      Specifies whether the device can perform acquisitions.


   .. py:attribute:: max_number_of_instructions
      :value: 12288


      The maximum number of Q1ASM instructions supported by this module type.


   .. py:attribute:: static_hw_properties


.. py:class:: QTMCompiler(name: str, total_play_time: float, instrument_cfg: qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.compiler_abc.ClusterModuleCompiler`


   QTM specific implementation of the qblox compiler.

   :param name: Name of the `QCoDeS` instrument this compiler object corresponds to.
   :param total_play_time: Total time execution of the schedule should go on for. This parameter is
                           used to ensure that the different devices, potentially with different clock
                           rates, can work in a synchronized way when performing multiple executions of
                           the schedule.
   :param instrument_cfg: The instrument compilation config referring to this device.


   .. py:attribute:: static_hw_properties
      :type:  qblox_scheduler.backends.types.qblox.StaticTimetagModuleProperties


   .. py:attribute:: sequencers
      :type:  dict[str, qblox_scheduler.backends.qblox.timetag.TimetagSequencerCompiler]


   .. py:attribute:: _settings
      :type:  qblox_scheduler.backends.types.qblox.TimetagModuleSettings


   .. py:property:: max_number_of_instructions
      :type: int


      The maximum number of Q1ASM instructions supported by this module type.


   .. py:property:: supports_acquisition
      :type: bool


      Specifies whether the device can perform acquisitions.


   .. py:method:: _construct_sequencer_compiler(index: int, sequencer_cfg: qblox_scheduler.backends.qblox_backend._SequencerCompilationConfig) -> qblox_scheduler.backends.qblox.timetag.TimetagSequencerCompiler

      Create the sequencer object of the correct sequencer type belonging to the module.



   .. py:method:: prepare(**kwargs) -> None

      Performs the logic needed before being able to start the compilation. In effect,
      this means assigning the pulses and acquisitions to the sequencers and
      calculating the relevant frequencies in case an external local oscillator is
      used.



   .. py:method:: _set_time_ref_channel(op_infos: dict[tuple[str, str], list[qblox_scheduler.backends.types.qblox.OpInfo]], portclock_to_path: dict[str, qblox_scheduler.backends.qblox_backend.ChannelPath]) -> None
      :staticmethod:


      Set the time_ref_channel for all Timetag operations using TimeRef.PORT.

      Needs to be called before `SequencerCompiler._prepare_acq_settings()`.

      It is not validated that there is indeed a timetag acquisition on the port that was
      referenced, as this is not necessary for the schedule to run without errors.



.. py:class:: QSMCompiler(name: str, total_play_time: float, instrument_cfg: qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.compiler_abc.ClusterModuleCompiler`


   QSM specific implementation of the qblox compiler.


   .. py:attribute:: _settings
      :type:  qblox_scheduler.backends.types.qblox.DCModuleSettings


   .. py:attribute:: supports_acquisition
      :value: False


      Specifies whether the device can perform acquisitions.


   .. py:attribute:: max_number_of_instructions
      :value: 16384


      The maximum number of Q1ASM instructions supported by this module type.


   .. py:attribute:: static_hw_properties
      :type:  qblox_scheduler.backends.types.qblox.StaticDCModuleProperties


   .. py:method:: prepare(**kwargs) -> None

      Do nothing, the QSM settings are already filled.



   .. py:method:: add_op_info(port: str, clock: str, op_info: qblox_scheduler.backends.types.qblox.OpInfo) -> None

      Do nothing, the QSM has no real-time operations.



   .. py:property:: _portclocks_with_data
      :type: set[tuple[str, str]]


      Do nothing, the QSM has no operations for the sequencers.


   .. py:method:: _construct_all_sequencer_compilers() -> None

      Do nothing, the QSM has no sequencers.



   .. py:method:: _construct_sequencer_compiler(index: int, sequencer_cfg: qblox_scheduler.backends.qblox_backend._SequencerCompilationConfig) -> qblox_scheduler.backends.qblox.compiler_abc._SequencerT_co

      Do nothing, the QSM has no sequencers.



   .. py:method:: distribute_data() -> None

      Do nothing, the QSM has no sequencers.



   .. py:method:: compile(debug_mode: bool, repetitions: int = 1, sequence_to_file: bool | None = None) -> dict[str, Any]

      Return the QSM module settings.



.. py:class:: ClusterCompiler(name: str, total_play_time: float, instrument_cfg: qblox_scheduler.backends.qblox_backend._ClusterCompilationConfig)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.compiler_abc.InstrumentCompiler`


   Compiler class for a Qblox cluster.

   :param name: Name of the `QCoDeS` instrument this compiler object corresponds to.
   :param total_play_time: Total time execution of the schedule should go on for.
   :param instrument_cfg: The instrument compiler config referring to this device.


   .. py:attribute:: compiler_classes
      :type:  ClassVar[dict[str, type]]

      References to the individual module compiler classes that can be used by the
      cluster.


   .. py:attribute:: instrument_cfg
      :type:  qblox_scheduler.backends.qblox_backend._ClusterCompilationConfig


   .. py:attribute:: _settings
      :type:  qblox_scheduler.backends.types.qblox.ClusterSettings


   .. py:attribute:: _op_infos
      :type:  dict[tuple[str, str], list[qblox_scheduler.backends.types.qblox.OpInfo]]


   .. py:attribute:: instrument_compilers


   .. py:attribute:: portclock_to_path


   .. py:method:: add_op_info(port: str, clock: str, op_info: qblox_scheduler.backends.types.qblox.OpInfo) -> None

      Assigns a certain pulse or acquisition to this device.

      :param port: The port this waveform is sent to (or acquired from).
      :param clock: The clock for modulation of the pulse or acquisition. Can be a BasebandClock.
      :param op_info: Data structure containing all the information regarding this specific
                      pulse or acquisition operation.



   .. py:method:: _construct_module_compilers() -> dict[str, qblox_scheduler.backends.qblox.analog.AnalogModuleCompiler]

      Constructs the compilers for the modules inside the cluster.

      :returns: :
                    A dictionary with the name of the module as key and the value its
                    compiler.




   .. py:method:: prepare(external_los: dict[str, LocalOscillatorCompiler] | None = None, schedule_resources: dict[str, qblox_scheduler.resources.Resource] | None = None, **kwargs) -> None

      Prepares the instrument compiler for compilation by assigning the data.

      :param external_los: Optional LO compiler objects representing external LOs, whose LO frequency
                           will be determined and set.
      :param schedule_resources: Mapping from clock name to clock resource, which contains the clock frequency.
      :param kwargs: Potential keyword arguments for other compiler classes.



   .. py:method:: _validate_external_trigger_sync() -> None

      Validate _ClusterCompilationConfig.sync_on_external_trigger.

      If the slot and channel used for external trigger sync are also in portclock_to_path,
      validate that the settings do not conflict.



   .. py:method:: distribute_data() -> None

      Distributes the pulses and acquisitions assigned to the cluster over the
      individual module compilers.



   .. py:method:: compile(debug_mode: bool, repetitions: int = 1) -> dict[str, Any]

      Performs the compilation.

      :param debug_mode: Debug mode can modify the compilation process,
                         so that debugging of the compilation process is easier.
      :param repetitions: Amount of times to repeat execution of the schedule.

      :returns: :
                    The part of the compiled instructions relevant for this instrument.




