channels
========

.. py:module:: qblox_scheduler.backends.types.qblox.channels 

.. autoapi-nested-parse::

   Python dataclasses for compilation to Qblox hardware.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.qblox.channels.ComplexChannelDescription
   qblox_scheduler.backends.types.qblox.channels.RealChannelDescription
   qblox_scheduler.backends.types.qblox.channels.DigitalChannelDescription




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


.. py:class:: DigitalChannelDescription(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Information needed to specify a digital (marker) output
   (for :class:`~.qblox_scheduler.operations.pulse_library.MarkerPulse`) in the
   :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.


   .. py:attribute:: distortion_correction_latency_compensation
      :type:  int

      Delay compensation setting that either
      delays the signal by the amount chosen by the settings or not.


