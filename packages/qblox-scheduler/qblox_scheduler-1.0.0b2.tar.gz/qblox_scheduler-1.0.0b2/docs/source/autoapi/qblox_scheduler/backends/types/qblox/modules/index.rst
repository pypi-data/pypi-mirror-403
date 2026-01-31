modules
=======

.. py:module:: qblox_scheduler.backends.types.qblox.modules 

.. autoapi-nested-parse::

   Python dataclasses for compilation to Qblox hardware.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.qblox.modules.QRMDescription
   qblox_scheduler.backends.types.qblox.modules.QCMDescription
   qblox_scheduler.backends.types.qblox.modules.RFDescription
   qblox_scheduler.backends.types.qblox.modules.QRMRFDescription
   qblox_scheduler.backends.types.qblox.modules.QRCDescription
   qblox_scheduler.backends.types.qblox.modules.QCMRFDescription
   qblox_scheduler.backends.types.qblox.modules.QTMDescription
   qblox_scheduler.backends.types.qblox.modules.QSMDescription




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.qblox.modules.ClusterModuleDescription


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

