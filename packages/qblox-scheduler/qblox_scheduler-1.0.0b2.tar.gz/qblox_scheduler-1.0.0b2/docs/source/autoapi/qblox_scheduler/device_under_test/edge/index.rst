edge
====

.. py:module:: qblox_scheduler.device_under_test.edge 

.. autoapi-nested-parse::

   The module contains definitions for edges.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.device_under_test.edge.Edge




.. py:class:: Edge(parent_element: qblox_scheduler.device_under_test.device_element.DeviceElement | str | None = None, child_element: qblox_scheduler.device_under_test.device_element.DeviceElement | str | None = None, **data: Any)

   Bases: :py:obj:`abc.ABC`, :py:obj:`qblox_scheduler.structure.model.SchedulerBaseModel`


   Create an Edge.

   This class encapsulates the connection information between DeviceElements in the
   QuantumDevice. It provides an interface for the QuantumDevice to generate the
   edge information for use in the device compilation step. See
   :class:`qblox_scheduler.device_under_test.composite_square_edge` for an example
   edge implementation.


   .. py:attribute:: edge_type
      :type:  str


   .. py:attribute:: parent_element_name
      :type:  str


   .. py:attribute:: child_element_name
      :type:  str


   .. py:attribute:: _parent_device_element
      :type:  qblox_scheduler.device_under_test.device_element.DeviceElement | None
      :value: None



   .. py:attribute:: _child_device_element
      :type:  qblox_scheduler.device_under_test.device_element.DeviceElement | None
      :value: None



   .. py:method:: include_submodule_names(data: Any) -> Any
      :classmethod:


      Fill in the ``name`` attribute of :class:`~Edge` submodules when missing
      (used for YAML deserialization, they are omitted at serialization).



   .. py:method:: dispatch_concrete_model(data: Any, handler: pydantic.ModelWrapValidatorHandler[typing_extensions.Self]) -> typing_extensions.Self
      :classmethod:


      When deserializing a dict representation of a concrete :class:`~Edge`,
      infer the matching class by looking its `edge_type` into the model registry
      and return a validated instance of the concrete edge.



   .. py:property:: parent_element
      :type: qblox_scheduler.device_under_test.device_element.DeviceElement | None


      Getter for the internal parent device element.


   .. py:property:: child_element
      :type: qblox_scheduler.device_under_test.device_element.DeviceElement | None


      Getter for the internal child device element.


   .. py:property:: submodules
      :type: dict[str, Any]


      Mapping of submodules of this edge.


   .. py:method:: _get_element_name(element: qblox_scheduler.device_under_test.device_element.DeviceElement | dict | str | None) -> str
      :staticmethod:


      Get the name of an element represented as a `DeviceElement` instance,
      dictionary or string.



   .. py:method:: generate_edge_config() -> dict[str, dict[str, qblox_scheduler.backends.graph_compilation.OperationCompilationConfig]]
      :abstractmethod:


      Generate the device configuration for an edge.

      This method is intended to be used when this object is part of a
      device object containing multiple elements.



