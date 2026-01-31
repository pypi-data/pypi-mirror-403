properties
==========

.. py:module:: qblox_scheduler.backends.types.qblox.properties 

.. autoapi-nested-parse::

   Python dataclasses for compilation to Qblox hardware.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.qblox.properties.BoundedParameter
   qblox_scheduler.backends.types.qblox.properties.StaticHardwareProperties
   qblox_scheduler.backends.types.qblox.properties.StaticAnalogModuleProperties
   qblox_scheduler.backends.types.qblox.properties.StaticTimetagModuleProperties
   qblox_scheduler.backends.types.qblox.properties.StaticDCModuleProperties




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


.. py:class:: StaticTimetagModuleProperties

   Bases: :py:obj:`StaticHardwareProperties`


   Specifies the fixed hardware properties needed in the backend for QTM modules.


.. py:class:: StaticDCModuleProperties

   Bases: :py:obj:`StaticHardwareProperties`


   Specifies the fixed hardware properties needed in the backend for QSM modules.


