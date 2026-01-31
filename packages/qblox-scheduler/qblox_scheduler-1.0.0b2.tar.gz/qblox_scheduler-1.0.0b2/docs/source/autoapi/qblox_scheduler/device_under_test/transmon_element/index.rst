transmon_element
================

.. py:module:: qblox_scheduler.device_under_test.transmon_element 

.. autoapi-nested-parse::

   The module contains definitions related to transmon elements.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.device_under_test.transmon_element.Ports
   qblox_scheduler.device_under_test.transmon_element.ClocksFrequencies
   qblox_scheduler.device_under_test.transmon_element.IdlingReset
   qblox_scheduler.device_under_test.transmon_element.RxyDRAG
   qblox_scheduler.device_under_test.transmon_element.PulseCompensationModule
   qblox_scheduler.device_under_test.transmon_element.DispersiveMeasurement
   qblox_scheduler.device_under_test.transmon_element.ReferenceMagnitude
   qblox_scheduler.device_under_test.transmon_element.BasicTransmonElement




.. py:class:: Ports(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing the ports.


   .. py:attribute:: microwave
      :type:  str
      :value: ''


      Name of the element's microwave port.


   .. py:attribute:: flux
      :type:  str
      :value: ''


      Name of the element's flux port.


   .. py:attribute:: readout
      :type:  str
      :value: ''


      Name of the element's readout port.


   .. py:method:: _fill_defaults() -> None


.. py:class:: ClocksFrequencies(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing the clock frequencies specifying the transitions to address.


   .. py:attribute:: f01
      :type:  float
      :value: None


      Frequency of the 01 clock.


   .. py:attribute:: f12
      :type:  float
      :value: None


      Frequency of the 12 clock.


   .. py:attribute:: readout
      :type:  float
      :value: None


      Frequency of the ro clock.


.. py:class:: IdlingReset(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing parameters for doing a reset by idling.


   .. py:attribute:: duration
      :type:  float
      :value: None


      Duration of the passive qubit reset (initialization by relaxation).


.. py:class:: RxyDRAG(name: str, parent: qblox_scheduler.device_under_test.device_element.DeviceElement | None = None, *, reference_magnitude_dBm: float = math.nan, reference_magnitude_V: float = math.nan, reference_magnitude_A: float = math.nan, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing parameters for performing an Rxy operation.

   The Rxy operation uses a DRAG pulse.


   .. py:attribute:: amp180
      :type:  float
      :value: None


      Amplitude required to perform a $\pi$ pulse.


   .. py:attribute:: beta
      :type:  float
      :value: None


      Ratio between the Gaussian Derivative (D) and Gaussian (G) components of the DRAG pulse.


   .. py:attribute:: duration
      :type:  float
      :value: None


      Duration of the control pulse.


   .. py:attribute:: reference_magnitude
      :type:  ReferenceMagnitude | None
      :value: None



.. py:class:: PulseCompensationModule(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing parameters for performing a PulseCompensation operation.


   .. py:attribute:: max_compensation_amp
      :type:  float
      :value: None


      Maximum amplitude for the pulse compensation.


   .. py:attribute:: time_grid
      :type:  float
      :value: None


      Time grid for the duration of the compensating pulse.


   .. py:attribute:: sampling_rate
      :type:  float
      :value: None


      Sampling rate of the pulses.


.. py:class:: DispersiveMeasurement(name: str, parent: qblox_scheduler.device_under_test.device_element.DeviceElement | None = None, *, reference_magnitude_dBm: float = math.nan, reference_magnitude_V: float = math.nan, reference_magnitude_A: float = math.nan, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing parameters to perform a measurement.

   The measurement that is performed is using
   :func:`~qblox_scheduler.operations.measurement_factories.dispersive_measurement_transmon`.


   .. py:attribute:: reference_magnitude


   .. py:attribute:: pulse_type
      :type:  Literal['SquarePulse']
      :value: None


      Envelope function that defines the shape of the readout pulse prior to modulation.


   .. py:attribute:: pulse_amp
      :type:  float
      :value: None


      Amplitude of the readout pulse.


   .. py:attribute:: pulse_duration
      :type:  float
      :value: None


      Duration of the readout pulse.


   .. py:attribute:: acq_channel
      :type:  collections.abc.Hashable
      :value: None


      Acquisition channel of to this device element.


   .. py:attribute:: acq_delay
      :type:  float
      :value: None


      Delay between the start of the readout pulse and the start of
      the acquisition. Note that some hardware backends do not support
      starting a pulse and the acquisition in the same clock cycle making 0
      delay an invalid value.


   .. py:attribute:: integration_time
      :type:  float
      :value: None


      Integration time for the readout acquisition.


   .. py:attribute:: reset_clock_phase
      :type:  bool
      :value: None


      The phase of the measurement clock will be reset by the control hardware
      at the start of each measurement if ``reset_clock_phase=True``.


   .. py:attribute:: acq_weights_a
      :type:  qblox_scheduler.structure.types.NDArray | None
      :value: None


      The weights for the I path. Used when specifying the
      ``"NumericalSeparatedWeightedIntegration"`` or the
      ``"NumericalWeightedIntegration"`` acquisition protocol.


   .. py:attribute:: acq_weights_b
      :type:  qblox_scheduler.structure.types.NDArray | None
      :value: None


      The weights for the Q path. Used when specifying the
      ``"NumericalSeparatedWeightedIntegration"`` or the
      ``"NumericalWeightedIntegration"`` acquisition protocol.


   .. py:attribute:: acq_weights_sampling_rate
      :type:  float
      :value: None


      The sample rate of the weights arrays, in Hertz. Used when specifying the
      ``"NumericalSeparatedWeightedIntegration"`` or the
      ``"NumericalWeightedIntegration"`` acquisition protocol.


   .. py:attribute:: acq_weight_type
      :type:  Literal['SSB', 'Numerical']
      :value: None



   .. py:attribute:: acq_rotation
      :type:  float
      :value: None


      The phase rotation in degrees required to perform thresholded acquisition.
      Note that rotation is performed before the threshold. For more details see
      :class:`~qblox_scheduler.operations.acquisition_library.ThresholdedAcquisition`.


   .. py:attribute:: acq_threshold
      :type:  float
      :value: None


      The threshold value against which the rotated and integrated result
      is compared against. For more details see
      :class:`~qblox_scheduler.operations.acquisition_library.ThresholdedAcquisition`.


   .. py:attribute:: num_points
      :type:  int
      :value: None


      Number of data points to be acquired during the measurement.

      This parameter defines how many discrete data points will be collected
      in the course of a single measurement sequence.


.. py:class:: ReferenceMagnitude(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule which describes an amplitude / power reference level.

   The reference level is with respect to which pulse amplitudes are defined.
   This can be specified in units of "V", "dBm" or "A".

   Only one unit parameter may have a defined value at a time. If we call the
   set method for any given unit parameter, all other unit parameters will be
   automatically set to nan.


   .. py:attribute:: dBm
      :type:  float
      :value: None



   .. py:attribute:: V
      :type:  float
      :value: None



   .. py:attribute:: A
      :type:  float
      :value: None



   .. py:attribute:: unit_params
      :type:  ClassVar[frozenset[str]]


   .. py:method:: get_val_unit() -> tuple[float, str]

      Get the value of the amplitude reference and its unit, if one is defined.

      If a value is defined for more than one unit, raise an exception.

      :returns: value
                    The value of the amplitude reference
                unit
                    The unit in which this value is specified




.. py:class:: BasicTransmonElement(/, name, **data: Any)

   Bases: :py:obj:`qblox_scheduler.device_under_test.device_element.DeviceElement`


   A device element representing a single fixed-frequency transmon qubit.

   The qubit is coupled to a readout resonator.


   .. admonition:: Examples

       Qubit parameters can be set through submodule attributes

       .. jupyter-execute::

           from qblox_scheduler import BasicTransmonElement

           device_element = BasicTransmonElement("q3")

           device_element.rxy.amp180 = 0.1
           device_element.measure.pulse_amp = 0.25
           device_element.measure.pulse_duration = 300e-9
           device_element.measure.acq_delay = 430e-9
           device_element.measure.integration_time = 1e-6
           ...

   :param name: The name of the transmon element.
   :param kwargs: Can be used to pass submodule initialization data by using submodule name
                  as keyword and as argument a dictionary containing the submodule parameter
                  names and their value.


   .. py:attribute:: element_type
      :type:  Literal['BasicTransmonElement']
      :value: 'BasicTransmonElement'



   .. py:attribute:: reset
      :type:  IdlingReset


   .. py:attribute:: rxy
      :type:  RxyDRAG


   .. py:attribute:: measure
      :type:  DispersiveMeasurement


   .. py:attribute:: pulse_compensation
      :type:  PulseCompensationModule


   .. py:attribute:: ports
      :type:  Ports


   .. py:attribute:: clock_freqs
      :type:  ClocksFrequencies


   .. py:method:: _generate_config() -> dict[str, dict[str, qblox_scheduler.backends.graph_compilation.OperationCompilationConfig]]

      Generate part of the device configuration specific to a single qubit.

      This method is intended to be used when this object is part of a
      device object containing multiple elements.



   .. py:method:: generate_device_config() -> qblox_scheduler.backends.graph_compilation.DeviceCompilationConfig

      Generate a valid device config.

      The config will be used for the qblox-scheduler making use of the
      :func:`~.circuit_to_device.compile_circuit_to_device_with_config_validation` function.

      This enables the settings of this device element to be used in isolation.

      .. note:

          This config is only valid for single qubit experiments.



