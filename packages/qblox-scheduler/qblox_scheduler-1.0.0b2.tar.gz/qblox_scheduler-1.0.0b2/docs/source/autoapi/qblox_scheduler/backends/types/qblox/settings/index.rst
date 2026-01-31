settings
========

.. py:module:: qblox_scheduler.backends.types.qblox.settings 

.. autoapi-nested-parse::

   Python dataclasses for compilation to Qblox hardware.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.qblox.settings.LOSettings
   qblox_scheduler.backends.types.qblox.settings.DistortionSettings
   qblox_scheduler.backends.types.qblox.settings.ExternalTriggerSyncSettings
   qblox_scheduler.backends.types.qblox.settings.ClusterSettings
   qblox_scheduler.backends.types.qblox.settings.BaseModuleSettings
   qblox_scheduler.backends.types.qblox.settings.AnalogModuleSettings
   qblox_scheduler.backends.types.qblox.settings.BasebandModuleSettings
   qblox_scheduler.backends.types.qblox.settings.RFModuleSettings
   qblox_scheduler.backends.types.qblox.settings.TimetagModuleSettings
   qblox_scheduler.backends.types.qblox.settings.DCModuleSettings
   qblox_scheduler.backends.types.qblox.settings.ThresholdedAcqTriggerReadSettings
   qblox_scheduler.backends.types.qblox.settings.SequencerSettings
   qblox_scheduler.backends.types.qblox.settings.AnalogSequencerSettings
   qblox_scheduler.backends.types.qblox.settings.TimetagSequencerSettings




.. py:class:: LOSettings

   Bases: :py:obj:`dataclasses_json.DataClassJsonMixin`


   Dataclass containing all the settings for a generic LO instrument.


   .. py:attribute:: power
      :type:  dict[str, float]

      Power of the LO source.


   .. py:attribute:: frequency
      :type:  dict[str, Optional[float]]

      The frequency to set the LO to.


.. py:class:: DistortionSettings

   Bases: :py:obj:`dataclasses_json.DataClassJsonMixin`


   Distortion correction settings for all Qblox modules.


   .. py:attribute:: exp0
      :type:  qblox_scheduler.backends.types.qblox.filters.QbloxRealTimeFilter

      The exponential overshoot correction 1 filter.


   .. py:attribute:: exp1
      :type:  qblox_scheduler.backends.types.qblox.filters.QbloxRealTimeFilter

      The exponential overshoot correction 2 filter.


   .. py:attribute:: exp2
      :type:  qblox_scheduler.backends.types.qblox.filters.QbloxRealTimeFilter

      The exponential overshoot correction 3 filter.


   .. py:attribute:: exp3
      :type:  qblox_scheduler.backends.types.qblox.filters.QbloxRealTimeFilter

      The exponential overshoot correction 4 filter.


   .. py:attribute:: fir
      :type:  qblox_scheduler.backends.types.qblox.filters.QbloxRealTimeFilter

      The FIR filter.


.. py:class:: ExternalTriggerSyncSettings

   Bases: :py:obj:`dataclasses_json.DataClassJsonMixin`


   Settings for synchronizing a cluster on an external trigger.


   .. py:attribute:: slot
      :type:  int

      Slot of the module receiving the incoming trigger (can be the CMM).


   .. py:attribute:: channel
      :type:  int

      Channel that receives the incoming trigger.

      Note that this is the channel number on the front panel. When using a CMM, this should be 1.


   .. py:attribute:: input_threshold
      :type:  Optional[float]
      :value: None


      If a QTM module is used, this setting specifies the input threshold.

      If a CMM is used instead, this setting is ignored and the trigger signal must be TTL (>2.4 V).


   .. py:attribute:: trigger_timestamp
      :type:  float
      :value: 0


      What time the cluster should be set to upon receiving the trigger.


   .. py:attribute:: timeout
      :type:  float
      :value: 1


      The time the cluster will wait for the trigger to arrive.


   .. py:attribute:: format
      :type:  str
      :value: 's'


      The time unit for the ``trigger_timestamp`` and ``timeout`` parameters.


   .. py:attribute:: edge_polarity
      :type:  qblox_instruments.qcodes_drivers.time.Polarity

      The edge polarity to trigger on.


   .. py:attribute:: sync_to_ref_clock
      :type:  bool
      :value: False


      If True, synchronizes to the next internal 10 MHz reference clock tick, by default False.


.. py:class:: ClusterSettings

   Bases: :py:obj:`dataclasses_json.DataClassJsonMixin`


   Shared settings between all the Qblox modules.


   .. py:attribute:: reference_source
      :type:  Literal['internal', 'external']


   .. py:attribute:: sync_on_external_trigger
      :type:  Optional[ExternalTriggerSyncSettings]
      :value: None



   .. py:method:: extract_settings_from_mapping(mapping: qblox_scheduler.backends.qblox_backend._ClusterCompilationConfig) -> ClusterSettings
      :classmethod:


      Factory method that takes all the settings defined in the mapping and generates
      an instance of this class.

      :param mapping: The mapping dict to extract the settings from
      :param \*\*kwargs: Additional keyword arguments passed to the constructor. Can be used to
                         override parts of the mapping dict.



.. py:class:: BaseModuleSettings

   Bases: :py:obj:`dataclasses_json.DataClassJsonMixin`


   Shared settings between all the Qblox modules.


   .. py:method:: extract_settings_from_mapping(mapping: qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig, **kwargs) -> _ModuleSettingsT
      :classmethod:


      Factory method that takes all the settings defined in the mapping and generates
      an instance of this class.

      :param mapping: The mapping dict to extract the settings from
      :param \*\*kwargs: Additional keyword arguments passed to the constructor. Can be used to
                         override parts of the mapping dict.



.. py:class:: AnalogModuleSettings

   Bases: :py:obj:`BaseModuleSettings`


   Shared settings between all QCM/QRM modules.


   .. py:attribute:: offset_ch0_path_I
      :type:  Optional[float]
      :value: None


      The DC offset on the path_I of channel 0.


   .. py:attribute:: offset_ch0_path_Q
      :type:  Optional[float]
      :value: None


      The DC offset on the path_Q of channel 0.


   .. py:attribute:: offset_ch1_path_I
      :type:  Optional[float]
      :value: None


      The DC offset on path_I of channel 1.


   .. py:attribute:: offset_ch1_path_Q
      :type:  Optional[float]
      :value: None


      The DC offset on path_Q of channel 1.


   .. py:attribute:: out0_lo_freq_cal_type_default
      :type:  qblox_scheduler.backends.qblox.enums.LoCalEnum

      Setting that controls whether the mixer of channel 0 is calibrated upon changing the
      LO and/or intermodulation frequency.


   .. py:attribute:: out1_lo_freq_cal_type_default
      :type:  qblox_scheduler.backends.qblox.enums.LoCalEnum

      Setting that controls whether the mixer of channel 1 is calibrated upon changing the
      LO and/or intermodulation frequency.


   .. py:attribute:: in0_gain
      :type:  Optional[int]
      :value: None


      The gain of input 0.


   .. py:attribute:: in1_gain
      :type:  Optional[int]
      :value: None


      The gain of input 1.


   .. py:attribute:: distortion_corrections
      :type:  list[DistortionSettings]

      Distortion correction settings.


.. py:class:: BasebandModuleSettings

   Bases: :py:obj:`AnalogModuleSettings`


   Settings for a baseband module.

   Class exists to ensure that the cluster baseband modules don't need special
   treatment in the rest of the code.


.. py:class:: RFModuleSettings

   Bases: :py:obj:`AnalogModuleSettings`


   Global settings for the module to be set in the InstrumentCoordinator component.
   This is kept separate from the settings that can be set on a per-sequencer basis,
   which are specified in :class:`~.AnalogSequencerSettings`.


   .. py:attribute:: lo0_freq
      :type:  Optional[float]
      :value: None


      The frequency of Output 0 (O1) LO. If left `None`, the parameter will not be set.


   .. py:attribute:: lo1_freq
      :type:  Optional[float]
      :value: None


      The frequency of Output 1 (O2) LO. If left `None`, the parameter will not be set.


   .. py:attribute:: lo2_freq
      :type:  Optional[float]
      :value: None


      The frequency of Output 2 (O3) LO. If left `None`, the parameter will not be set.


   .. py:attribute:: lo3_freq
      :type:  Optional[float]
      :value: None


      The frequency of Output 3 (O4) LO. If left `None`, the parameter will not be set.


   .. py:attribute:: lo4_freq
      :type:  Optional[float]
      :value: None


      The frequency of Output 4 (O5) LO. If left `None`, the parameter will not be set.


   .. py:attribute:: lo5_freq
      :type:  Optional[float]
      :value: None


      The frequency of Output 5 (O6) LO. If left `None`, the parameter will not be set.


   .. py:attribute:: out0_att
      :type:  Optional[int]
      :value: None


      The attenuation of Output 0 (O1).


   .. py:attribute:: out1_att
      :type:  Optional[int]
      :value: None


      The attenuation of Output 1 (O2).


   .. py:attribute:: out2_att
      :type:  Optional[int]
      :value: None


      The attenuation of Output 2 (O3).


   .. py:attribute:: out3_att
      :type:  Optional[int]
      :value: None


      The attenuation of Output 3 (O4).


   .. py:attribute:: out4_att
      :type:  Optional[int]
      :value: None


      The attenuation of Output 4 (O5).


   .. py:attribute:: out5_att
      :type:  Optional[int]
      :value: None


      The attenuation of Output 5 (O6).


   .. py:attribute:: in0_att
      :type:  Optional[int]
      :value: None


      The attenuation of Input 0 (I1).


   .. py:attribute:: in1_att
      :type:  Optional[int]
      :value: None


      The attenuation of Input 1 (I2).


   .. py:method:: extract_settings_from_mapping(mapping: qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig, **kwargs: Optional[dict]) -> RFModuleSettings
      :classmethod:


      Factory method that takes all the settings defined in the mapping and generates
      an :class:`~.RFModuleSettings` object from it.

      :param mapping: The compiler config to extract the settings from
      :param \*\*kwargs: Additional keyword arguments passed to the constructor. Can be used to
                         override parts of the mapping dict.



.. py:class:: TimetagModuleSettings

   Bases: :py:obj:`BaseModuleSettings`


   Global settings for the module to be set in the InstrumentCoordinator component.
   This is kept separate from the settings that can be set on a per-sequencer basis,
   which are specified in :class:`~.TimetagSequencerSettings`.


.. py:class:: DCModuleSettings

   Bases: :py:obj:`BaseModuleSettings`


   Settings for a DC module (QSM).


   .. py:attribute:: NUM_CHANNELS
      :type:  ClassVar[int]
      :value: 8


      Number of IO channels available on a QSM.


   .. py:attribute:: source_mode
      :type:  dict[int, Literal['v_source', 'i_source', 'ground', 'open']]

      Sourcing behavior of the channel, either outputting a controlled voltage or current.


   .. py:attribute:: measure_mode
      :type:  dict[int, Literal['automatic', 'coarse', 'fine_nanoampere', 'fine_picoampere']]

      Range coarse/fine for the measurement precision.


   .. py:attribute:: ramping_rate
      :type:  dict[int, float]

      Ramp rate to ramp_rate value in volt/s. The different levels allow shortcuts
      to avoid unwanted communications with the instrument.


   .. py:attribute:: integration_time
      :type:  dict[int, float]

      Integration time in seconds. The different levels allow shortcuts
      to avoid unwanted communications with the instrument.


   .. py:attribute:: safe_voltage_range
      :type:  dict[int, tuple[float, float]]

      Voltage limits (-min, +max) to protect the device against accidental overvolting.


   .. py:method:: extract_settings_from_mapping(mapping: qblox_scheduler.backends.qblox_backend._ClusterModuleCompilationConfig, **kwargs) -> typing_extensions.Self
      :classmethod:


      Override the base factory method to extract the settings from QSM-like format.

      Example: ``{"source_mode": {"cluster0.module1": "ground"}}``

      At this point each hardware option should only have paths corresponding to the module
      being loaded. If the path doesn't contain a channel name, we assume the setting
      needs to be applied to all IO channels and distribute it as such.



.. py:class:: ThresholdedAcqTriggerReadSettings

   Bases: :py:obj:`dataclasses_json.DataClassJsonMixin`


   Settings for reading from a trigger address.


   .. py:attribute:: thresholded_acq_trigger_invert
      :type:  bool
      :value: False


      If true, inverts the comparison result that is read from the trigger network address
      counter.


   .. py:attribute:: thresholded_acq_trigger_count
      :type:  Optional[int]
      :value: None


      Sets the threshold for the counter on the specified trigger address.


.. py:class:: SequencerSettings

   Bases: :py:obj:`dataclasses_json.DataClassJsonMixin`


   Sequencer level settings.

   In the Qblox driver these settings are typically recognized by parameter names of
   the form ``"{module}.sequencer{index}.{setting}"`` (for allowed values see
   `Cluster QCoDeS parameters
   <https://docs.qblox.com/en/main/api_reference/sequencer.html#cluster-qcodes-parameters>`__).
   These settings are set once and will remain unchanged after, meaning that these
   correspond to the "slow" QCoDeS parameters and not settings that are changed
   dynamically by the sequencer.

   These settings are mostly defined in the hardware configuration under each
   port-clock key combination or in some cases through the device configuration
   (e.g. parameters related to thresholded acquisition).


   .. py:attribute:: sync_en
      :type:  bool

      Enables party-line synchronization.


   .. py:attribute:: channel_name
      :type:  str

      Specifies the channel identifier of the hardware config (e.g. `complex_output_0`).


   .. py:attribute:: channel_name_measure
      :type:  Union[list[str], None]

      Extra channel name necessary to define a `Measure` operation.


   .. py:attribute:: connected_output_indices
      :type:  tuple[int, Ellipsis]

      Specifies the indices of the outputs this sequencer produces waveforms for.


   .. py:attribute:: connected_input_indices
      :type:  tuple[int, Ellipsis]

      Specifies the indices of the inputs this sequencer collects data for.


   .. py:attribute:: sequence
      :type:  Optional[dict[str, Any]]
      :value: None


      JSON compatible dictionary holding the waveforms and program for the
      sequencer.


   .. py:attribute:: seq_fn
      :type:  Optional[str]
      :value: None


      Filename of JSON file containing a dump of the waveforms and program.


   .. py:attribute:: thresholded_acq_trigger_write_en
      :type:  Optional[bool]
      :value: None


      Enables mapping of thresholded acquisition results to the trigger network.


   .. py:attribute:: thresholded_acq_trigger_write_address
      :type:  Optional[int]
      :value: None


      The trigger address that thresholded acquisition results are written to.


   .. py:attribute:: thresholded_acq_trigger_write_invert
      :type:  bool
      :value: False


      If True, inverts the trigger before writing to the trigger network.


   .. py:attribute:: thresholded_acq_trigger_read_settings
      :type:  dict[int, ThresholdedAcqTriggerReadSettings]

      Settings for reading from a trigger address.


   .. py:method:: initialize_from_compilation_config(sequencer_cfg: qblox_scheduler.backends.qblox_backend._SequencerCompilationConfig, connected_output_indices: tuple[int, Ellipsis], connected_input_indices: tuple[int, Ellipsis], default_nco_en: bool) -> SequencerSettings
      :classmethod:


      Instantiates an instance of this class, with initial parameters determined from
      the sequencer compilation config.

      :param sequencer_cfg: The sequencer compilation_config.
      :param connected_output_indices: Specifies the indices of the outputs this sequencer produces waveforms for.
      :param connected_input_indices: Specifies the indices of the inputs this sequencer collects data for.
      :param default_nco_en: Specifies the default setting to enable nco.

      :returns: : SequencerSettings
                    A SequencerSettings instance with initial values.




.. py:class:: AnalogSequencerSettings

   Bases: :py:obj:`SequencerSettings`


   Sequencer level settings.

   In the Qblox driver these settings are typically recognized by parameter names of
   the form ``"{module}.sequencer{index}.{setting}"`` (for allowed values see
   `Cluster QCoDeS parameters
   <https://docs.qblox.com/en/master/api_reference/sequencer.html#cluster-qcodes-parameters>`__).
   These settings are set once and will remain unchanged after, meaning that these
   correspond to the "slow" QCoDeS parameters and not settings that are changed
   dynamically by the sequencer.

   These settings are mostly defined in the hardware configuration under each
   port-clock key combination or in some cases through the device configuration
   (e.g. parameters related to thresholded acquisition).


   .. py:attribute:: nco_en
      :type:  bool
      :value: False


      Specifies whether the NCO will be used or not.


   .. py:attribute:: init_offset_awg_path_I
      :type:  float
      :value: 0.0


      Specifies what value the sequencer offset for AWG path_I will be reset to
      before the start of the experiment.


   .. py:attribute:: init_offset_awg_path_Q
      :type:  float
      :value: 0.0


      Specifies what value the sequencer offset for AWG path_Q will be reset to
      before the start of the experiment.


   .. py:attribute:: init_gain_awg_path_I
      :type:  float
      :value: 1.0


      Specifies what value the sequencer gain for AWG path_I will be reset to
      before the start of the experiment.


   .. py:attribute:: init_gain_awg_path_Q
      :type:  float
      :value: 1.0


      Specifies what value the sequencer gain for AWG path_Q will be reset to
      before the start of the experiment.


   .. py:attribute:: modulation_freq
      :type:  Optional[float]
      :value: None


      Specifies the frequency of the modulation.


   .. py:attribute:: mixer_corr_phase_offset_degree
      :type:  Optional[float]
      :value: None


      The phase shift to apply between the I and Q channels, to correct for quadrature
      errors.


   .. py:attribute:: mixer_corr_gain_ratio
      :type:  Optional[float]
      :value: None


      The gain ratio to apply in order to correct for imbalances between the I and Q
      paths of the mixer.


   .. py:attribute:: auto_sideband_cal
      :type:  qblox_scheduler.backends.qblox.enums.SidebandCalEnum

      Setting that controls whether the mixer is calibrated upon changing the
      intermodulation frequency.


   .. py:attribute:: integration_length_acq
      :type:  Optional[int]
      :value: None


      Integration length for acquisitions. Must be a multiple of 4 ns.


   .. py:attribute:: thresholded_acq_threshold
      :type:  Optional[float]
      :value: None


      The sequencer discretization threshold for discretizing the phase rotation result.


   .. py:attribute:: thresholded_acq_rotation
      :type:  Optional[float]
      :value: None


      The sequencer integration result phase rotation in degrees.


   .. py:attribute:: ttl_acq_input_select
      :type:  Optional[int]
      :value: None


      Selects the input used to compare against
      the threshold value in the TTL trigger acquisition path.


   .. py:attribute:: ttl_acq_threshold
      :type:  Optional[float]
      :value: None


      For QRM modules only, sets the threshold value with which to compare the input ADC
      values of the selected input path.


   .. py:attribute:: ttl_acq_auto_bin_incr_en
      :type:  Optional[bool]
      :value: None


      Selects if the bin index is automatically incremented when acquiring multiple triggers.


   .. py:method:: initialize_from_compilation_config(sequencer_cfg: qblox_scheduler.backends.qblox_backend._SequencerCompilationConfig, connected_output_indices: tuple[int, Ellipsis], connected_input_indices: tuple[int, Ellipsis], default_nco_en: bool) -> AnalogSequencerSettings
      :classmethod:


      Instantiates an instance of this class, with initial parameters determined from
      the sequencer compilation config.

      :param sequencer_cfg: The sequencer compilation_config.
      :param connected_output_indices: Specifies the indices of the outputs this sequencer produces waveforms for.
      :param connected_input_indices: Specifies the indices of the inputs this sequencer collects data for.
      :param default_nco_en: Specifies the default setting to enable nco.

      :returns: : AnalogSequencerSettings
                    A AnalogSequencerSettings instance with initial values.




.. py:class:: TimetagSequencerSettings

   Bases: :py:obj:`SequencerSettings`


   Sequencer level settings.

   In the Qblox driver these settings are typically recognized by parameter names of
   the form ``"{module}.sequencer{index}.{setting}"`` (for allowed values see
   `Cluster QCoDeS parameters
   <https://docs.qblox.com/en/master/api_reference/sequencer.html#cluster-qcodes-parameters>`__).
   These settings are set once and will remain unchanged after, meaning that these
   correspond to the "slow" QCoDeS parameters and not settings that are changed
   dynamically by the sequencer.

   These settings are mostly defined in the hardware configuration under each
   port-clock key combination or in some cases through the device configuration
   (e.g. parameters related to thresholded acquisition).


   .. py:attribute:: analog_threshold
      :type:  Optional[float]
      :value: None


      The settings that determine when an analog voltage is counted as a pulse.


   .. py:attribute:: time_source
      :type:  Optional[qblox_scheduler.enums.TimeSource]
      :value: None


      Selects the timetag data source for timetag acquisitions.


   .. py:attribute:: time_ref
      :type:  Optional[qblox_scheduler.enums.TimeRef]
      :value: None


      Selects the time reference that the timetag is recorded in relation to.


   .. py:attribute:: time_ref_channel
      :type:  Optional[int]
      :value: None


      If using TimeRef.PORT, this setting specifies the channel index (on the same module) belonging
      to that port.


   .. py:attribute:: scope_trace_type
      :type:  Optional[qblox_scheduler.backends.qblox.enums.TimetagTraceType]
      :value: None


      Set to True if the program on this sequencer contains a scope/trace acquisition.


   .. py:attribute:: trace_acq_duration
      :type:  Optional[int]
      :value: None


      Duration of the trace acquisition (if any) done with this sequencer.


   .. py:attribute:: thresholded_acq_trigger_write_address_low
      :type:  int
      :value: 0



   .. py:attribute:: thresholded_acq_trigger_write_address_mid
      :type:  int
      :value: 0



   .. py:attribute:: thresholded_acq_trigger_write_address_high
      :type:  int
      :value: 0



   .. py:attribute:: thresholded_acq_trigger_write_address_invalid
      :type:  int
      :value: 0



   .. py:attribute:: thresholded_acq_trigger_write_threshold_low
      :type:  Optional[int]
      :value: None


      Optional threshold value used for the upd_thres Q1ASM instruction if ThresholdedTriggerCount is
      scheduled.


   .. py:attribute:: thresholded_acq_trigger_write_threshold_high
      :type:  Optional[int]
      :value: None


      Optional threshold value used for the upd_thres Q1ASM instruction if ThresholdedTriggerCount is
      scheduled.


   .. py:method:: _validate_io_indices_no_channel_map() -> None

      There is no channel map in the QTM yet, so there can be only one connected
      index: either input or output.



   .. py:method:: initialize_from_compilation_config(sequencer_cfg: qblox_scheduler.backends.qblox_backend._SequencerCompilationConfig, connected_output_indices: tuple[int, Ellipsis], connected_input_indices: tuple[int, Ellipsis], default_nco_en: bool) -> TimetagSequencerSettings
      :classmethod:


      Instantiates an instance of this class, with initial parameters determined from
      the sequencer compilation config.

      :param sequencer_cfg: The sequencer compilation config.
      :param connected_output_indices: Specifies the indices of the outputs this sequencer produces waveforms for.
      :param connected_input_indices: Specifies the indices of the inputs this sequencer collects data for.
      :param default_nco_en: Specifies the indices of the default setting to enable nco.
                             Not applicable for timetag sequencer.

      :returns: : SequencerSettings
                    A SequencerSettings instance with initial values.




