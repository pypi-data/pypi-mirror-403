enums
=====

.. py:module:: qblox_scheduler.backends.qblox.enums 

.. autoapi-nested-parse::

   Enums used by Qblox backend.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.enums._DeprecatedEnum
   qblox_scheduler.backends.qblox.enums.ChannelMode
   qblox_scheduler.backends.qblox.enums.FilterConfig
   qblox_scheduler.backends.qblox.enums.FilterMarkerDelay
   qblox_scheduler.backends.qblox.enums.QbloxFilterConfig
   qblox_scheduler.backends.qblox.enums.QbloxFilterMarkerDelay
   qblox_scheduler.backends.qblox.enums.DistortionCorrectionLatencyEnum
   qblox_scheduler.backends.qblox.enums.LoCalEnum
   qblox_scheduler.backends.qblox.enums.SidebandCalEnum
   qblox_scheduler.backends.qblox.enums.TimetagTraceType




.. py:class:: _DeprecatedEnum

   Bases: :py:obj:`enum.EnumMeta`


   Metaclass for Enum


.. py:class:: ChannelMode

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Enum for the channel mode of the Sequencer.


   .. py:attribute:: COMPLEX
      :value: 'complex'



   .. py:attribute:: REAL
      :value: 'real'



   .. py:attribute:: DIGITAL
      :value: 'digital'



.. py:class:: FilterConfig

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Configuration of a filter.


   .. py:attribute:: BYPASSED
      :value: 'bypassed'



   .. py:attribute:: ENABLED
      :value: 'enabled'



   .. py:attribute:: DELAY_COMP
      :value: 'delay_comp'



.. py:class:: FilterMarkerDelay

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Marker delay setting of a filter.


   .. py:attribute:: BYPASSED
      :value: 'bypassed'



   .. py:attribute:: DELAY_COMP
      :value: 'delay_comp'



.. py:class:: QbloxFilterConfig

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Deprecated.


   .. py:attribute:: BYPASSED
      :value: 'bypassed'



   .. py:attribute:: ENABLED
      :value: 'enabled'



   .. py:attribute:: DELAY_COMP
      :value: 'delay_comp'



.. py:class:: QbloxFilterMarkerDelay

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Deprecated.


   .. py:attribute:: BYPASSED
      :value: 'bypassed'



   .. py:attribute:: DELAY_COMP
      :value: 'delay_comp'



.. py:class:: DistortionCorrectionLatencyEnum

   Bases: :py:obj:`int`, :py:obj:`enum.Enum`


   Settings related to distortion corrections.


   .. py:attribute:: NO_DELAY_COMP
      :value: 0


      Setting for no distortion correction delay compensation


   .. py:attribute:: EXP0
      :value: 2


      Setting for delay compensation equal to exponential overshoot or undershoot correction


   .. py:attribute:: EXP1
      :value: 4


      Setting for delay compensation equal to exponential overshoot or undershoot correction


   .. py:attribute:: EXP2
      :value: 8


      Setting for delay compensation equal to exponential overshoot or undershoot correction


   .. py:attribute:: EXP3
      :value: 16


      Setting for delay compensation equal to exponential overshoot or undershoot correction


   .. py:attribute:: FIR
      :value: 32


      Setting for delay compensation equal to FIR filter


.. py:class:: LoCalEnum

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Settings related to the LO part of automatic mixer corrections.


   .. py:attribute:: OFF
      :value: 'off'



   .. py:attribute:: ON_LO_FREQ_CHANGE
      :value: 'on_lo_freq_change'



   .. py:attribute:: ON_LO_INTERM_FREQ_CHANGE
      :value: 'on_lo_interm_freq_change'



.. py:class:: SidebandCalEnum

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Settings related to the NCO part of automatic mixer corrections.


   .. py:attribute:: OFF
      :value: 'off'



   .. py:attribute:: ON_INTERM_FREQ_CHANGE
      :value: 'on_interm_freq_change'



.. py:class:: TimetagTraceType

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Types trace acquisition possible for a QTM.


   .. py:attribute:: SCOPE
      :value: 'scope'



   .. py:attribute:: TIMETAG
      :value: 'timetag'



