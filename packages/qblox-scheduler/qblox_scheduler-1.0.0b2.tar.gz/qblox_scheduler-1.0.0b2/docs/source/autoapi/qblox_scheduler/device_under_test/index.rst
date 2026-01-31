device_under_test
=================

.. py:module:: qblox_scheduler.device_under_test 

.. autoapi-nested-parse::

   Module containing instruments that represent quantum devices and elements.

   The elements and their components are intended to generate valid
   :ref:`device configuration <sec-device-config>` files for compilation from the
   :ref:`quantum-circuit layer <sec-user-guide-quantum-circuit>` to the
   :ref:`quantum-device layer description<sec-user-guide-quantum-device>`.



Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   composite_square_edge/index.rst
   device_element/index.rst
   edge/index.rst
   hardware_config/index.rst
   mock_setup/index.rst
   nv_element/index.rst
   quantum_device/index.rst
   spin_edge/index.rst
   spin_element/index.rst
   transmon_element/index.rst


Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.device_under_test.CompositeSquareEdge
   qblox_scheduler.device_under_test.BasicElectronicNVElement
   qblox_scheduler.device_under_test.QuantumDevice
   qblox_scheduler.device_under_test.SpinEdge
   qblox_scheduler.device_under_test.BasicSpinElement
   qblox_scheduler.device_under_test.ChargeSensor
   qblox_scheduler.device_under_test.BasicTransmonElement




.. py:class:: CompositeSquareEdge(parent_element: qblox_scheduler.device_under_test.device_element.DeviceElement | str | None = None, child_element: qblox_scheduler.device_under_test.device_element.DeviceElement | str | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.device_under_test.edge.Edge`


   An example Edge implementation which connects two BasicTransmonElements.

   This edge implements a square flux pulse and two virtual z
   phase corrections for the CZ operation between the two BasicTransmonElements.


   .. py:attribute:: edge_type
      :type:  Literal['CompositeSquareEdge']
      :value: 'CompositeSquareEdge'



   .. py:attribute:: _parent_device_element
      :type:  qblox_scheduler.device_under_test.transmon_element.BasicTransmonElement | None
      :value: None



   .. py:attribute:: _child_device_element
      :type:  qblox_scheduler.device_under_test.transmon_element.BasicTransmonElement | None
      :value: None



   .. py:attribute:: cz
      :type:  CZ


   .. py:method:: generate_edge_config() -> dict[str, dict[str, qblox_scheduler.backends.graph_compilation.OperationCompilationConfig]]

      Generate valid device config.

      Fills in the edges information to produce a valid device config for the
      qblox-scheduler making use of the
      :func:`~.circuit_to_device.compile_circuit_to_device_with_config_validation` function.



.. py:class:: BasicElectronicNVElement(/, name, **data: Any)

   Bases: :py:obj:`qblox_scheduler.device_under_test.device_element.DeviceElement`


   A device element representing an electronic qubit in an NV center.

   The submodules contain the necessary device element parameters to translate higher-level
   operations into pulses. Please see the documentation of these classes.

   .. admonition:: Examples

       Qubit parameters can be set through submodule attributes

       .. jupyter-execute::

           from qblox_scheduler import BasicElectronicNVElement

           device_element = BasicElectronicNVElement("q2")

           device_element.rxy.amp180 = 0.1
           device_element.measure.pulse_amplitude = 0.25
           device_element.measure.pulse_duration = 300e-9
           device_element.measure.acq_delay = 430e-9
           device_element.measure.acq_duration = 1e-6
           ...



   .. py:attribute:: element_type
      :type:  Literal['BasicElectronicNVElement']
      :value: 'BasicElectronicNVElement'



   .. py:attribute:: spectroscopy_operation
      :type:  SpectroscopyOperationNV


   .. py:attribute:: ports
      :type:  Ports


   .. py:attribute:: clock_freqs
      :type:  ClockFrequencies


   .. py:attribute:: reset
      :type:  ResetSpinpump


   .. py:attribute:: charge_reset
      :type:  ChargeReset


   .. py:attribute:: measure
      :type:  Measure


   .. py:attribute:: pulse_compensation
      :type:  qblox_scheduler.device_under_test.transmon_element.PulseCompensationModule


   .. py:attribute:: cr_count
      :type:  CRCount


   .. py:attribute:: rxy
      :type:  RxyNV


   .. py:method:: _generate_config() -> dict[str, dict[str, qblox_scheduler.backends.graph_compilation.OperationCompilationConfig]]

      Generate part of the device configuration specific to a single qubit.

      This method is intended to be used when this object is part of a
      device object containing multiple elements.



   .. py:method:: generate_device_config() -> qblox_scheduler.backends.graph_compilation.DeviceCompilationConfig

      Generate a valid device config for the qblox-scheduler.

      This makes use of the
      :func:`~.circuit_to_device.compile_circuit_to_device_with_config_validation` function.

      This enables the settings of this qubit to be used in isolation.

      .. note:

          This config is only valid for single qubit experiments.



.. py:class:: QuantumDevice(/, name, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerBaseModel`


   The QuantumDevice directly represents the device under test (DUT).

   This contains a description of the connectivity to the control hardware as
   well as parameters specifying quantities like cross talk, attenuation and
   calibrated cable-delays. The QuantumDevice also contains references to
   individual DeviceElements, representations of elements on a device (e.g, a
   transmon qubit) containing the (calibrated) control-pulse parameters.

   This object can be used to generate configuration files for the compilation step
   from the gate-level to the pulse level description.
   These configuration files should be compatible with the
   :meth:`~qblox_scheduler.backends.graph_compilation.ScheduleCompiler.compile`
   function.


   .. py:attribute:: model_config

      Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].


   .. py:attribute:: elements
      :type:  dict[str, ConcreteDeviceElement]
      :value: None



   .. py:attribute:: edges
      :type:  dict[str, ConcreteEdge]
      :value: None



   .. py:attribute:: instr_instrument_coordinator
      :type:  qblox_scheduler.instrument_coordinator.InstrumentCoordinator | None
      :value: None



   .. py:attribute:: cfg_sched_repetitions
      :type:  pydantic.PositiveInt
      :value: None



   .. py:attribute:: keep_original_schedule
      :type:  bool
      :value: None



   .. py:attribute:: hardware_config
      :type:  qblox_scheduler.backends.types.common.HardwareCompilationConfig | dict | None
      :value: None



   .. py:attribute:: scheduling_strategy
      :type:  qblox_scheduler.enums.SchedulingStrategy
      :value: None



   .. py:method:: validate_instrument_coordinator(value: str | qblox_scheduler.instrument_coordinator.InstrumentCoordinator | None) -> qcodes.instrument.Instrument | None
      :classmethod:


      Load InstrumentCoordinator instance from its name.

      Pydantic doesn't know how to handle a QCoDeS instrument; thus, we have to allow
      arbitrary types and manually fetch them with `find_or_create_instrument`.



   .. py:method:: validate_scheduling_strategy(value: str | qblox_scheduler.enums.SchedulingStrategy) -> qblox_scheduler.enums.SchedulingStrategy
      :classmethod:


      Force `scheduling_strategy` into its proper enum value.



   .. py:method:: validate_elements_and_edges(data: Any, handler: pydantic.ModelWrapValidatorHandler[typing_extensions.Self]) -> typing_extensions.Self
      :classmethod:


      Add elements and edges to the model by calling `add_element` and `add_edge`
      respectively to force our consistency checks.



   .. py:method:: generate_compilation_config() -> qblox_scheduler.backends.graph_compilation.SerialCompilationConfig

      Generate a config for use with a :class:`~.graph_compilation.ScheduleCompiler`.



   .. py:method:: generate_hardware_config() -> dict[str, Any]

      Generate a valid hardware configuration describing the quantum device.

      :returns: The hardware configuration file used for compiling from the quantum-device
                layer to a hardware backend.

      .. warning:

          The config currently has to be specified by the user using the
          :code:`hardware_config` parameter.




   .. py:method:: generate_device_config() -> qblox_scheduler.backends.graph_compilation.DeviceCompilationConfig

      Generate a device config.

      This config is used to compile from the quantum-circuit to the
      quantum-device layer.



   .. py:method:: generate_hardware_compilation_config() -> qblox_scheduler.backends.types.common.HardwareCompilationConfig | None

      Generate a hardware compilation config.

      The compilation config is used to compile from the quantum-device to the
      control-hardware layer.



   .. py:method:: get_element(name: str) -> qblox_scheduler.device_under_test.device_element.DeviceElement

      Return a :class:`~qblox_scheduler.device_under_test.device_element.DeviceElement`
      by name.

      :param name: The element name.

      :returns: :
                    The element.

      :raises KeyError: If key ``name`` is not present in `self.elements`.



   .. py:method:: add_element(element: qblox_scheduler.device_under_test.device_element.DeviceElement) -> None

      Add an element to the elements collection.

      :param element: The element to add.

      :raises ValueError: If an element with a duplicated name is added to the collection.
      :raises TypeError: If :code:`element` is not an instance of the base element.



   .. py:method:: remove_element(name: str) -> None

      Removes an element by name.

      :param name: The element name.
                   Has to follow the convention ``"{element_0}_{element_1}"``.



   .. py:method:: get_edge(name: str) -> qblox_scheduler.device_under_test.edge.Edge

      Returns an edge by name.

      :param name: The edge name.
                   Has to follow the convention ``"{element_0}_{element_1}"``.

      :returns: :
                    The edge.

      :raises KeyError: If key ``name`` is not present in ``self.edges``.



   .. py:method:: add_edge(edge: qblox_scheduler.device_under_test.edge.Edge) -> None

      Add the edges.

      :param edge: The edge to add.



   .. py:method:: remove_edge(name: str) -> None

      Remove an edge by name.

      :param name: The edge name connecting the elements.
                   Has to follow the convention ``"{element_0}_{element_1}"``.



   .. py:method:: from_json_file(filename: str | pathlib.Path) -> typing_extensions.Self
      :classmethod:


      Read JSON data from a file and convert it to an instance of the attached class.



.. py:class:: SpinEdge(parent_element: qblox_scheduler.device_under_test.device_element.DeviceElement | str | None = None, child_element: qblox_scheduler.device_under_test.device_element.DeviceElement | str | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.device_under_test.edge.Edge`


   Spin edge implementation which connects two BasicSpinElements.

   This edge implements some operations between the two BasicSpinElements.


   .. py:attribute:: edge_type
      :type:  Literal['SpinEdge']
      :value: 'SpinEdge'



   .. py:attribute:: _parent_device_element
      :type:  qblox_scheduler.device_under_test.spin_element.BasicSpinElement | None
      :value: None



   .. py:attribute:: _child_device_element
      :type:  qblox_scheduler.device_under_test.spin_element.BasicSpinElement | None
      :value: None



   .. py:attribute:: spin_init
      :type:  SpinInit


   .. py:attribute:: cz
      :type:  CZ


   .. py:attribute:: cnot
      :type:  CNOT


   .. py:attribute:: ports
      :type:  PortSpinEdge


   .. py:method:: generate_edge_config() -> dict[str, dict[str, qblox_scheduler.backends.graph_compilation.OperationCompilationConfig]]

      Generate valid device config.

      Fills in the edges information to produce a valid device config for the
      qblox-scheduler making use of the
      :func:`~.circuit_to_device.compile_circuit_to_device_with_config_validation` function.



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



