qblox_backend
=============

.. py:module:: qblox_scheduler.backends.qblox_backend 

.. autoapi-nested-parse::

   Compiler backend for Qblox hardware.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox_backend.LongPulseReplacementSpec
   qblox_scheduler.backends.qblox_backend.OperationTimingInfo
   qblox_scheduler.backends.qblox_backend.ConditionalInfo
   qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig
   qblox_scheduler.backends.qblox_backend._LocalOscillatorCompilationConfig
   qblox_scheduler.backends.qblox_backend.AllowedChannels
   qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig
   qblox_scheduler.backends.qblox_backend._QCMCompilationConfig
   qblox_scheduler.backends.qblox_backend._QRMCompilationConfig
   qblox_scheduler.backends.qblox_backend._QCMRFCompilationConfig
   qblox_scheduler.backends.qblox_backend._QRMRFCompilationConfig
   qblox_scheduler.backends.qblox_backend._QRCCompilationConfig
   qblox_scheduler.backends.qblox_backend._QTMCompilationConfig
   qblox_scheduler.backends.qblox_backend._QSMCompilationConfig
   qblox_scheduler.backends.qblox_backend._SequencerCompilationConfig
   qblox_scheduler.backends.qblox_backend._ClusterCompilationConfig



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox_backend._all_pulses_with_abs_times
   qblox_scheduler.backends.qblox_backend._validate_non_overlapping_long_pulses
   qblox_scheduler.backends.qblox_backend._replace_long_pulses_recursively
   qblox_scheduler.backends.qblox_backend.compile_long_pulses_to_awg_offsets
   qblox_scheduler.backends.qblox_backend._all_conditional_acqs_and_control_flows_and_latch_reset
   qblox_scheduler.backends.qblox_backend._get_module_type
   qblox_scheduler.backends.qblox_backend._update_conditional_info_from_acquisition
   qblox_scheduler.backends.qblox_backend._set_conditional_info_map
   qblox_scheduler.backends.qblox_backend._insert_latch_reset
   qblox_scheduler.backends.qblox_backend.compile_conditional_playback
   qblox_scheduler.backends.qblox_backend.hardware_compile
   qblox_scheduler.backends.qblox_backend._add_support_input_channel_names
   qblox_scheduler.backends.qblox_backend._add_clock_freqs_to_set_clock_frequency
   qblox_scheduler.backends.qblox_backend._exists_pulse_starting_before_current_end
   qblox_scheduler.backends.qblox_backend._raise_if_pulses_overlap_on_same_port_clock
   qblox_scheduler.backends.qblox_backend._get_pulse_start_ends
   qblox_scheduler.backends.qblox_backend._operation_end



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox_backend.SequencerIndex


.. py:exception:: QbloxModuleNotFoundError

   Bases: :py:obj:`KeyError`


   Exception raised when a module is not defined in the hardware description.


.. py:class:: LongPulseReplacementSpec

   Specification for replacing long waveform pulses using a factory function.

   This dataclass encapsulates the criteria and behavior for identifying and replacing
   specific waveform types (e.g., square, ramp) based on their waveform function name
   and minimum duration.



   .. py:attribute:: wf_func_name
      :type:  str

      The name of the waveform function to match, e.g., qblox_scheduler.waveforms.square.


   .. py:attribute:: min_duration
      :type:  float

      The minimum duration (in seconds) a pulse must have to be eligible for replacement.


   .. py:attribute:: pulse_factory
      :type:  collections.abc.Callable

      A function that generates the replacement pulse, e.g., `long_square_pulse`.


   .. py:attribute:: extra_kwargs
      :type:  collections.abc.Callable[[dict], dict]

      A callable that receives the original pulse_info dictionary and returns
      additional keyword arguments to be passed to the `pulse_factory`.


   .. py:method:: match(pulse_info: dict) -> bool

      Checks whether the pulse_info matches with the current spec.



.. py:function:: _all_pulses_with_abs_times(operation: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule, time_offset: float, accumulator: list[tuple[float, qblox_scheduler.operations.operation.Operation]]) -> None

.. py:function:: _validate_non_overlapping_long_pulses(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, specs: list[LongPulseReplacementSpec]) -> None

   Raise an error when pulses overlap, if at least one contains a voltage offset.

   Since voltage offsets are sometimes used to construct pulses (see e.g.
   :func:`.long_square_pulse`), overlapping these with regular pulses in time on the
   same port-clock can lead to undefined behaviour.

   Note that for each schedulable, all pulse info entries with the same port and clock
   count as one pulse for that port and clock. This is because schedulables, starting
   before another schedulable has finished, could affect the waveforms or offsets in
   the remaining time of that other schedulable.


.. py:function:: _replace_long_pulses_recursively(operation: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule, specs: list[LongPulseReplacementSpec]) -> qblox_scheduler.schedules.schedule.TimeableSchedule | None

   Recursively replace long waveform pulses defined by multiple specs.

   :param operation: An operation or schedule possibly containing long pulses.
   :param specs: A list of LongPulseReplacementSpec, each describing one waveform type to replace.

   :returns: TimeableSchedule | None
                 Replacing operation if applicable. None if no replacement was required.



.. py:function:: compile_long_pulses_to_awg_offsets(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, config: qblox_scheduler.structure.model.DataStructure | dict) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Replace square and ramp pulses in the schedule with stitched long pulses using AWG offsets.

   :param schedule: A schedule possibly containing long square or ramp pulses.
   :type schedule: TimeableSchedule

   :returns: schedule : TimeableSchedule
                 Modified schedule with long pulses replaced using AWG offsets.



.. py:function:: _all_conditional_acqs_and_control_flows_and_latch_reset(operation: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule, time_offset: float, accumulator: list[tuple[float, qblox_scheduler.operations.operation.Operation]]) -> None

.. py:class:: OperationTimingInfo

   Timing information for an Operation.


   .. py:attribute:: start
      :type:  float

      start time of the operation.


   .. py:attribute:: end
      :type:  float

      end time of the operation.


   .. py:method:: from_operation_and_schedulable(operation: qblox_scheduler.operations.operation.Operation, schedulable: qblox_scheduler.schedules.schedule.Schedulable) -> OperationTimingInfo
      :classmethod:


      Create an ``OperationTimingInfo`` from an operation and a schedulable.



   .. py:method:: overlaps_with(operation_timing_info: OperationTimingInfo) -> bool

      Check if this operation timing info overlaps with another.



.. py:class:: ConditionalInfo

   Container for conditional address data.


   .. py:attribute:: portclocks
      :type:  set[tuple[str, str]]

      Port-clocks reading from the trigger address.


   .. py:attribute:: address
      :type:  int

      Trigger address.


   .. py:attribute:: _trigger_invert
      :type:  bool | None
      :value: None



   .. py:attribute:: _trigger_count
      :type:  int | None
      :value: None



   .. py:property:: trigger_invert
      :type: bool | None


      If True, inverts the threshold comparison result when reading from the trigger address
      counter.

      If a ThresholdedTriggerCount acquisition is done with a QRM, this must be set according to
      the condition you are trying to measure (greater than /equal to the threshold, or less than
      the threshold). If it is done with a QTM, this is set to False.


   .. py:property:: trigger_count
      :type: int | None


      The sequencer trigger address counter threshold.

      If a ThresholdedTriggerCount acquisition is done with a QRM, this must be set to the counts
      threshold. If it is done with a QTM, this is set to 1.


.. py:function:: _get_module_type(port: str, clock: str, compilation_config: qblox_scheduler.backends.graph_compilation.CompilationConfig) -> qblox_instruments.InstrumentType

.. py:function:: _update_conditional_info_from_acquisition(acq_info: dict[str, Any], cond_info: collections.defaultdict[str, ConditionalInfo], compilation_config: qblox_scheduler.backends.graph_compilation.CompilationConfig) -> None

.. py:function:: _set_conditional_info_map(operation: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule, conditional_info_map: collections.defaultdict[str, ConditionalInfo], compilation_config: qblox_scheduler.backends.graph_compilation.CompilationConfig) -> None

.. py:function:: _insert_latch_reset(operation: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule, abs_time_relative_to_schedule: float, schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, conditional_info_map: collections.defaultdict[str, ConditionalInfo]) -> None

.. py:function:: compile_conditional_playback(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, config: qblox_scheduler.backends.graph_compilation.CompilationConfig) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Compiles conditional playback.

   This compiler pass will determine the mapping between trigger labels and
   trigger addresses that the hardware will use. The feedback trigger address
   is stored under the key ``feedback_trigger_address`` in ``pulse_info`` and
   in ``acquisition_info`` of the corresponding operation.

   A valid conditional playback consists of two parts: (1) a conditional
   acquisition or measure, and (2) a conditional control flow. The first should
   always be followed by the second, else an error is raised. A conditional
   acquisition sends a trigger after the acquisition ends and if the
   acquisition crosses a certain threshold. Each sequencer that is subscribed
   to this trigger will increase their *latch* counters by one. To ensure the
   latch counters contain either 0 or 1 trigger counts, a
   :class:`~qblox_scheduler.operations.hardware_operations.pulse_library.LatchReset`
   operation is inserted right after the start of a conditional acquisition, on
   all sequencers. If this is not possible (e.g. due to concurring operations),
   a :class:`RuntimeError` is raised.

   :param schedule: The schedule to compile.

   :returns: TimeableSchedule
                 The returned schedule is a reference to the original `.TimeableSchedule``, but
                 updated.

   :raises RuntimeError: - If a conditional acquisitions/measures is not followed by a
         conditional control flow.
       - If a conditional control flow is not preceded by a conditional
         acquisition/measure.
       - If the compilation pass is unable to insert
         :class:`~qblox_scheduler.operations.hardware_operations.pulse_library.LatchReset`
         on all sequencers.


.. py:function:: hardware_compile(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, config: qblox_scheduler.backends.graph_compilation.CompilationConfig) -> qblox_scheduler.schedules.schedule.CompiledSchedule

   Generate qblox hardware instructions for executing the schedule.

   The principle behind the overall compilation is as follows:

   For every instrument in the hardware configuration, we instantiate a compiler
   object. Then we assign all the pulses/acquisitions that need to be played by that
   instrument to the compiler, which then compiles for each instrument individually.

   This function then returns all the compiled programs bundled together in a
   dictionary with the QCoDeS name of the instrument as key.

   :param schedule: The schedule to compile. It is assumed the pulse and acquisition info is
                    already added to the operation. Otherwise an exception is raised.
   :param config: Compilation config for
                  :class:`~qblox_scheduler.backends.graph_compilation.ScheduleCompiler`.

   :returns: :
                 The compiled schedule.



.. py:class:: QbloxHardwareCompilationConfig(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.backends.types.common.HardwareCompilationConfig`


   Data structure containing the information needed to compile to the Qblox backend.

   This information is structured in the same way as in the generic
   :class:`~qblox_scheduler.backends.types.common.HardwareCompilationConfig`, but
   contains fields for hardware-specific settings.


   .. py:attribute:: config_type
      :type:  Literal['QbloxHardwareCompilationConfig']
      :value: 'QbloxHardwareCompilationConfig'


      A reference to the
      :class:`~qblox_scheduler.backends.types.common.HardwareCompilationConfig`
      DataStructure for the Qblox backend.


   .. py:attribute:: version
      :type:  str
      :value: None


      Version of the specific hardware compilation config used.


   .. py:attribute:: hardware_description
      :type:  dict[str, qblox_scheduler.backends.types.qblox.QbloxHardwareDescription | qblox_scheduler.backends.types.common.HardwareDescription]

      Description of the instruments in the physical setup.


   .. py:attribute:: hardware_options
      :type:  qblox_scheduler.backends.types.qblox.QbloxHardwareOptions

      Options that are used in compiling the instructions for the hardware, such as
      :class:`~qblox_scheduler.backends.types.common.LatencyCorrection` or
      :class:`~qblox_scheduler.backends.types.qblox.SequencerOptions`.


   .. py:attribute:: compilation_passes
      :type:  list[qblox_scheduler.backends.graph_compilation.SimpleNodeConfig]
      :value: None


      The list of compilation nodes that should be called in succession to compile a
      schedule to instructions for the Qblox hardware.


   .. py:method:: _validate_connectivity_channel_names() -> QbloxHardwareCompilationConfig


   .. py:method:: _warn_mix_lo_false() -> QbloxHardwareCompilationConfig


   .. py:method:: _validate_versioning(config: dict[str, Any]) -> dict[str, Any]
      :classmethod:



   .. py:method:: _extract_instrument_compilation_configs(portclocks_used: set[tuple]) -> dict[str, Any]

      Extract an instrument compiler config
      for each instrument mentioned in ``hardware_description``.
      Each instrument config has a similar structure as ``QbloxHardwareCompilationConfig``,
      but contains only the settings related to their related instrument.
      Each config must contain at least one portclock referenced in ``portclocks_used``,
      otherwise the config is deleted.



   .. py:method:: _get_all_portclock_to_path_and_lo_name_to_path(portclocks_used: set[tuple[str, str]], cluster_configs: dict[str, _ClusterCompilationConfig], lo_configs: dict[str, _LocalOscillatorCompilationConfig]) -> None


.. py:class:: _LocalOscillatorCompilationConfig(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Configuration values for a
   :class:`qblox_scheduler.backends.qblox.instrument_compilers.LocalOscillatorCompiler`.


   .. py:attribute:: hardware_description
      :type:  qblox_scheduler.backends.types.common.LocalOscillatorDescription

      Description of the physical setup of this local oscillator.


   .. py:attribute:: frequency
      :type:  float | None
      :value: None


      The frequency of this local oscillator.


.. py:data:: SequencerIndex

   Index of a sequencer.

.. py:class:: AllowedChannels(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Allowed channels for a specific sequencer.


   .. py:attribute:: output
      :type:  set[str]

      Allowed outputs.

      For example `{"complex_output_0", "real_output_0", `digital_output_0"}`.


   .. py:attribute:: input
      :type:  set[str]

      Allowed inputs.

      For example `{"complex_input_1", "real_input_1"}`.


.. py:class:: _ClusterModuleCompilationConfig(/, **data: Any)

   Bases: :py:obj:`abc.ABC`, :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Configuration values for a :class:`~.ClusterModuleCompiler`.


   .. py:attribute:: hardware_description
      :type:  qblox_scheduler.backends.types.qblox.ClusterModuleDescription

      Description of the physical setup of this module.


   .. py:attribute:: hardware_options
      :type:  qblox_scheduler.backends.types.qblox.QbloxHardwareOptions

      Options that are used in compiling the instructions for the hardware.


   .. py:attribute:: portclock_to_path
      :type:  dict[str, qblox_scheduler.backends.types.common.ChannelPath]
      :value: None


      Mapping between portclocks and their associated channel name paths
      (e.g. cluster0.module1.complex_output_0).


   .. py:attribute:: lo_to_path
      :type:  dict[str, qblox_scheduler.backends.types.common.ChannelPath]
      :value: None


      Mapping between lo names and their associated channel name paths
      (e.g. cluster0.module1.complex_output_0).


   .. py:attribute:: parent_config_version
      :type:  str

      Version of the parent hardware compilation config used.


   .. py:attribute:: sequencer_allowed_channels
      :type:  ClassVar[dict[SequencerIndex, AllowedChannels]]

      Allowed channels for each sequencer.


   .. py:method:: _sequencer_to_portclock() -> dict[SequencerIndex, str]


   .. py:method:: _extract_sequencer_compilation_configs() -> dict[int, _SequencerCompilationConfig]


   .. py:method:: _validate_hardware_distortion_corrections_mode() -> _ClusterModuleCompilationConfig


   .. py:method:: _validate_input_gain_mode() -> _ClusterModuleCompilationConfig


   .. py:method:: _validate_channel_name_measure() -> None


.. py:class:: _QCMCompilationConfig(/, **data: Any)

   Bases: :py:obj:`_ClusterModuleCompilationConfig`


   QCM-specific configuration values for a :class:`~.ClusterModuleCompiler`.


   .. py:attribute:: sequencer_allowed_channels
      :type:  ClassVar[dict[SequencerIndex, AllowedChannels]]

      Allowed channels for each sequencer.


   .. py:method:: _validate_channel_name_measure() -> None


.. py:class:: _QRMCompilationConfig(/, **data: Any)

   Bases: :py:obj:`_ClusterModuleCompilationConfig`


   QRM-specific configuration values for a :class:`~.ClusterModuleCompiler`.


   .. py:attribute:: sequencer_allowed_channels
      :type:  ClassVar[dict[SequencerIndex, AllowedChannels]]

      Allowed channels for each sequencer.


   .. py:method:: _validate_channel_name_measure() -> None


.. py:class:: _QCMRFCompilationConfig(/, **data: Any)

   Bases: :py:obj:`_ClusterModuleCompilationConfig`


   QCM_RF-specific configuration values for a :class:`~.ClusterModuleCompiler`.


   .. py:attribute:: sequencer_allowed_channels
      :type:  ClassVar[dict[SequencerIndex, AllowedChannels]]

      Allowed channels for each sequencer.


   .. py:method:: _validate_channel_name_measure() -> None


.. py:class:: _QRMRFCompilationConfig(/, **data: Any)

   Bases: :py:obj:`_ClusterModuleCompilationConfig`


   QRMRF-specific configuration values for a :class:`~.ClusterModuleCompiler`.


   .. py:attribute:: sequencer_allowed_channels
      :type:  ClassVar[dict[SequencerIndex, AllowedChannels]]

      Allowed channels for each sequencer.


   .. py:method:: _validate_channel_name_measure() -> None


.. py:class:: _QRCCompilationConfig(/, **data: Any)

   Bases: :py:obj:`_ClusterModuleCompilationConfig`


   QRC-specific configuration values for a :class:`~.ClusterModuleCompiler`.


   .. py:attribute:: sequencer_allowed_channels
      :type:  ClassVar[dict[SequencerIndex, AllowedChannels]]

      Allowed channels for each sequencer.


   .. py:method:: _validate_channel_name_measure() -> None


.. py:class:: _QTMCompilationConfig(/, **data: Any)

   Bases: :py:obj:`_ClusterModuleCompilationConfig`


   QTM-specific configuration values for a :class:`~.ClusterModuleCompiler`.


   .. py:attribute:: sequencer_allowed_channels
      :type:  ClassVar[dict[SequencerIndex, AllowedChannels]]

      Allowed channels for each sequencer.


   .. py:method:: _validate_channel_name_measure() -> None


.. py:class:: _QSMCompilationConfig(/, **data: Any)

   Bases: :py:obj:`_ClusterModuleCompilationConfig`


   QSM-specific configuration values for a :class:`~.ClusterModuleCompiler`.


   .. py:attribute:: sequencer_allowed_channels
      :type:  ClassVar[dict[SequencerIndex, AllowedChannels]]

      Allowed channels for each sequencer.


.. py:class:: _SequencerCompilationConfig(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Configuration values for a :class:`~.SequencerCompiler`.


   .. py:attribute:: hardware_description
      :type:  qblox_scheduler.backends.types.qblox.ComplexChannelDescription | qblox_scheduler.backends.types.qblox.RealChannelDescription | qblox_scheduler.backends.types.qblox.DigitalChannelDescription

      Information needed to specify a complex/real/digital input/output.


   .. py:attribute:: sequencer_options
      :type:  qblox_scheduler.backends.types.qblox.SequencerOptions

      Configuration options for this sequencer.


   .. py:attribute:: portclock
      :type:  str

      Portclock associated to this sequencer.


   .. py:attribute:: channel_name
      :type:  str

      Channel name associated to this sequencer.


   .. py:attribute:: channel_name_measure
      :type:  None | list[str]

      Extra channel name necessary to define a `Measure` operation.


   .. py:attribute:: latency_correction
      :type:  qblox_scheduler.backends.types.common.LatencyCorrection

      Latency correction that should be applied to operations on this sequencer.


   .. py:attribute:: distortion_correction
      :type:  qblox_scheduler.backends.types.common.SoftwareDistortionCorrection | None

      Distortion corrections that should be applied to waveforms on this sequencer.


   .. py:attribute:: lo_name
      :type:  str | None

      Local oscillator associated to this sequencer.


   .. py:attribute:: modulation_frequencies
      :type:  qblox_scheduler.backends.types.common.ModulationFrequencies

      Modulation frequencies associated to this sequencer.


   .. py:attribute:: mixer_corrections
      :type:  qblox_scheduler.backends.types.qblox.QbloxMixerCorrections | None

      Mixer correction settings.


   .. py:attribute:: digitization_thresholds
      :type:  qblox_scheduler.backends.types.qblox.DigitizationThresholds | None
      :value: None


      The settings that determine when an analog voltage is counted as a pulse.


.. py:class:: _ClusterCompilationConfig(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Configuration values for a :class:`~.ClusterCompiler`.


   .. py:attribute:: hardware_description
      :type:  qblox_scheduler.backends.types.qblox.ClusterDescription

      Description of the physical setup of this cluster.


   .. py:attribute:: hardware_options
      :type:  qblox_scheduler.backends.types.qblox.QbloxHardwareOptions

      Options that are used in compiling the instructions for the hardware.


   .. py:attribute:: portclock_to_path
      :type:  dict[str, qblox_scheduler.backends.types.common.ChannelPath]
      :value: None


      Mapping between portclocks and their associated channel name paths
      (e.g. cluster0.module1.complex_output_0).


   .. py:attribute:: lo_to_path
      :type:  dict[str, qblox_scheduler.backends.types.common.ChannelPath]
      :value: None


      Mapping between lo names and their associated channel name paths
      (e.g. cluster0.module1.complex_output_0).


   .. py:attribute:: parent_config_version
      :type:  str

      Version of the parent hardware compilation config used.


   .. py:attribute:: module_config_classes
      :type:  ClassVar[dict[str, type[_ClusterModuleCompilationConfig]]]


   .. py:method:: _extract_module_compilation_configs() -> dict[int, _ClusterModuleCompilationConfig]


.. py:function:: _add_support_input_channel_names(module_config: _ClusterModuleCompilationConfig) -> None

.. py:function:: _add_clock_freqs_to_set_clock_frequency(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, operation: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule | None = None) -> None

.. py:function:: _exists_pulse_starting_before_current_end(abs_times_and_operations: list[tuple[float, qblox_scheduler.operations.operation.Operation]], current_idx: int) -> tuple[float, qblox_scheduler.operations.operation.Operation] | Literal[False]

.. py:function:: _raise_if_pulses_overlap_on_same_port_clock(abs_time_a: float, op_a: qblox_scheduler.operations.operation.Operation, abs_time_b: float, op_b: qblox_scheduler.operations.operation.Operation) -> None

   Raise an error if any pulse operations overlap on the same port-clock.

   A pulse here means a waveform or a voltage offset.


.. py:function:: _get_pulse_start_ends(abs_time: float, operation: qblox_scheduler.operations.operation.Operation) -> dict[str, tuple[float, float]]

.. py:function:: _operation_end(abs_time_and_operation: tuple[float, qblox_scheduler.operations.operation.Operation]) -> float

