qblox
=====

.. py:module:: qblox_scheduler.backends.types.qblox 

.. autoapi-nested-parse::

   Public API for the Qblox backend data types.



Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   calibration/index.rst
   channels/index.rst
   filters/index.rst
   hardware/index.rst
   modules/index.rst
   op_info/index.rst
   options/index.rst
   properties/index.rst
   settings/index.rst


Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.qblox.ComplexInputGain
   qblox_scheduler.backends.types.qblox.DigitizationThresholds
   qblox_scheduler.backends.types.qblox.QbloxHardwareDistortionCorrection
   qblox_scheduler.backends.types.qblox.QbloxMixerCorrections
   qblox_scheduler.backends.types.qblox.ComplexChannelDescription
   qblox_scheduler.backends.types.qblox.DigitalChannelDescription
   qblox_scheduler.backends.types.qblox.RealChannelDescription
   qblox_scheduler.backends.types.qblox.QbloxRealTimeFilter
   qblox_scheduler.backends.types.qblox.ClusterDescription
   qblox_scheduler.backends.types.qblox.QbloxBaseDescription
   qblox_scheduler.backends.types.qblox.QCMDescription
   qblox_scheduler.backends.types.qblox.QCMRFDescription
   qblox_scheduler.backends.types.qblox.QRCDescription
   qblox_scheduler.backends.types.qblox.QRMDescription
   qblox_scheduler.backends.types.qblox.QRMRFDescription
   qblox_scheduler.backends.types.qblox.QSMDescription
   qblox_scheduler.backends.types.qblox.QTMDescription
   qblox_scheduler.backends.types.qblox.RFDescription
   qblox_scheduler.backends.types.qblox.OpInfo
   qblox_scheduler.backends.types.qblox.QbloxHardwareOptions
   qblox_scheduler.backends.types.qblox.SequencerOptions
   qblox_scheduler.backends.types.qblox.BoundedParameter
   qblox_scheduler.backends.types.qblox.StaticAnalogModuleProperties
   qblox_scheduler.backends.types.qblox.StaticDCModuleProperties
   qblox_scheduler.backends.types.qblox.StaticHardwareProperties
   qblox_scheduler.backends.types.qblox.StaticTimetagModuleProperties
   qblox_scheduler.backends.types.qblox.AnalogModuleSettings
   qblox_scheduler.backends.types.qblox.AnalogSequencerSettings
   qblox_scheduler.backends.types.qblox.BaseModuleSettings
   qblox_scheduler.backends.types.qblox.BasebandModuleSettings
   qblox_scheduler.backends.types.qblox.ClusterSettings
   qblox_scheduler.backends.types.qblox.DCModuleSettings
   qblox_scheduler.backends.types.qblox.DistortionSettings
   qblox_scheduler.backends.types.qblox.ExternalTriggerSyncSettings
   qblox_scheduler.backends.types.qblox.LOSettings
   qblox_scheduler.backends.types.qblox.RFModuleSettings
   qblox_scheduler.backends.types.qblox.SequencerSettings
   qblox_scheduler.backends.types.qblox.ThresholdedAcqTriggerReadSettings
   qblox_scheduler.backends.types.qblox.TimetagModuleSettings
   qblox_scheduler.backends.types.qblox.TimetagSequencerSettings




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.qblox.InputAttenuation
   qblox_scheduler.backends.types.qblox.OutputAttenuation
   qblox_scheduler.backends.types.qblox.RealInputGain
   qblox_scheduler.backends.types.qblox.QbloxHardwareDescription
   qblox_scheduler.backends.types.qblox.ClusterModuleDescription


.. py:class:: ComplexInputGain(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Input gain settings for a complex input connected to a port-clock combination.

   This gain value will be set on the QRM input ports
   that are connected to this port-clock combination.

   .. admonition:: Example
       :class: dropdown

       .. code-block:: python

           hardware_compilation_config.hardware_options.input_gain = {
               "q0:res-q0.ro": ComplexInputGain(
                   gain_I=2,
                   gain_Q=3
               ),
           }


   .. py:attribute:: gain_I
      :type:  int

      Gain setting on the input receiving the I-component data for this port-clock combination.


   .. py:attribute:: gain_Q
      :type:  int

      Gain setting on the input receiving the Q-component data for this port-clock combination.


.. py:class:: DigitizationThresholds(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   The settings that determine when an analog voltage is counted as a pulse.


   .. py:attribute:: analog_threshold
      :type:  Optional[float]
      :value: None


      For QTM modules only, this is the voltage threshold above which an input signal is
      registered as high.


.. py:data:: InputAttenuation

   Input attenuation setting for a port-clock combination.

   This attenuation value will be set on each control-hardware output
   port that is connected to this port-clock combination.

   .. admonition:: Example
       :class: dropdown

       .. code-block:: python

           hardware_compilation_config.hardware_options.input_att = {
               "q0:res-q0.ro": InputAttenuation(10),
           }

.. py:data:: OutputAttenuation

   Output attenuation setting for a port-clock combination.

   This attenuation value will be set on each control-hardware output
   port that is connected to this port-clock combination.

   .. admonition:: Example
       :class: dropdown

       .. code-block:: python

           hardware_compilation_config.hardware_options.output_att = {
               "q0:res-q0.ro": OutputAttenuation(10),
           }

.. py:class:: QbloxHardwareDistortionCorrection(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.backends.types.common.HardwareDistortionCorrection`


   A hardware distortion correction specific to the Qblox backend.


   .. py:attribute:: exp0_coeffs
      :type:  Optional[list[float]]
      :value: None


      Coefficients of the exponential overshoot/undershoot correction 1.


   .. py:attribute:: exp1_coeffs
      :type:  Optional[list[float]]
      :value: None


      Coefficients of the exponential overshoot/undershoot correction 2.


   .. py:attribute:: exp2_coeffs
      :type:  Optional[list[float]]
      :value: None


      Coefficients of the exponential overshoot/undershoot correction 3.


   .. py:attribute:: exp3_coeffs
      :type:  Optional[list[float]]
      :value: None


      Coefficients of the exponential overshoot/undershoot correction 4.


   .. py:attribute:: fir_coeffs
      :type:  Optional[list[float]]
      :value: None


      Coefficients for the FIR filter.


   .. py:method:: fir_coeffs_sum_to_1(value: Optional[list[float]]) -> Optional[list[float]]
      :classmethod:


      Validate whether the FIR coefficients sum up to 1.



.. py:class:: QbloxMixerCorrections(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.backends.types.common.MixerCorrections`


   Mixer correction settings with defaults set to None, and extra mixer correction
   settings for _automated_ mixer correction.

   These settings will be set on each control-hardware output
   port that is connected to this port-clock combination.

   .. admonition:: Example
       :class: dropdown

       .. code-block:: python

           hardware_compilation_config.hardware_options.mixer_corrections = {
               "q0:res-q0.ro": {
                   auto_lo_cal="on_lo_interm_freq_change",
                   auto_sideband_cal="on_interm_freq_change"
               },
           }


   .. py:attribute:: dc_offset_i
      :type:  Optional[float]
      :value: None


      The DC offset on the I channel used for this port-clock combination.


   .. py:attribute:: dc_offset_q
      :type:  Optional[float]
      :value: None


      The DC offset on the Q channel used for this port-clock combination.


   .. py:attribute:: amp_ratio
      :type:  float
      :value: None


      The mixer gain ratio used for this port-clock combination.


   .. py:attribute:: phase_error
      :type:  float
      :value: None


      The mixer phase error used for this port-clock combination.


   .. py:attribute:: auto_lo_cal
      :type:  qblox_scheduler.backends.qblox.enums.LoCalEnum

      Setting that controls whether the mixer is calibrated upon changing the LO and/or
      intermodulation frequency.


   .. py:attribute:: auto_sideband_cal
      :type:  qblox_scheduler.backends.qblox.enums.SidebandCalEnum

      Setting that controls whether the mixer is calibrated upon changing the
      intermodulation frequency.


   .. py:method:: warn_if_mixed_auto_and_manual_calibration(data: dict[str, Any]) -> dict[str, Any]
      :classmethod:


      Warn if there is mixed usage of automatic mixer calibration (the auto_*
      settings) and manual mixer correction settings.



.. py:data:: RealInputGain

   Input gain settings for a real input connected to a port-clock combination.

   This gain value will be set on the QRM input ports
   that are connected to this port-clock combination.

   .. admonition:: Example
       :class: dropdown

       .. code-block:: python

           hardware_compilation_config.hardware_options.input_gain = {
               "q0:res-q0.ro": RealInputGain(2),
           }

.. py:class:: ComplexChannelDescription(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Information needed to specify a complex input/output in the
   :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.


   .. py:attribute:: marker_debug_mode_enable
      :type:  bool
      :value: False


      Setting to send 4 ns trigger pulse on the marker
      located next to the I/O port along with each operation.
      The marker will be pulled high at the same time as the module starts playing or acquiring.


   .. py:attribute:: mix_lo
      :type:  bool
      :value: True


      Whether IQ mixing with a local oscillator is enabled for this channel.
      Effectively always ``True`` for RF modules.


   .. py:attribute:: downconverter_freq
      :type:  Optional[float]
      :value: None


      Downconverter frequency that should be taken into account w
      hen determining the modulation frequencies for this channel.
      Only relevant for users with custom Qblox downconverter hardware.


   .. py:attribute:: distortion_correction_latency_compensation
      :type:  int

      Delay compensation setting that either
      delays the signal by the amount chosen by the settings or not.


.. py:class:: DigitalChannelDescription(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Information needed to specify a digital (marker) output
   (for :class:`~.qblox_scheduler.operations.pulse_library.MarkerPulse`) in the
   :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.


   .. py:attribute:: distortion_correction_latency_compensation
      :type:  int

      Delay compensation setting that either
      delays the signal by the amount chosen by the settings or not.


.. py:class:: RealChannelDescription(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Information needed to specify a real input/output in the
   :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.


   .. py:attribute:: marker_debug_mode_enable
      :type:  bool
      :value: False


      Setting to send 4 ns trigger pulse on the marker located
      next to the I/O port along with each operation.
      The marker will be pulled high at the same time as the module starts playing or acquiring.


   .. py:attribute:: mix_lo
      :type:  bool
      :value: True


      Whether IQ mixing with a local oscillator is enabled for this channel.
      Effectively always ``True`` for RF modules.


   .. py:attribute:: distortion_correction_latency_compensation
      :type:  int

      Delay compensation setting that either
      delays the signal by the amount chosen by the settings or not.


.. py:class:: QbloxRealTimeFilter

   Bases: :py:obj:`dataclasses_json.DataClassJsonMixin`


   An individual real time filter on Qblox hardware.


   .. py:attribute:: coeffs
      :type:  Optional[Union[float, list[float]]]
      :value: None


      Coefficient(s) of the filter.
      Can be None if there is no filter
      or if it is inactive.


   .. py:attribute:: config
      :type:  qblox_scheduler.backends.qblox.enums.FilterConfig

      Configuration of the filter.
      One of 'BYPASSED', 'ENABLED',
      or 'DELAY_COMP'.


   .. py:attribute:: marker_delay
      :type:  qblox_scheduler.backends.qblox.enums.FilterMarkerDelay

      State of the marker delay.
      One of 'BYPASSED' or 'ENABLED'.


.. py:class:: ClusterDescription(/, **data: Any)

   Bases: :py:obj:`QbloxBaseDescription`


   Information needed to specify a Cluster in the :class:`~.CompilationConfig`.


   .. py:attribute:: instrument_type
      :type:  Literal['Cluster']
      :value: 'Cluster'


      The instrument type, used to select this datastructure
      when parsing a :class:`~.CompilationConfig`.


   .. py:attribute:: modules
      :type:  dict[int, qblox_scheduler.backends.types.qblox.modules.ClusterModuleDescription]

      Description of the modules of this Cluster, using slot index as key.


   .. py:attribute:: ip
      :type:  Optional[str]
      :value: None


      Unique identifier (typically the ip address) used to connect to the cluster


   .. py:attribute:: sync_on_external_trigger
      :type:  Optional[qblox_scheduler.backends.types.qblox.settings.ExternalTriggerSyncSettings]
      :value: None


      Settings for synchronizing the cluster on an external trigger.


.. py:class:: QbloxBaseDescription(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.backends.types.common.HardwareDescription`


   Base class for a Qblox hardware description.


   .. py:attribute:: ref
      :type:  Literal['internal', 'external']

      The reference source for the instrument.


   .. py:attribute:: sequence_to_file
      :type:  bool
      :value: False


      Write sequencer programs to files for (all modules in this) instrument.


.. py:data:: QbloxHardwareDescription

   Specifies a piece of Qblox hardware and its instrument-specific settings.

.. py:data:: ClusterModuleDescription

   Specifies a Cluster module and its instrument-specific settings.

   The supported instrument types are:
   :class:`~.QRMDescription`,
   :class:`~.QCMDescription`,
   :class:`~.QRMRFDescription`,
   :class:`~.QRCDescription`,
   :class:`~.QCMRFDescription`,
   :class:`~.QTMDescription`,
   :class:`~.QSMDescription`,

.. py:class:: QCMDescription(/, **data: Any)

   Bases: :py:obj:`_ModuleDescriptionBase`


   Information needed to specify a QCM in the
   :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.


   .. py:attribute:: instrument_type
      :type:  Literal['QCM']
      :value: 'QCM'


      The instrument type of this module.


   .. py:attribute:: sequence_to_file
      :type:  bool
      :value: False


      Write sequencer programs to files, for this module.


   .. py:attribute:: complex_output_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex output channel on this QCM, corresponding to ports O1 and O2.


   .. py:attribute:: complex_output_1
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex output channel on this QCM, corresponding to ports O3 and O4.


   .. py:attribute:: real_output_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.RealChannelDescription]
      :value: None


      Description of the real output channel on this QCM, corresponding to port O1.


   .. py:attribute:: real_output_1
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.RealChannelDescription]
      :value: None


      Description of the real output channel on this QCM, corresponding to port O2.


   .. py:attribute:: real_output_2
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.RealChannelDescription]
      :value: None


      Description of the real output channel on this QCM, corresponding to port O3.


   .. py:attribute:: real_output_3
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.RealChannelDescription]
      :value: None


      Description of the real output channel on this QCM, corresponding to port O4.


   .. py:attribute:: digital_output_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital (marker) output channel on this QCM, corresponding to port M1.


   .. py:attribute:: digital_output_1
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital (marker) output channel on this QCM, corresponding to port M2.


   .. py:attribute:: digital_output_2
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital (marker) output channel on this QCM, corresponding to port M3.


   .. py:attribute:: digital_output_3
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital (marker) output channel on this QCM, corresponding to port M4.


.. py:class:: QCMRFDescription(/, **data: Any)

   Bases: :py:obj:`RFDescription`


   Information needed to specify a QCM-RF in the
   :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.


   .. py:attribute:: instrument_type
      :type:  Literal['QCM_RF']
      :value: 'QCM_RF'


      The instrument type of this module.


   .. py:attribute:: complex_output_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex output channel on this QCM-RF, corresponding to port O1.


   .. py:attribute:: complex_output_1
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex output channel on this QCM-RF, corresponding to port O2.


   .. py:attribute:: digital_output_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital (marker) output channel on this QCM-RF,
      corresponding to port M1.


   .. py:attribute:: digital_output_1
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital (marker) output channel on this QCM-RF,
      corresponding to port M2.


.. py:class:: QRCDescription(/, **data: Any)

   Bases: :py:obj:`_ModuleDescriptionBase`


   Information needed to specify a QRC in the
   :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.


   .. py:attribute:: instrument_type
      :type:  Literal['QRC']
      :value: 'QRC'


      The instrument type of this module.


   .. py:attribute:: sequence_to_file
      :type:  bool
      :value: False


      Write sequencer programs to files, for this module.


   .. py:attribute:: complex_output_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex output channel on this QRC, corresponding to port O1.


   .. py:attribute:: complex_output_1
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex output channel on this QRC, corresponding to port O2.


   .. py:attribute:: complex_output_2
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex output channel on this QRC, corresponding to port O3.


   .. py:attribute:: complex_output_3
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex output channel on this QRC, corresponding to port O4.


   .. py:attribute:: complex_output_4
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex output channel on this QRC, corresponding to port O5.


   .. py:attribute:: complex_output_5
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex output channel on this QRC, corresponding to port O6.


   .. py:attribute:: complex_input_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex input channel on this QRC, corresponding to port I1.


   .. py:attribute:: complex_input_1
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex input channel on this QRC, corresponding to port I2.


   .. py:attribute:: digital_output_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital (marker) output channel on this QRC, corresponding to port M1.


.. py:class:: QRMDescription(/, **data: Any)

   Bases: :py:obj:`_ModuleDescriptionBase`


   Information needed to specify a QRM in the
   :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.


   .. py:attribute:: instrument_type
      :type:  Literal['QRM']
      :value: 'QRM'


      The instrument type of this module.


   .. py:attribute:: sequence_to_file
      :type:  bool
      :value: False


      Write sequencer programs to files, for this module.


   .. py:attribute:: complex_output_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex output channel on this QRM, corresponding to ports O1 and O2.


   .. py:attribute:: complex_input_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex input channel on this QRM, corresponding to ports I1 and I2.


   .. py:attribute:: real_output_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.RealChannelDescription]
      :value: None


      Description of the real output channel on this QRM, corresponding to port O1.


   .. py:attribute:: real_output_1
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.RealChannelDescription]
      :value: None


      Description of the real output channel on this QRM, corresponding to port O2.


   .. py:attribute:: real_input_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.RealChannelDescription]
      :value: None


      Description of the real input channel on this QRM, corresponding to port I1.


   .. py:attribute:: real_input_1
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.RealChannelDescription]
      :value: None


      Description of the real output channel on this QRM, corresponding to port I2.


   .. py:attribute:: digital_output_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital (marker) output channel on this QRM, corresponding to port M1.


   .. py:attribute:: digital_output_1
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital (marker) output channel on this QRM, corresponding to port M2.


   .. py:attribute:: digital_output_2
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital (marker) output channel on this QRM, corresponding to port M3.


   .. py:attribute:: digital_output_3
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital (marker) output channel on this QRM, corresponding to port M4.


.. py:class:: QRMRFDescription(/, **data: Any)

   Bases: :py:obj:`RFDescription`


   Information needed to specify a QRM-RF in the
   :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.


   .. py:attribute:: instrument_type
      :type:  Literal['QRM_RF']
      :value: 'QRM_RF'


      The instrument type of this module.


   .. py:attribute:: complex_output_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex output channel on this QRM-RF, corresponding to port O1.


   .. py:attribute:: complex_input_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription]
      :value: None


      Description of the complex input channel on this QRM-RF, corresponding to port I1.


   .. py:attribute:: digital_output_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital (marker) output channel on this QRM-RF,
      corresponding to port M1.


   .. py:attribute:: digital_output_1
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital (marker) output channel on this QRM-RF,
      corresponding to port M2.


.. py:class:: QSMDescription(/, **data: Any)

   Bases: :py:obj:`_ModuleDescriptionBase`


   Information needed to specify a QSM in the
   :class:`~.quantify_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.


   .. py:attribute:: instrument_type
      :type:  Literal['QSM']
      :value: 'QSM'


      The instrument type of this module.


   .. py:attribute:: sequence_to_file
      :type:  bool
      :value: False


      Write sequencer programs to files, for this module.


.. py:class:: QTMDescription(/, **data: Any)

   Bases: :py:obj:`_ModuleDescriptionBase`


   Information needed to specify a QTM in the
   :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.


   .. py:attribute:: instrument_type
      :type:  Literal['QTM']
      :value: 'QTM'


      The instrument type of this module.


   .. py:attribute:: sequence_to_file
      :type:  bool
      :value: False


      Write sequencer programs to files, for this module.


   .. py:attribute:: digital_input_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 1, specified as input.


   .. py:attribute:: digital_input_1
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 2, specified as input.


   .. py:attribute:: digital_input_2
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 3, specified as input.


   .. py:attribute:: digital_input_3
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 4, specified as input.


   .. py:attribute:: digital_input_4
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 5, specified as input.


   .. py:attribute:: digital_input_5
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 6, specified as input.


   .. py:attribute:: digital_input_6
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 7, specified as input.


   .. py:attribute:: digital_input_7
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 8, specified as input.


   .. py:attribute:: digital_output_0
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 1, specified as output.


   .. py:attribute:: digital_output_1
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 2, specified as output.


   .. py:attribute:: digital_output_2
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 3, specified as output.


   .. py:attribute:: digital_output_3
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 4, specified as output.


   .. py:attribute:: digital_output_4
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 5, specified as output.


   .. py:attribute:: digital_output_5
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 6, specified as output.


   .. py:attribute:: digital_output_6
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 7, specified as output.


   .. py:attribute:: digital_output_7
      :type:  Optional[qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription]
      :value: None


      Description of the digital channel corresponding to port 8, specified as output.


   .. py:method:: validate_channel_names(channel_names: collections.abc.Iterable[str]) -> None
      :classmethod:


      Validate channel names specified in the Connectivity.



.. py:class:: RFDescription(/, **data: Any)

   Bases: :py:obj:`_ModuleDescriptionBase`


   User settings for QCM-RF and QRM-RF radio frequency (RF) modules.


   .. py:attribute:: sequence_to_file
      :type:  bool
      :value: False


      Write sequencer programs to files, for this module.


   .. py:attribute:: rf_output_on
      :type:  bool
      :value: True


      Whether the RF outputs of this module are always on by default.
      If set to False they can be turned on by using the
      :class:`~.qblox_scheduler.operations.hardware_operations.pulse_library.RFSwitchToggle`
      operation for QRM-RF and QCM-RF.


.. py:class:: OpInfo

   Bases: :py:obj:`dataclasses_json.DataClassJsonMixin`


   Data structure describing a pulse or acquisition and containing all the information
   required to play it.


   .. py:attribute:: name
      :type:  str

      Name of the operation that this pulse/acquisition is part of.


   .. py:attribute:: data
      :type:  dict

      The pulse/acquisition info taken from the ``data`` property of the
      pulse/acquisition in the schedule.


   .. py:attribute:: timing
      :type:  float

      The start time of this pulse/acquisition.
      Note that this is a combination of the start time "t_abs" of the schedule
      operation, and the t0 of the pulse/acquisition which specifies a time relative
      to "t_abs".


   .. py:property:: duration
      :type: float


      The duration of the pulse/acquisition.


   .. py:property:: is_acquisition
      :type: bool


      Returns ``True`` if this is an acquisition, ``False`` otherwise.


   .. py:property:: is_real_time_io_operation
      :type: bool


      Returns ``True`` if the operation is a non-idle pulse (i.e., it has a
      waveform), ``False`` otherwise.


   .. py:property:: is_offset_instruction
      :type: bool


      Returns ``True`` if the operation describes a DC offset operation,
      corresponding to the Q1ASM instruction ``set_awg_offset``.


   .. py:property:: is_parameter_instruction
      :type: bool


      Return ``True`` if the instruction is a parameter, like a voltage offset.

      From the Qblox documentation: "parameter operation instructions" are latched and
      only updated when the upd_param, play, acquire, acquire_weighed or acquire_ttl
      instructions are executed.

      Please refer to
      https://docs.qblox.com/en/main/cluster/q1_sequence_processor.html#q1-instructions
      for the full list of these instructions.


   .. py:property:: is_parameter_update
      :type: bool


      Return ``True`` if the operation is a parameter update, corresponding to the
      Q1ASM instruction ``upd_param``.


   .. py:property:: is_loop
      :type: bool


      Return ``True`` if the operation is a loop, corresponding to the Q1ASM
      instruction ``loop``.


   .. py:property:: is_control_flow_end
      :type: bool


      Return ``True`` if the operation is a control flow end.


   .. py:method:: substitute(substitutions: dict[qblox_scheduler.operations.expressions.Expression, qblox_scheduler.operations.expressions.Expression | int | float | complex]) -> OpInfo

      Substitute matching expressions in operand, possibly evaluating a result.



.. py:class:: QbloxHardwareOptions(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.backends.types.common.HardwareOptions`


   Datastructure containing the hardware options for each port-clock combination.

   .. admonition:: Example
       :class: dropdown

       Here, the HardwareOptions datastructure is created by parsing a
       dictionary containing the relevant information.

       .. jupyter-execute::

           import pprint
           from qblox_scheduler.schemas.examples.utils import (
               load_json_example_scheme
           )

       .. jupyter-execute::

           from qblox_scheduler.backends.types.qblox import (
               QbloxHardwareOptions
           )
           qblox_hw_options_dict = load_json_example_scheme(
               "qblox_hardware_config_transmon.json")["hardware_options"]
           pprint.pprint(qblox_hw_options_dict)

       The dictionary can be parsed using the :code:`model_validate` method.

       .. jupyter-execute::

           qblox_hw_options = QbloxHardwareOptions.model_validate(qblox_hw_options_dict)
           qblox_hw_options


   .. py:attribute:: input_gain
      :type:  Optional[dict[str, Union[qblox_scheduler.backends.types.qblox.calibration.RealInputGain, qblox_scheduler.backends.types.qblox.calibration.ComplexInputGain]]]
      :value: None


      Dictionary containing the input gain settings (values) that should be applied
      to the inputs that are connected to a certain port-clock combination (keys).


   .. py:attribute:: output_att
      :type:  Optional[dict[str, qblox_scheduler.backends.types.qblox.calibration.OutputAttenuation]]
      :value: None


      Dictionary containing the attenuation settings (values) that should be applied
      to the outputs that are connected to a certain port-clock combination (keys).


   .. py:attribute:: input_att
      :type:  Optional[dict[str, qblox_scheduler.backends.types.qblox.calibration.InputAttenuation]]
      :value: None


      Dictionary containing the attenuation settings (values) that should be applied
      to the inputs that are connected to a certain port-clock combination (keys).


   .. py:attribute:: mixer_corrections
      :type:  Optional[dict[str, qblox_scheduler.backends.types.qblox.calibration.QbloxMixerCorrections]]
      :value: None


      Dictionary containing the qblox-specific mixer corrections (values) that should be
      used for signals on a certain port-clock combination (keys).


   .. py:attribute:: sequencer_options
      :type:  Optional[dict[str, SequencerOptions]]
      :value: None


      Dictionary containing the options (values) that should be set
      on the sequencer that is used for a certain port-clock combination (keys).


   .. py:attribute:: distortion_corrections
      :type:  Optional[dict[str, Union[qblox_scheduler.backends.types.common.SoftwareDistortionCorrection, qblox_scheduler.backends.types.qblox.calibration.QbloxHardwareDistortionCorrection, list[qblox_scheduler.backends.types.qblox.calibration.QbloxHardwareDistortionCorrection]]]]
      :value: None


      Dictionary containing the distortion corrections (values) that should be applied
      to waveforms on a certain port-clock combination (keys).


   .. py:attribute:: digitization_thresholds
      :type:  Optional[dict[str, qblox_scheduler.backends.types.qblox.calibration.DigitizationThresholds]]
      :value: None


      Dictionary containing the digitization threshold settings for QTM modules. These are
      the settings that determine the voltage thresholds above which input signals are
      registered as high.


   .. py:attribute:: source_mode
      :type:  Optional[dict[str, Literal['v_source', 'i_source', 'ground', 'open']]]
      :value: None


      Sourcing behavior of the channel, either outputting a controlled voltage or current
      (QSM modules).


   .. py:attribute:: measure_mode
      :type:  Optional[dict[str, Literal['automatic', 'coarse', 'fine_nanoampere', 'fine_picoampere']]]
      :value: None


      Range coarse/fine for the measurement precision (QSM modules).


   .. py:attribute:: ramping_rate
      :type:  Optional[dict[str, float]]
      :value: None


      Ramp rate to ramp_rate value in volt/s. The different levels allow shortcuts
      to avoid unwanted communications with the instrument (QSM modules).


   .. py:attribute:: integration_time
      :type:  Optional[dict[str, int]]
      :value: None


      Integration time in seconds. The different levels allow shortcuts
      to avoid unwanted communications with the instrument (QSM modules).


   .. py:attribute:: safe_voltage_range
      :type:  Optional[dict[str, tuple[float, float]]]
      :value: None


      Voltage limits (-min, +max) to protect the device against accidental overvolting
      (QSM modules).


.. py:class:: SequencerOptions(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Configuration options for a sequencer.

   For allowed values, also see `Cluster QCoDeS parameters
   <https://docs.qblox.com/en/main/api_reference/sequencer.html#cluster-qcodes-parameters>`__.

   .. admonition:: Example
       :class: dropdown

       .. code-block:: python

           hardware_compilation_config.hardware_options.sequencer_options = {
               "q0:res-q0.ro": {
                   "init_offset_awg_path_I": 0.1,
                   "init_offset_awg_path_Q": -0.1,
                   "init_gain_awg_path_I": 0.9,
                   "init_gain_awg_path_Q": 1.0,
                   "ttl_acq_threshold": 0.5
                   "qasm_hook_func": foo
               }
           }


   .. py:attribute:: init_offset_awg_path_I
      :type:  float
      :value: None


      Specifies what value the sequencer offset for AWG path_I will be reset to
      before the start of the experiment.


   .. py:attribute:: init_offset_awg_path_Q
      :type:  float
      :value: None


      Specifies what value the sequencer offset for AWG path_Q will be reset to
      before the start of the experiment.


   .. py:attribute:: init_gain_awg_path_I
      :type:  float
      :value: None


      Specifies what value the sequencer gain for AWG path_I will be reset to
      before the start of the experiment.


   .. py:attribute:: init_gain_awg_path_Q
      :type:  float
      :value: None


      Specifies what value the sequencer gain for AWG path_Q will be reset to
      before the start of the experiment.


   .. py:attribute:: ttl_acq_threshold
      :type:  Optional[float]
      :value: None


      For QRM modules only, the threshold value with which to compare the input ADC values
      of the selected input path.


   .. py:attribute:: qasm_hook_func
      :type:  Optional[collections.abc.Callable]
      :value: None


      Function to inject custom qasm instructions after the compiler inserts the
      footer and the stop instruction in the generated qasm program.


   .. py:method:: _init_setting_limits(init_setting: float) -> float
      :classmethod:



.. py:class:: BoundedParameter

   Specifies a certain parameter with a fixed max and min in a certain unit.


   .. py:attribute:: min_val
      :type:  float

      Min value allowed.


   .. py:attribute:: max_val
      :type:  float

      Max value allowed.


   .. py:attribute:: units
      :type:  str

      Units in which the parameter is specified.


.. py:class:: StaticAnalogModuleProperties

   Bases: :py:obj:`StaticHardwareProperties`


   Specifies the fixed hardware properties needed in the backend for QRM/QCM modules.


   .. py:attribute:: max_awg_output_voltage
      :type:  Optional[float]

      Maximum output voltage of the awg.


   .. py:attribute:: mixer_dc_offset_range
      :type:  BoundedParameter

      Specifies the range over which the dc offsets can be set that are used for mixer
      calibration.


   .. py:attribute:: channel_name_to_digital_marker
      :type:  dict[str, int]

      A mapping from channel_name to digital marker setting.
      Specifies which marker bit needs to be set at start if the
      output (as a string ex. `complex_output_0`) contains a pulse.


   .. py:attribute:: default_markers
      :type:  dict[str, int] | None
      :value: None


      The default markers value to set at the beginning of programs and reset marker pulses to.
      A mapping from channel name to marker.
      Important for RF instruments that use the set_mrk command to enable/disable the RF output.


   .. py:attribute:: default_nco_en
      :type:  bool
      :value: False


      The default nco settings for sequencers
      (``mod_en_awg`` and ``demod_en_acq`` QCoDeS parameters).


.. py:class:: StaticDCModuleProperties

   Bases: :py:obj:`StaticHardwareProperties`


   Specifies the fixed hardware properties needed in the backend for QSM modules.


.. py:class:: StaticHardwareProperties

   Specifies the fixed hardware properties needed in the backend.


   .. py:attribute:: instrument_type
      :type:  str

      The type of instrument.


   .. py:method:: _get_connected_io_indices(mode: str, channel_idx: str) -> tuple[int, Ellipsis]

      Return the connected input/output indices associated to this channel name.



   .. py:method:: _get_connected_output_indices(channel_name: str) -> tuple[int, Ellipsis]

      Return the connected output indices associated to this channel name.



   .. py:method:: _get_connected_input_indices(channel_name: str, channel_name_measure: Union[list[str], None]) -> tuple[int, Ellipsis]

      Return the connected input indices associated to this channel name.



.. py:class:: StaticTimetagModuleProperties

   Bases: :py:obj:`StaticHardwareProperties`


   Specifies the fixed hardware properties needed in the backend for QTM modules.


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



.. py:class:: BasebandModuleSettings

   Bases: :py:obj:`AnalogModuleSettings`


   Settings for a baseband module.

   Class exists to ensure that the cluster baseband modules don't need special
   treatment in the rest of the code.


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


.. py:class:: LOSettings

   Bases: :py:obj:`dataclasses_json.DataClassJsonMixin`


   Dataclass containing all the settings for a generic LO instrument.


   .. py:attribute:: power
      :type:  dict[str, float]

      Power of the LO source.


   .. py:attribute:: frequency
      :type:  dict[str, Optional[float]]

      The frequency to set the LO to.


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


.. py:class:: TimetagModuleSettings

   Bases: :py:obj:`BaseModuleSettings`


   Global settings for the module to be set in the InstrumentCoordinator component.
   This is kept separate from the settings that can be set on a per-sequencer basis,
   which are specified in :class:`~.TimetagSequencerSettings`.


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




