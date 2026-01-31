quantum_device
==============

.. py:module:: qblox_scheduler.device_under_test.quantum_device 

.. autoapi-nested-parse::

   Module containing the QuantumDevice object.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.device_under_test.quantum_device.QuantumDevice




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.device_under_test.quantum_device.ConcreteDeviceElement
   qblox_scheduler.device_under_test.quantum_device.ConcreteEdge


.. py:data:: ConcreteDeviceElement

.. py:data:: ConcreteEdge

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



