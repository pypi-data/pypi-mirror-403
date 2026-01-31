qblox
=====

.. py:module:: qblox_scheduler.instrument_coordinator.components.qblox 

.. autoapi-nested-parse::

   Module containing Qblox InstrumentCoordinator Components.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.instrument_coordinator.components.qblox.ComponentTypeProperties
   qblox_scheduler.instrument_coordinator.components.qblox._StaticHardwareProperties
   qblox_scheduler.instrument_coordinator.components.qblox._StaticAnalogModuleProperties
   qblox_scheduler.instrument_coordinator.components.qblox._StaticTimetagModuleProperties
   qblox_scheduler.instrument_coordinator.components.qblox._StaticDCModuleProperties
   qblox_scheduler.instrument_coordinator.components.qblox._ModuleComponentBase
   qblox_scheduler.instrument_coordinator.components.qblox._AnalogModuleComponent
   qblox_scheduler.instrument_coordinator.components.qblox._QCMComponent
   qblox_scheduler.instrument_coordinator.components.qblox._AnalogReadoutComponent
   qblox_scheduler.instrument_coordinator.components.qblox._QRMComponent
   qblox_scheduler.instrument_coordinator.components.qblox._RFComponent
   qblox_scheduler.instrument_coordinator.components.qblox._QCMRFComponent
   qblox_scheduler.instrument_coordinator.components.qblox._QRMRFComponent
   qblox_scheduler.instrument_coordinator.components.qblox._QRCComponent
   qblox_scheduler.instrument_coordinator.components.qblox._QTMComponent
   qblox_scheduler.instrument_coordinator.components.qblox._QSMComponent
   qblox_scheduler.instrument_coordinator.components.qblox._AcquisitionManagerBase
   qblox_scheduler.instrument_coordinator.components.qblox._QRMAcquisitionManager
   qblox_scheduler.instrument_coordinator.components.qblox._QTMAcquisitionManager
   qblox_scheduler.instrument_coordinator.components.qblox.ClusterComponent



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.instrument_coordinator.components.qblox._get_instrument_ip
   qblox_scheduler.instrument_coordinator.components.qblox._get_configuration_manager
   qblox_scheduler.instrument_coordinator.components.qblox._download_log



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.instrument_coordinator.components.qblox.logger
   qblox_scheduler.instrument_coordinator.components.qblox._QCM_BASEBAND_PROPERTIES
   qblox_scheduler.instrument_coordinator.components.qblox._QRM_BASEBAND_PROPERTIES
   qblox_scheduler.instrument_coordinator.components.qblox._QCM_RF_PROPERTIES
   qblox_scheduler.instrument_coordinator.components.qblox._QRM_RF_PROPERTIES
   qblox_scheduler.instrument_coordinator.components.qblox._QRC_PROPERTIES
   qblox_scheduler.instrument_coordinator.components.qblox._QTM_PROPERTIES
   qblox_scheduler.instrument_coordinator.components.qblox._QSM_PROPERTIES
   qblox_scheduler.instrument_coordinator.components.qblox._HardwarePropertiesT_co
   qblox_scheduler.instrument_coordinator.components.qblox._ReadoutModuleComponentT


.. py:class:: ComponentTypeProperties

   Bases: :py:obj:`tuple`


   .. py:attribute:: is_qcm_type


   .. py:attribute:: is_qrm_type


   .. py:attribute:: is_rf_type


   .. py:attribute:: is_qtm_type


   .. py:attribute:: is_qrc_type


   .. py:attribute:: is_qsm_type


.. py:data:: logger

.. py:class:: _StaticHardwareProperties

   Dataclass for storing configuration differences across Qblox devices.


   .. py:attribute:: settings_type
      :type:  type[qblox_scheduler.backends.types.qblox.BaseModuleSettings]

      The settings dataclass to use that the hardware needs to configure to.


   .. py:attribute:: number_of_sequencers
      :type:  int

      The number of sequencers the hardware has available.


   .. py:attribute:: number_of_output_channels
      :type:  int

      The number of physical output channels that can be used.


   .. py:attribute:: number_of_input_channels
      :type:  int

      The number of physical input channels that can be used.


   .. py:attribute:: number_of_scope_acq_channels
      :type:  int

      The number of scope acquisition channels.


.. py:class:: _StaticAnalogModuleProperties

   Bases: :py:obj:`_StaticHardwareProperties`


   Dataclass for storing configuration differences across Qblox devices.


   .. py:attribute:: settings_type
      :type:  type[qblox_scheduler.backends.types.qblox.AnalogModuleSettings]

      The settings dataclass to use that the hardware needs to configure to.


   .. py:attribute:: has_internal_lo
      :type:  bool

      Specifies if an internal lo source is available.


.. py:class:: _StaticTimetagModuleProperties

   Bases: :py:obj:`_StaticHardwareProperties`


   Dataclass for storing configuration differences across Qblox devices.


   .. py:attribute:: settings_type
      :type:  type[qblox_scheduler.backends.types.qblox.TimetagModuleSettings]

      The settings dataclass to use that the hardware needs to configure to.


.. py:class:: _StaticDCModuleProperties

   Bases: :py:obj:`_StaticHardwareProperties`


   Dataclass for storing configuration differences across Qblox devices.


   .. py:attribute:: settings_type
      :type:  type[qblox_scheduler.backends.types.qblox.settings.DCModuleSettings]

      The settings dataclass to use that the hardware needs to configure to.


.. py:data:: _QCM_BASEBAND_PROPERTIES

.. py:data:: _QRM_BASEBAND_PROPERTIES

.. py:data:: _QCM_RF_PROPERTIES

.. py:data:: _QRM_RF_PROPERTIES

.. py:data:: _QRC_PROPERTIES

.. py:data:: _QTM_PROPERTIES

.. py:data:: _QSM_PROPERTIES

.. py:data:: _HardwarePropertiesT_co

.. py:class:: _ModuleComponentBase(instrument: qblox_instruments.qcodes_drivers.module.Module)

   Bases: :py:obj:`qblox_scheduler.instrument_coordinator.components.base.InstrumentCoordinatorComponentBase`, :py:obj:`Generic`\ [\ :py:obj:`_HardwarePropertiesT_co`\ ]


   Qblox InstrumentCoordinator component base class.


   .. py:attribute:: _hardware_properties
      :type:  _HardwarePropertiesT_co


   .. py:attribute:: _instrument_module


   .. py:attribute:: _seq_name_to_idx_map


   .. py:attribute:: _program


   .. py:attribute:: _nco_frequency_changed
      :type:  dict[int, bool]

      Private attribute for automatic mixer calibration. The keys are sequencer
      indices. The `prepare` method resets this to an empty dictionary.


   .. py:property:: instrument
      :type: qblox_instruments.qcodes_drivers.module.Module


      Returns a reference to the module instrument.


   .. py:method:: _set_parameter(instrument: qcodes.instrument.instrument_base.InstrumentBase, parameter_name: str, val: Any) -> None

      Set the parameter directly or using the lazy set.

      :param instrument: The instrument or instrument channel that holds the parameter to set,
                         e.g. `self.instrument` or `self.instrument[f"sequencer{idx}"]`.
      :param parameter_name: The name of the parameter to set.
      :param val: The new value of the parameter.



   .. py:property:: is_running
      :type: bool


      Finds if any of the sequencers is currently running.

      :returns: :
                    True if any of the sequencers reports the `SequencerStates.RUNNING` status.


   .. py:method:: wait_done(timeout_sec: int = 10) -> None

      Blocks the instrument until all the sequencers are done running.

      :param timeout_sec: The timeout in seconds. N.B. the instrument takes the timeout in minutes
                          (int), therefore it is rounded down to whole minutes with a minimum of 1.



   .. py:method:: get_hardware_log(compiled_schedule: qblox_scheduler.schedules.schedule.CompiledSchedule) -> dict | None

      Retrieve the hardware log of the Qblox instrument associated to this component.

      This log does not include the instrument serial number and firmware version.

      :param compiled_schedule: Compiled schedule to check if this component is referenced in.

      :returns: :
                    A dict containing the hardware log of the Qblox instrument, in case the
                    component was referenced; else None.




   .. py:method:: prepare(program: dict[str, dict], acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, repetitions: int) -> None

      Store program containing sequencer settings.



   .. py:method:: disable_sync() -> None

      Disable sync for all sequencers.



   .. py:method:: stop() -> None

      Stops all execution.



   .. py:method:: _configure_global_settings(settings: qblox_scheduler.backends.types.qblox.BaseModuleSettings) -> None
      :abstractmethod:


      Configures all settings that are set globally for the whole instrument.

      :param settings: The settings to configure it to.



   .. py:method:: _configure_sequencer_settings(seq_idx: int, settings: qblox_scheduler.backends.types.qblox.SequencerSettings) -> None

      Configures all sequencer-specific settings.

      :param seq_idx: Index of the sequencer to configure.
      :param settings: The settings to configure it to.



   .. py:method:: arm_all_sequencers_in_program() -> None

      Arm all the sequencers that are part of the program.



   .. py:method:: start() -> None

      Clear data, arm sequencers and start sequencers.



   .. py:method:: _start_armed_sequencers() -> None

      Start execution of the schedule: start armed sequencers.



   .. py:method:: clear_data() -> None

      Clears remaining data on the module. Module type specific function.



.. py:class:: _AnalogModuleComponent(instrument: qblox_instruments.qcodes_drivers.module.Module)

   Bases: :py:obj:`_ModuleComponentBase`


   Qblox InstrumentCoordinator component base class.


   .. py:attribute:: _hardware_properties
      :type:  _StaticAnalogModuleProperties


   .. py:method:: _configure_global_settings(settings: qblox_scheduler.backends.types.qblox.BaseModuleSettings) -> None
      :abstractmethod:


      Configures all settings that are set globally for the whole instrument.

      :param settings: The settings to configure it to.



   .. py:method:: _configure_sequencer_settings(seq_idx: int, settings: qblox_scheduler.backends.types.qblox.SequencerSettings) -> None

      Configures all sequencer-specific settings.

      :param seq_idx: Index of the sequencer to configure.
      :param settings: The settings to configure it to.



   .. py:method:: _determine_channel_map_parameters(settings: qblox_scheduler.backends.types.qblox.AnalogSequencerSettings) -> dict[str, str]

      Returns a dictionary with the channel map parameters for this module.



   .. py:method:: _determine_output_channel_map_parameters(settings: qblox_scheduler.backends.types.qblox.AnalogSequencerSettings, channel_map_parameters: dict[str, str]) -> dict[str, str]

      Adds the outputs to the channel map parameters dict.



   .. py:method:: _configure_nco_mixer_calibration(seq_idx: int, settings: qblox_scheduler.backends.types.qblox.AnalogSequencerSettings) -> None


.. py:class:: _QCMComponent(instrument: qblox_instruments.qcodes_drivers.module.Module)

   Bases: :py:obj:`_AnalogModuleComponent`


   QCM specific InstrumentCoordinator component.


   .. py:attribute:: _hardware_properties


   .. py:method:: retrieve_acquisition() -> None

      Retrieves the previous acquisition.

      :returns: :
                    QCM returns None since the QCM has no acquisition.




   .. py:method:: prepare(program: dict[str, dict], acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, repetitions: int) -> None

      Uploads the waveforms and programs to the sequencers.

      All the settings that are required are configured. Keep in mind that
      values set directly through the driver may be overridden (e.g. the
      offsets will be set according to the specified mixer calibration
      parameters).

      :param program: Program to upload to the sequencers.
                      Under the key :code:`"sequencer"` you specify the sequencer specific
                      options for each sequencer, e.g. :code:`"seq0"`.
                      For global settings, the options are under different keys, e.g. :code:`"settings"`.
      :param acq_channels_data: Acquisition channels data.
      :param repetitions: Repetitions of the schedule.



   .. py:method:: _configure_sequencer_settings(seq_idx: int, settings: qblox_scheduler.backends.types.qblox.SequencerSettings) -> None

      Configures all sequencer-specific settings.

      :param seq_idx: Index of the sequencer to configure.
      :param settings: The settings to configure it to.



   .. py:method:: _configure_global_settings(settings: qblox_scheduler.backends.types.qblox.BaseModuleSettings) -> None

      Configures all settings that are set globally for the whole instrument.

      :param settings: The settings to configure it to.



.. py:class:: _AnalogReadoutComponent(instrument: qblox_instruments.qcodes_drivers.module.Module)

   Bases: :py:obj:`_AnalogModuleComponent`


   Qblox InstrumentCoordinator readout component base class.


   .. py:attribute:: _acquisition_manager
      :type:  _QRMAcquisitionManager | None
      :value: None


      Holds all the acquisition related logic.


   .. py:method:: retrieve_acquisition() -> xarray.Dataset | None

      Retrieves the latest acquisition results.

      :returns: :
                    The acquired data.




   .. py:method:: prepare(program: dict[str, dict], acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, repetitions: int) -> None

      Uploads the waveforms and programs to the sequencers.

      All the settings that are required are configured. Keep in mind that
      values set directly through the driver may be overridden (e.g. the
      offsets will be set according to the specified mixer calibration
      parameters).

      :param program: Program to upload to the sequencers.
                      Under the key :code:`"sequencer"` you specify the sequencer specific
                      options for each sequencer, e.g. :code:`"seq0"`.
                      For global settings, the options are under different keys, e.g. :code:`"settings"`.
      :param acq_channels_data: Acquisition channels data.
      :param repetitions: Repetitions of the schedule.



   .. py:method:: _configure_global_settings(settings: qblox_scheduler.backends.types.qblox.AnalogModuleSettings) -> None

      Configures all settings that are set globally for the whole instrument.

      :param settings: The settings to configure it to.



   .. py:method:: _configure_sequencer_settings(seq_idx: int, settings: qblox_scheduler.backends.types.qblox.SequencerSettings) -> None

      Configures all sequencer-specific settings.

      :param seq_idx: Index of the sequencer to configure.
      :param settings: The settings to configure it to.



   .. py:method:: _determine_channel_map_parameters(settings: qblox_scheduler.backends.types.qblox.AnalogSequencerSettings) -> dict[str, str]

      Returns a dictionary with the channel map parameters for this module.



   .. py:method:: _determine_input_channel_map_parameters(settings: qblox_scheduler.backends.types.qblox.AnalogSequencerSettings, channel_map_parameters: dict[str, str]) -> dict[str, str]

      Adds the inputs to the channel map parameters dict.



   .. py:method:: _determine_scope_mode_acquisition_sequencer_and_qblox_acq_index(acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, acq_hardware_mapping: dict[str, qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMapping]) -> tuple[int, int] | None

      Finds the sequencer and qblox_acq_index that performs the raw trace acquisition.

      Raises an error if multiple scope mode acquisitions are present per sequencer.
      Note, that compiler ensures there is at most one scope mode acquisition,
      however the user is able to freely modify the compiler program,
      so we make sure this requirement is still satisfied. See
      :func:`~qblox_scheduler.backends.qblox.analog.AnalogModuleCompiler._ensure_single_scope_mode_acquisition_sequencer`.

      :returns: :
                    The sequencer and qblox_acq_channel for the trace acquisition, if there is any,
                    otherwise None.




   .. py:method:: clear_data() -> None

      Clears remaining data on the module. Module type specific function.



.. py:class:: _QRMComponent(instrument: qblox_instruments.qcodes_drivers.module.Module)

   Bases: :py:obj:`_AnalogReadoutComponent`


   QRM specific InstrumentCoordinator component.


   .. py:attribute:: _hardware_properties


   .. py:method:: prepare(program: dict[str, dict], acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, repetitions: int) -> None

      Uploads the waveforms and programs to the sequencers.

      All the settings that are required are configured. Keep in mind that
      values set directly through the driver may be overridden (e.g. the
      offsets will be set according to the specified mixer calibration
      parameters).

      :param program: Program to upload to the sequencers.
                      Under the key :code:`"sequencer"` you specify the sequencer specific
                      options for each sequencer, e.g. :code:`"seq0"`.
                      For global settings, the options are under different keys, e.g. :code:`"settings"`.
      :param acq_channels_data: Acquisition channels data.
      :param repetitions: Repetitions of the schedule.



   .. py:method:: _configure_sequencer_settings(seq_idx: int, settings: qblox_scheduler.backends.types.qblox.SequencerSettings) -> None

      Configures all sequencer-specific settings.

      :param seq_idx: Index of the sequencer to configure.
      :param settings: The settings to configure it to.



.. py:class:: _RFComponent(instrument: qblox_instruments.qcodes_drivers.module.Module)

   Bases: :py:obj:`_AnalogModuleComponent`


   Mix-in for RF-module-specific InstrumentCoordinatorComponent behaviour.


   .. py:method:: prepare(program: dict[str, dict], acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, repetitions: int) -> None

      Uploads the waveforms and programs to the sequencers.

      Overrides the parent method to additionally set LO settings for automatic mixer
      calibration. This must be done _after_ all NCO frequencies have been set.

      :param program: Program to upload to the sequencers.
                      Under the key :code:`"sequencer"` you specify the sequencer specific
                      options for each sequencer, e.g. :code:`"seq0"`.
                      For global settings, the options are under different keys, e.g. :code:`"settings"`.
      :param acq_channels_data: Acquisition channels data.
      :param repetitions: Repetitions of the schedule.



   .. py:method:: _configure_sequencer_settings(seq_idx: int, settings: qblox_scheduler.backends.types.qblox.SequencerSettings) -> None

      Configures all sequencer-specific settings.

      :param seq_idx: Index of the sequencer to configure.
      :param settings: The settings to configure it to.



   .. py:method:: _determine_output_channel_map_parameters(settings: qblox_scheduler.backends.types.qblox.AnalogSequencerSettings, channel_map_parameters: dict[str, str]) -> dict[str, str]

      Adds the outputs to the channel map parameters dict.



   .. py:method:: _get_connected_lo_idx_for_sequencer(sequencer_settings: qblox_scheduler.backends.types.qblox.AnalogSequencerSettings) -> list[int]

      Looks at the connected _output_ ports of the sequencer (if any) to determine
      which LO this sequencer's output is coupled to.



   .. py:method:: _configure_lo_settings(settings: qblox_scheduler.backends.types.qblox.RFModuleSettings, lo_idx_to_connected_seq_idx: dict[int, list[int]]) -> None
      :abstractmethod:


      Configure the settings for LO frequency and automatic mixer calibration.



.. py:class:: _QCMRFComponent(instrument: qblox_instruments.qcodes_drivers.module.Module)

   Bases: :py:obj:`_RFComponent`, :py:obj:`_QCMComponent`


   QCM-RF specific InstrumentCoordinator component.


   .. py:attribute:: _hardware_properties


   .. py:method:: _configure_global_settings(settings: qblox_scheduler.backends.types.qblox.BaseModuleSettings) -> None

      Configures all settings that are set globally for the whole instrument.

      :param settings: The settings to configure it to.



   .. py:method:: _configure_lo_settings(settings: qblox_scheduler.backends.types.qblox.RFModuleSettings, lo_idx_to_connected_seq_idx: dict[int, list[int]]) -> None

      Configure the settings for LO frequency and automatic mixer calibration.



.. py:class:: _QRMRFComponent(instrument: qblox_instruments.qcodes_drivers.module.Module)

   Bases: :py:obj:`_RFComponent`, :py:obj:`_QRMComponent`


   QRM-RF specific InstrumentCoordinator component.


   .. py:attribute:: _hardware_properties


   .. py:method:: _configure_global_settings(settings: qblox_scheduler.backends.types.qblox.BaseModuleSettings) -> None

      Configures all settings that are set globally for the whole instrument.

      :param settings: The settings to configure it to.



   .. py:method:: _configure_lo_settings(settings: qblox_scheduler.backends.types.qblox.RFModuleSettings, lo_idx_to_connected_seq_idx: dict[int, list[int]]) -> None

      Configure the settings for LO frequency and automatic mixer calibration.



   .. py:method:: _determine_input_channel_map_parameters(settings: qblox_scheduler.backends.types.qblox.AnalogSequencerSettings, channel_map_parameters: dict[str, str]) -> dict[str, str]

      Adds the inputs to the channel map parameters dict.



.. py:class:: _QRCComponent(instrument: qblox_instruments.qcodes_drivers.module.Module)

   Bases: :py:obj:`_RFComponent`, :py:obj:`_AnalogReadoutComponent`


   QRC specific InstrumentCoordinator component.


   .. py:attribute:: _hardware_properties


   .. py:method:: prepare(program: dict[str, dict], acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, repetitions: int) -> None

      Uploads the waveforms and programs to the sequencers.

      All the settings that are required are configured. Keep in mind that
      values set directly through the driver may be overridden (e.g. the
      offsets will be set according to the specified mixer calibration
      parameters).

      :param program: Program to upload to the sequencers.
                      Under the key :code:`"sequencer"` you specify the sequencer specific
                      options for each sequencer, e.g. :code:`"seq0"`.
                      For global settings, the options are under different keys, e.g. :code:`"settings"`.
      :param acq_channels_data: Acquisition channels data.
      :param repetitions: Repetitions of the schedule.



   .. py:method:: _configure_global_settings(settings: qblox_scheduler.backends.types.qblox.BaseModuleSettings) -> None

      Configures all settings that are set globally for the whole instrument.

      :param settings: The settings to configure it to.



   .. py:method:: _configure_lo_settings(settings: qblox_scheduler.backends.types.qblox.RFModuleSettings, lo_idx_to_connected_seq_idx: dict[int, list[int]]) -> None

      Configure the settings for the frequency.



   .. py:method:: _determine_input_channel_map_parameters(settings: qblox_scheduler.backends.types.qblox.AnalogSequencerSettings, channel_map_parameters: dict[str, str]) -> dict[str, str]

      Adds the inputs to the channel map parameters dict.



   .. py:method:: _configure_sequencer_settings(seq_idx: int, settings: qblox_scheduler.backends.types.qblox.SequencerSettings) -> None

      Configures all sequencer-specific settings.

      :param seq_idx: Index of the sequencer to configure.
      :param settings: The settings to configure it to.



.. py:class:: _QTMComponent(instrument: qblox_instruments.qcodes_drivers.module.Module)

   Bases: :py:obj:`_ModuleComponentBase`


   QTM specific InstrumentCoordinator component.


   .. py:attribute:: _hardware_properties


   .. py:attribute:: _acquisition_manager
      :type:  _QTMAcquisitionManager | None
      :value: None


      Holds all the acquisition related logic.


   .. py:method:: retrieve_acquisition() -> xarray.Dataset | None

      Retrieves the latest acquisition results.

      :returns: :
                    The acquired data.




   .. py:method:: prepare(program: dict[str, dict], acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, repetitions: int) -> None

      Uploads the waveforms and programs to the sequencers.

      All the settings that are required are configured. Keep in mind that
      values set directly through the driver may be overridden (e.g. the
      offsets will be set according to the specified mixer calibration
      parameters).

      :param program: Program to upload to the sequencers.
                      Under the key :code:`"sequencer"` you specify the sequencer specific
                      options for each sequencer, e.g. :code:`"seq0"`.
                      For global settings, the options are under different keys, e.g. :code:`"settings"`.
      :param acq_channels_data: Acquisition channels data.
      :param repetitions: Repetitions of the schedule.



   .. py:method:: _configure_global_settings(settings: qblox_scheduler.backends.types.qblox.BaseModuleSettings) -> None

      Configures all settings that are set globally for the whole instrument.

      :param settings: The settings to configure it to.



   .. py:method:: _configure_io_channel_settings(seq_idx: int, settings: qblox_scheduler.backends.types.qblox.TimetagSequencerSettings) -> None

      Configures all io_channel-specific settings.

      :param seq_idx: Index of the sequencer to configure.
      :param settings: The settings to configure it to.



   .. py:method:: clear_data() -> None

      Clears remaining data on the module. Module type specific function.



.. py:class:: _QSMComponent(instrument: qblox_instruments.qcodes_drivers.module.Module)

   Bases: :py:obj:`_ModuleComponentBase`


   QSM specific InstrumentCoordinator component.


   .. py:attribute:: _hardware_properties


   .. py:property:: is_running
      :type: bool


      Do nothing, the QSM has no sequencers.


   .. py:method:: wait_done(timeout_sec: int = 10) -> None

      Do nothing, the QSM has no sequencers.



   .. py:method:: prepare(program: dict[str, dict], acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, repetitions: int) -> None

      Do nothing, the QSM has no sequencers.



   .. py:method:: disable_sync() -> None

      Do nothing, the QSM has no sequencers.



   .. py:method:: arm_all_sequencers_in_program() -> None

      Do nothing, the QSM has no sequencers.



   .. py:method:: start() -> None

      Do nothing, the QSM has no sequencers.



   .. py:method:: stop() -> None

      Do nothing, the QSM has no sequencers.



   .. py:method:: retrieve_acquisition() -> xarray.Dataset | None

      Gets and returns acquisition data.



   .. py:method:: _configure_global_settings(settings: qblox_scheduler.backends.types.qblox.settings.DCModuleSettings) -> None

      Configures all settings that are set globally for the whole instrument.

      :param settings: The settings to configure it to.



   .. py:method:: _configure_sequencer_settings(seq_idx: int, settings: qblox_scheduler.backends.types.qblox.SequencerSettings) -> None

      Do nothing, the QSM has no sequencers.



.. py:data:: _ReadoutModuleComponentT

.. py:class:: _AcquisitionManagerBase(parent: _ReadoutModuleComponentT, acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, acq_hardware_mapping: dict[str, qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMapping], acquisition_duration: dict[str, int], seq_name_to_idx_map: dict[str, int], repetitions: int)

   Bases: :py:obj:`abc.ABC`


   Utility class that handles the acquisitions performed with a module.

   An instance of this class is meant to exist only for a single prepare-start-
   retrieve_acquisition cycle to prevent stateful behavior.

   :param parent: Reference to the parent QRM IC component.
   :param acq_channels_data: Provides a summary of the used acquisition protocol, bin mode, acquisition channels,
                             acquisition indices per channel, and repetitions.
   :param acq_hardware_mapping: Acquisition hardware mapping.
   :param acquisition_duration: The duration of each acquisition for each sequencer.
   :param seq_name_to_idx_map: All available sequencer names to their ids in a dict.
   :param repetitions: How many times the schedule repeats.


   .. py:attribute:: parent


   .. py:attribute:: _acq_channels_data


   .. py:attribute:: _acq_hardware_mapping


   .. py:attribute:: _acq_duration


   .. py:attribute:: _seq_name_to_idx_map


   .. py:attribute:: _repetitions


   .. py:property:: instrument
      :type: qblox_instruments.qcodes_drivers.module.Module


      Returns the QRM driver from the parent IC component.


   .. py:method:: _check_bin_mode_compatible(acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, acq_hardware_mapping: dict[str, qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMapping]) -> None
      :staticmethod:

      :abstractmethod:



   .. py:method:: _protocol_to_acq_function_map(protocol: str) -> collections.abc.Callable
      :abstractmethod:


      Mapping from acquisition protocol name to the function that processes the raw
      acquisition data.



   .. py:method:: _protocol_to_bin_function(protocol: str) -> collections.abc.Callable
      :abstractmethod:



   .. py:method:: _retrieve_acquisition_fully_append_recursive(node: qblox_scheduler.backends.qblox.qblox_acq_index_manager.AcqFullyAppendLoopNode | qblox_scheduler.backends.qblox.qblox_acq_index_manager.FullyAppendAcqInfo, qblox_acq_bin: int, qblox_acq_index: int, hardware_retrieved_acquisitions: dict, acq_duration: int, acq_index_offset: int, total_average_repetitions: int) -> tuple[xarray.Dataset, int]


   .. py:method:: _retrieve_acquisition_fully_append(fully_append_mapping: qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionBinMappingFullyAppend, hardware_retrieved_acquisitions: dict, acq_duration: int) -> xarray.Dataset


   .. py:method:: retrieve_acquisition() -> xarray.Dataset

      Retrieves all the acquisition data in the correct format.

      :returns: :
                    The acquisitions with the protocols specified in the `acquisition_metadata`.
                    Each `xarray.DataArray` in the `xarray.Dataset` corresponds to one `acq_channel`.
                    The ``acq_channel`` is the name of each `xarray.DataArray` in the `xarray.Dataset`.
                    Each `xarray.DataArray` is a two-dimensional array, with ``acq_index`` and
                    Each `xarray.DataArray` is a two-dimensional array,
                    with ``acq_index`` and ``repetition`` as dimensions.




   .. py:method:: delete_acquisition_data() -> None

      Delete acquisition data from sequencers that have associated hardware acquisition mapping.

      To be called before starting the sequencers, so that old data does not get retrieved more
      than once.



   .. py:method:: _assert_acquisition_data_exists(hardware_retrieved_acquisitions: dict, qblox_acq_index: int, acq_channel: collections.abc.Hashable) -> None

      Assert that the qblox_acq_index is in the acquisition data.



   .. py:method:: _acq_channel_attrs(protocol: str, acq_index_dim_name: str) -> dict
      :staticmethod:



   .. py:method:: _get_bin_data(hardware_retrieved_acquisitions: dict, qblox_acq_index: int = 0) -> dict
      :classmethod:


      Returns the bin entry of the acquisition data dict.



   .. py:method:: _qblox_acq_index_to_qblox_acq_name(qblox_acq_index: int) -> str
      :staticmethod:


      Returns the name of the acquisition from the qblox_acq_index.



   .. py:method:: _get_binned_data_append(bin_data_function: collections.abc.Callable, acq_channel: str, seq_channel_hardware_mapping: qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMappingNonFullyAppend, use_repetitions: bool, coords: list[dict]) -> xarray.DataArray


   .. py:method:: _get_binned_data(bin_data_function: collections.abc.Callable, hardware_retrieved_acquisitions: dict, acq_channel: str, seq_channel_hardware_mapping: qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMappingNonFullyAppend, acq_duration: int, sequencer_name: str) -> xarray.DataArray

      Retrieves the binned acquisition data associated with an `acq_channel`.
      Note, this function is only called for `AVERAGE`, `APPEND` and `SUM` bin modes,
      but not for `AVERAGE_APPEND`.

      :param bin_data_function: Function that returns the bin data for the Qblox acquisition index and bin.
      :param hardware_retrieved_acquisitions: The acquisitions dict as returned by the sequencer.
      :param acq_channel: Acquisition channel.
      :param seq_channel_hardware_mapping: Acquisition hardware mapping for the sequencer and channel.
      :param acq_duration: Acquisition duration.
      :param sequencer_name: Sequencer.

      :returns: :
                    The integrated data.




   .. py:method:: _get_trigger_count_bin(qblox_acq_index: int, qblox_acq_bin: int, thresholded_trigger_count_metadata: qblox_scheduler.backends.types.common.ThresholdedTriggerCountMetadata | None, hardware_retrieved_acquisitions: dict, acq_duration: int, acq_channel: collections.abc.Hashable, sum_multiply_repetitions: bool, total_average_repetitions: int) -> int


   .. py:method:: _get_trigger_count_data(*, hardware_retrieved_acquisitions: dict, acq_channel: str, seq_channel_hardware_mapping: qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMappingNonFullyAppend, acq_duration: int, sequencer_name: str, sum_multiply_repetitions: bool) -> xarray.DataArray

      Retrieves the trigger count acquisition data associated with `acq_channel`.

      :param hardware_retrieved_acquisitions: The acquisitions dict as returned by the sequencer.
      :param acq_channel: The acquisition channel.
      :param seq_channel_hardware_mapping: Acquisition hardware mapping for the sequencer and channel.
      :param acq_duration: Desired maximum number of samples for the scope acquisition.
      :param sequencer_name: Sequencer.
      :param sum_multiply_repetitions: Multiplies data by repetitions for the SUM and AVERAGE_APPEND bin mode.

      :returns: data : xarray.DataArray
                    The acquired trigger count data.

      .. rubric:: Notes

      - For BinMode.DISTRIBUTION, `data` contains the distribution of counts.
      - For BinMode.APPEND, `data` contains the raw trigger counts.



   .. py:method:: _get_thresholded_trigger_count_bin(qblox_acq_index: int, qblox_acq_bin: int, thresholded_trigger_count_metadata: qblox_scheduler.backends.types.common.ThresholdedTriggerCountMetadata | None, hardware_retrieved_acquisitions: dict, acq_duration: int, acq_channel: collections.abc.Hashable, sum_multiply_repetitions: bool, total_average_repetitions: int) -> int


   .. py:method:: _get_thresholded_trigger_count_data(*, hardware_retrieved_acquisitions: dict, acq_channel: str, seq_channel_hardware_mapping: qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMappingNonFullyAppend, acq_duration: int, sequencer_name: str, sum_multiply_repetitions: bool) -> xarray.DataArray

      Gets the integration data but normalized to the integration time.

      The return value is thus the amplitude of the demodulated
      signal directly and has volt units (i.e. same units as a single sample of the
      integrated signal).

      :param hardware_retrieved_acquisitions: The acquisitions dict as returned by the sequencer.
      :param acq_channel: The acquisition channel.
      :param seq_channel_hardware_mapping: Acquisition hardware mapping for the sequencer and channel.
      :param acq_duration: Desired maximum number of samples for the scope acquisition.
      :param sequencer_name: Sequencer.
      :param sum_multiply_repetitions: Multiplies data by repetitions for the SUM and AVERAGE_APPEND bin mode.

      :returns: :
                    DataArray containing thresholded acquisition data.




.. py:class:: _QRMAcquisitionManager(parent: _AnalogReadoutComponent, acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, acq_hardware_mapping: dict[str, qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMapping], acquisition_duration: dict[str, int], seq_name_to_idx_map: dict[str, int], repetitions: int, scope_mode_sequencer_and_qblox_acq_index: tuple[int, int] | None = None, sequencers: dict[str, dict] | None = None)

   Bases: :py:obj:`_AcquisitionManagerBase`


   Utility class that handles the acquisitions performed with the QRM and QRC.

   An instance of this class is meant to exist only for a single prepare-start-
   retrieve_acquisition cycle to prevent stateful behavior.

   :param parent: Reference to the parent QRM or QRC IC component.
   :param acq_channels_data: Provides a summary of the used acquisition protocol, bin mode, acquisition channels,
                             acquisition indices per channel.
   :param acq_hardware_mapping: Acquisition hardware mapping.
   :param acquisition_duration: The duration of each acquisition for each sequencer.
   :param seq_name_to_idx_map: All available sequencer names to their ids in a dict.
   :param scope_mode_sequencer_and_qblox_acq_index: The sequencer and qblox acq_index of the scope mode acquisition if there's any.
   :param sequencers: Sequencer data.


   .. py:attribute:: _scope_mode_sequencer_and_qblox_acq_index
      :value: None



   .. py:attribute:: _sequencers
      :value: None



   .. py:method:: _protocol_to_bin_function(protocol: str) -> collections.abc.Callable


   .. py:method:: _protocol_to_acq_function_map(protocol: str) -> collections.abc.Callable

      Mapping from acquisition protocol name to the function that processes the raw
      acquisition data.



   .. py:method:: _check_bin_mode_compatible_fully_append(acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, node: qblox_scheduler.backends.qblox.qblox_acq_index_manager.AcqFullyAppendLoopNode | qblox_scheduler.backends.qblox.qblox_acq_index_manager.FullyAppendAcqInfo) -> None
      :staticmethod:



   .. py:method:: _check_bin_mode_compatible(acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, acq_hardware_mapping: dict[str, qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMapping]) -> None
      :staticmethod:



   .. py:method:: retrieve_acquisition() -> xarray.Dataset

      Retrieves all the acquisition data in the correct format.

      :returns: :
                    The acquisitions with the protocols specified in the `acq_channels_data`.
                    Each `xarray.DataArray` in the `xarray.Dataset` corresponds to one `acq_channel`.
                    The ``acq_channel`` is the name of each `xarray.DataArray` in the `xarray.Dataset`.
                    Each `xarray.DataArray` is a two-dimensional array,
                    with ``acq_index`` and ``repetition`` as dimensions.




   .. py:method:: _store_scope_acquisition() -> None

      Calls :code:`store_scope_acquisition` function on the Qblox instrument.

      This will ensure that the correct sequencer will store the scope acquisition
      data on the hardware, so it will be filled out when we call :code:`get_acquisitions`
      on the Qblox instrument's sequencer corresponding to the scope acquisition.



   .. py:method:: _get_scope_data(*, hardware_retrieved_acquisitions: dict, acq_channel: str, seq_channel_hardware_mapping: qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMappingNonFullyAppend, acq_duration: int, sequencer_name: str) -> xarray.DataArray

      Retrieves the scope mode acquisition associated with an `acq_channel`.

      :param hardware_retrieved_acquisitions: The acquisitions dict as returned by the sequencer.
      :param acq_channel: The acquisition channel.
      :param seq_channel_hardware_mapping: Acquisition hardware mapping for the sequencer and channel.
      :param acq_duration: Desired maximum number of samples for the scope acquisition.
      :param sequencer_name: Sequencer.

      :returns: :
                    The scope mode data.




   .. py:method:: _get_integration_weighted_separated_bin(qblox_acq_index: int, qblox_acq_bin: int, thresholded_trigger_count_metadata: qblox_scheduler.backends.types.common.ThresholdedTriggerCountMetadata | None, hardware_retrieved_acquisitions: dict, acq_duration: int, acq_channel: collections.abc.Hashable, total_average_repetitions: int) -> complex


   .. py:method:: _get_integration_amplitude_bin(qblox_acq_index: int, qblox_acq_bin: int, thresholded_trigger_count_metadata: qblox_scheduler.backends.types.common.ThresholdedTriggerCountMetadata | None, hardware_retrieved_acquisitions: dict, acq_duration: int, acq_channel: collections.abc.Hashable, total_average_repetitions: int) -> complex


   .. py:method:: _get_integration_real_bin(qblox_acq_index: int, qblox_acq_bin: int, thresholded_trigger_count_metadata: qblox_scheduler.backends.types.common.ThresholdedTriggerCountMetadata | None, hardware_retrieved_acquisitions: dict, acq_duration: int, acq_channel: collections.abc.Hashable, total_average_repetitions: int) -> complex


   .. py:method:: _get_thresholded_bin(qblox_acq_index: int, qblox_acq_bin: int, thresholded_trigger_count_metadata: qblox_scheduler.backends.types.common.ThresholdedTriggerCountMetadata | None, hardware_retrieved_acquisitions: dict, acq_duration: int, acq_channel: collections.abc.Hashable, total_average_repetitions: int) -> int


.. py:class:: _QTMAcquisitionManager(parent: _ReadoutModuleComponentT, acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, acq_hardware_mapping: dict[str, qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMapping], acquisition_duration: dict[str, int], seq_name_to_idx_map: dict[str, int], repetitions: int)

   Bases: :py:obj:`_AcquisitionManagerBase`


   Utility class that handles the acquisitions performed with the QTM.

   An instance of this class is meant to exist only for a single prepare-start-
   retrieve_acquisition cycle to prevent stateful behavior.

   :param parent: Reference to the parent QRM IC component.
   :param acq_channels_data: Provides a summary of the used acquisition protocol, bin mode, acquisition channels,
                             acquisition indices per channel, and repetitions, for each sequencer.
   :param acquisition_duration: The duration of each acquisition for each sequencer.
   :param seq_name_to_idx_map: All available sequencer names to their ids in a dict.


   .. py:method:: _protocol_to_bin_function(protocol: str) -> collections.abc.Callable


   .. py:method:: _protocol_to_acq_function_map(protocol: str) -> collections.abc.Callable

      Mapping from acquisition protocol name to the function that processes the raw
      acquisition data.



   .. py:method:: _check_bin_mode_compatible_fully_append(acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, node: qblox_scheduler.backends.qblox.qblox_acq_index_manager.AcqFullyAppendLoopNode | qblox_scheduler.backends.qblox.qblox_acq_index_manager.FullyAppendAcqInfo) -> None
      :staticmethod:



   .. py:method:: _check_bin_mode_compatible(acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, acq_hardware_mapping: dict[str, qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMapping]) -> None
      :staticmethod:



   .. py:method:: _get_digital_trace_data(*, hardware_retrieved_acquisitions: dict, acq_channel: str, seq_channel_hardware_mapping: qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMappingNonFullyAppend, acq_duration: int, sequencer_name: str) -> xarray.DataArray


   .. py:method:: _get_timetag_trace_data(*, hardware_retrieved_acquisitions: dict, acq_channel: str, seq_channel_hardware_mapping: qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMappingNonFullyAppend, acq_duration: int, sequencer_name: str) -> xarray.DataArray


   .. py:method:: _split_timetag_trace_data_per_window(timetags: list[int], scope_data: list[tuple[str, int]]) -> list[list[float]]

      Split the long array of ``scope_data`` on acquisition windows.

      The scope_data is formatted like [[TYPE, TIME],[TYPE,TIME],...], where TYPE is one of
      "OPEN", "RISE", "CLOSE". The TIME is absolute (cluster system time).

      Each acquisition window starts with "OPEN" and ends with "CLOSE". This method
      uses that information to divide the long ``scope_data`` array up into smaller
      arrays for each acquisition window.

      Furthermore, the ``timetags`` list contains the *relative* timetags of the
      *first* pulse recorded in each window. This data is used to calculate the
      relative timetags for all timetags in the trace.



   .. py:method:: _get_timetag_bin(qblox_acq_index: int, qblox_acq_bin: int, thresholded_trigger_count_metadata: qblox_scheduler.backends.types.common.ThresholdedTriggerCountMetadata | None, hardware_retrieved_acquisitions: dict, acq_duration: int, acq_channel: collections.abc.Hashable, total_average_repetitions: int) -> xarray.DataArray


.. py:class:: ClusterComponent(instrument: qblox_instruments.Cluster)

   Bases: :py:obj:`qblox_scheduler.instrument_coordinator.components.base.InstrumentCoordinatorComponentBase`


   Class that represents an instrument coordinator component for a Qblox cluster.

   New instances of the ClusterComponent will automatically add installed
   modules using name `"<cluster_name>_module<slot>"`.

   :param instrument: Reference to the cluster driver object.


   .. py:class:: _Program

      .. py:attribute:: module_programs
         :type:  dict[str, Any]


      .. py:attribute:: settings
         :type:  qblox_scheduler.backends.types.qblox.ClusterSettings



   .. py:attribute:: _cluster_modules
      :type:  dict[str, qblox_scheduler.instrument_coordinator.components.base.InstrumentCoordinatorComponentBase]


   .. py:attribute:: _program
      :type:  ClusterComponent | None
      :value: None



   .. py:attribute:: cluster


   .. py:property:: is_running
      :type: bool


      Returns true if any of the modules are currently running.


   .. py:method:: _set_parameter(instrument: qcodes.instrument.instrument_base.InstrumentBase, parameter_name: str, val: Any) -> None

      Set the parameter directly or using the lazy set.

      :param instrument: The instrument or instrument channel that holds the parameter to set,
                         e.g. `self.instrument` or `self.instrument[f"sequencer{idx}"]`.
      :param parameter_name: The name of the parameter to set.
      :param val: The new value of the parameter.



   .. py:method:: start() -> None

      Starts all the modules in the cluster.



   .. py:method:: _sync_on_external_trigger(settings: qblox_scheduler.backends.types.qblox.ExternalTriggerSyncSettings) -> None


   .. py:method:: stop() -> None

      Stops all the modules in the cluster.



   .. py:method:: prepare(program: dict[str, dict | qblox_scheduler.backends.types.qblox.ClusterSettings]) -> None

      Prepares the cluster component for execution of a schedule.

      :param program: The compiled instructions to configure the cluster to.
      :param acq_channels_data: Acquisition channels data for acquisition mapping.
      :param repetitions: Repetitions of the schedule.



   .. py:method:: retrieve_acquisition() -> xarray.Dataset | None

      Retrieves all the data from the instruments.

      :returns: :
                    The acquired data or ``None`` if no acquisitions have been performed.




   .. py:method:: wait_done(timeout_sec: int = 10) -> None

      Blocks until all the components are done executing their programs.

      :param timeout_sec: The time in seconds until the instrument is considered to have timed out.



   .. py:method:: get_hardware_log(compiled_schedule: qblox_scheduler.schedules.schedule.CompiledSchedule) -> dict | None

      Retrieve the hardware log of the Cluster Management Module and associated modules.

      This log includes the module serial numbers and
      firmware version.

      :param compiled_schedule: Compiled schedule to check if this cluster is referenced in (and if so,
                                which specific modules are referenced in).

      :returns: :
                    A dict containing the hardware log of the cluster, in case the
                    component was referenced; else None.




   .. py:method:: get_module_descriptions() -> dict[int, qblox_scheduler.backends.types.qblox.ClusterModuleDescription]

      Get the module types of this cluster, indexed by their position in the cluster.


      :returns: :
                    A dictionary containing the module types in this cluster,
                    indexed by their position in the cluster.




.. py:function:: _get_instrument_ip(component: qblox_scheduler.instrument_coordinator.components.base.InstrumentCoordinatorComponentBase) -> str

.. py:function:: _get_configuration_manager(instrument_ip: str) -> qblox_instruments.ConfigurationManager

.. py:function:: _download_log(config_manager: qblox_instruments.ConfigurationManager, is_cluster: bool | None = False) -> dict

