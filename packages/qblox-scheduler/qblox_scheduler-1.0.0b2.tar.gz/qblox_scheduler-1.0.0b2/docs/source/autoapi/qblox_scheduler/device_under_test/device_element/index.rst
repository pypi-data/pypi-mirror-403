device_element
==============

.. py:module:: qblox_scheduler.device_under_test.device_element 

.. autoapi-nested-parse::

   The module contains definitions for device elements.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.device_under_test.device_element.DeviceElement



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.device_under_test.device_element.is_identifier_without_underscore



.. py:function:: is_identifier_without_underscore(value: str) -> str

   Pydantic validator for names that are valid identifiers but without underscore.


.. py:class:: DeviceElement(/, name, **data: Any)

   Bases: :py:obj:`abc.ABC`, :py:obj:`qblox_scheduler.structure.model.SchedulerBaseModel`


   Create a device element for managing parameters.

   The :class:`~DeviceElement` is responsible for compiling operations applied to that
   specific device element from the quantum-circuit to the quantum-device layer.


   .. py:attribute:: element_type
      :type:  str


   .. py:attribute:: name
      :type:  Annotated[str, AfterValidator(is_identifier_without_underscore)]
      :value: None



   .. py:method:: include_submodule_names(data: Any) -> Any
      :classmethod:


      Fill in the ``name`` attribute of :class:`~DeviceElement` submodules when missing
      (used for YAML deserialization, they are omitted at serialization).



   .. py:method:: dispatch_concrete_model(data: Any, handler: pydantic.ModelWrapValidatorHandler[typing_extensions.Self]) -> typing_extensions.Self
      :classmethod:


      When deserializing a dict representation of a concrete :class:`~DeviceElement`,
      infer the matching class by looking its `element_type` into the model registry
      and return a validated instance of the concrete device element.



   .. py:method:: generate_device_config() -> qblox_scheduler.backends.graph_compilation.DeviceCompilationConfig
      :abstractmethod:


      Generate the device configuration.



