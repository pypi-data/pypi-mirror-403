calibration
===========

.. py:module:: qblox_scheduler.backends.types.qblox.calibration 

.. autoapi-nested-parse::

   Python dataclasses for compilation to Qblox hardware.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.qblox.calibration.ComplexInputGain
   qblox_scheduler.backends.types.qblox.calibration.QbloxMixerCorrections
   qblox_scheduler.backends.types.qblox.calibration.QbloxHardwareDistortionCorrection
   qblox_scheduler.backends.types.qblox.calibration.DigitizationThresholds




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.qblox.calibration.RealInputGain
   qblox_scheduler.backends.types.qblox.calibration.OutputAttenuation
   qblox_scheduler.backends.types.qblox.calibration.InputAttenuation


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



.. py:class:: DigitizationThresholds(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   The settings that determine when an analog voltage is counted as a pulse.


   .. py:attribute:: analog_threshold
      :type:  Optional[float]
      :value: None


      For QTM modules only, this is the voltage threshold above which an input signal is
      registered as high.


