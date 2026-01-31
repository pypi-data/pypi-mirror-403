options
=======

.. py:module:: qblox_scheduler.backends.types.qblox.options 

.. autoapi-nested-parse::

   Python dataclasses for compilation to Qblox hardware.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.qblox.options.SequencerOptions
   qblox_scheduler.backends.types.qblox.options.QbloxHardwareOptions




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


