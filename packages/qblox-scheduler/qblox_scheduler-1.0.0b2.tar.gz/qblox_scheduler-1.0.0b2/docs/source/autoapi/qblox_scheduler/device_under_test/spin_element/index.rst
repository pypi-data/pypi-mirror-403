spin_element
============

.. py:module:: qblox_scheduler.device_under_test.spin_element 

.. autoapi-nested-parse::

   The module contains definitions related to spin qubit elements.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.device_under_test.spin_element.PortsChargeSensor
   qblox_scheduler.device_under_test.spin_element.PortsSpin
   qblox_scheduler.device_under_test.spin_element.ClocksFrequenciesSensor
   qblox_scheduler.device_under_test.spin_element.ClocksFrequenciesSpin
   qblox_scheduler.device_under_test.spin_element.RxyGaussian
   qblox_scheduler.device_under_test.spin_element.DispersiveMeasurementSpin
   qblox_scheduler.device_under_test.spin_element.BasicSpinElement
   qblox_scheduler.device_under_test.spin_element.ChargeSensor




.. py:class:: PortsChargeSensor(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing the ports.


   .. py:attribute:: gate
      :type:  str
      :value: ''


      Name of the element's ohmic gate port.


   .. py:attribute:: readout
      :type:  str
      :value: ''


      Name of the element's readout port.


   .. py:method:: _fill_defaults() -> None


.. py:class:: PortsSpin(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`PortsChargeSensor`


   Submodule containing the ports.


   .. py:attribute:: microwave
      :type:  str
      :value: ''


      Name of the element's microwave port.


   .. py:method:: _fill_defaults() -> None


.. py:class:: ClocksFrequenciesSensor(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing the clock frequencies specifying the transitions to address.


   .. py:attribute:: readout
      :type:  float
      :value: None


      Frequency of the ro clock.


.. py:class:: ClocksFrequenciesSpin(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`ClocksFrequenciesSensor`


   Submodule containing the clock frequencies specifying the transitions to address.


   .. py:attribute:: f_larmor
      :type:  float
      :value: None


      Larmor frequency for the spin device element


.. py:class:: RxyGaussian(name: str, parent: qblox_scheduler.device_under_test.device_element.DeviceElement | None = None, *, reference_magnitude_dBm: float = math.nan, reference_magnitude_V: float = math.nan, reference_magnitude_A: float = math.nan, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing parameters for performing an Rxy operation.

   The Rxy operation uses a Gaussian pulse.


   .. py:attribute:: reference_magnitude


   .. py:attribute:: amp180
      :type:  float
      :value: None


      Amplitude required to perform a $\pi$ pulse.


   .. py:attribute:: duration
      :type:  float
      :value: None


      Duration of the control pulse.


.. py:class:: DispersiveMeasurementSpin(name: str, parent: qblox_scheduler.device_under_test.device_element.DeviceElement | None = None, *, reference_magnitude_dBm: float = math.nan, reference_magnitude_V: float = math.nan, reference_magnitude_A: float = math.nan, **data: Any)

   Bases: :py:obj:`qblox_scheduler.device_under_test.transmon_element.DispersiveMeasurement`


   Submodule containing parameters to perform a measurement.

   The measurement that is performed is using
   :func:`~qblox_scheduler.operations.measurement_factories.dispersive_measurement_spin`.


   .. py:attribute:: gate_pulse_amp
      :type:  float
      :value: None


      Amplitude of the gate pulse.


   .. py:attribute:: integration_time
      :type:  float
      :value: None


      Integration time for the readout acquisition.


.. py:class:: BasicSpinElement(/, name, **data: Any)

   Bases: :py:obj:`qblox_scheduler.device_under_test.device_element.DeviceElement`


   A device element representing a Loss-DiVincenzo Spin qubit.
   The element refers to the intrinsic spin-1/2 degree of freedom of
   individual electrons/holes trapped in quantum dots.
   The charge of the particle is coupled to a resonator.

   .. admonition:: Examples

       Qubit parameters can be set through submodule attributes

       .. jupyter-execute::

           from qblox_scheduler import BasicSpinElement

           device_element = BasicSpinElement("q1")

           device_element.rxy.amp180 = 0.1
           device_element.measure.pulse_amp = 0.25
           device_element.measure.pulse_duration = 300e-9
           device_element.measure.acq_delay = 430e-9
           device_element.measure.integration_time = 1e-6
           ...


   :param name: The name of the spin element.
   :param kwargs: Can be used to pass submodule initialization data by using submodule name
                  as keyword and as argument a dictionary containing the submodule parameter
                  names and their value.


   .. py:attribute:: element_type
      :type:  Literal['BasicSpinElement']
      :value: 'BasicSpinElement'



   .. py:attribute:: reset
      :type:  qblox_scheduler.device_under_test.transmon_element.IdlingReset


   .. py:attribute:: rxy
      :type:  RxyGaussian


   .. py:attribute:: measure
      :type:  DispersiveMeasurementSpin


   .. py:attribute:: pulse_compensation
      :type:  qblox_scheduler.device_under_test.transmon_element.PulseCompensationModule


   .. py:attribute:: ports
      :type:  PortsSpin


   .. py:attribute:: clock_freqs
      :type:  ClocksFrequenciesSpin


   .. py:method:: _generate_config() -> dict[str, dict[str, qblox_scheduler.backends.graph_compilation.OperationCompilationConfig]]

      Generate part of the device configuration specific to a single qubit trapped in a quantum
      dot. A resonator to perform dispersive readout is attached to the gate to perform charge
      sensing.

      This method is intended to be used when this object is part of a
      device object containing multiple elements.



   .. py:method:: generate_device_config() -> qblox_scheduler.backends.graph_compilation.DeviceCompilationConfig

      Generate a valid device config.

      The config will be used for the qblox-scheduler making use of the
      :func:`~.circuit_to_device.compile_circuit_to_device_with_config_validation` function.

      This enables the settings of this qubit to be used in isolation.

      .. note:

          This config is only valid for single qubit experiments.



.. py:class:: ChargeSensor(/, name, **data: Any)

   Bases: :py:obj:`qblox_scheduler.device_under_test.device_element.DeviceElement`


   A device element representing a Charge Sensor connected to a tank circuit to perform
   dispersive readout.

   .. admonition:: Examples

       Sensor parameters can be set through submodule attributes

       .. jupyter-execute::

           from qblox_scheduler import ChargeSensor

           sensor = ChargeSensor("s1")

           sensor.measure.pulse_amp = 0.25
           sensor.measure.pulse_duration = 300e-9
           sensor.measure.acq_delay = 430e-9
           sensor.measure.integration_time = 1e-6
           ...

   :param name: The name of the spin element.
   :param kwargs: Can be used to pass submodule initialization data by using submodule name
                  as keyword and as argument a dictionary containing the submodule parameter
                  names and their value.


   .. py:attribute:: element_type
      :type:  Literal['ChargeSensor']
      :value: 'ChargeSensor'



   .. py:attribute:: measure
      :type:  DispersiveMeasurementSpin


   .. py:attribute:: pulse_compensation
      :type:  qblox_scheduler.device_under_test.transmon_element.PulseCompensationModule


   .. py:attribute:: ports
      :type:  PortsChargeSensor


   .. py:attribute:: clock_freqs
      :type:  ClocksFrequenciesSensor


   .. py:method:: _generate_config() -> dict[str, dict[str, qblox_scheduler.backends.graph_compilation.OperationCompilationConfig]]

      Generate part of the device configuration specific to a single qubit.

      This method is intended to be used when this object is part of a
      device object containing multiple elements.



   .. py:method:: generate_device_config() -> qblox_scheduler.backends.graph_compilation.DeviceCompilationConfig

      Generate a valid device config.

      The config will be used for the qblox-scheduler making use of the
      :func:`~.circuit_to_device.compile_circuit_to_device_with_config_validation` function.

      This enables the settings of this qubit to be used in isolation.

      .. note:

          This config is only valid for single qubit experiments.



