model
=====

.. py:module:: qblox_scheduler.structure.model 

.. autoapi-nested-parse::

   Root models for data structures used within the package.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.structure.model.Numbers
   qblox_scheduler.structure.model._SerializableBaseModel
   qblox_scheduler.structure.model.SchedulerBaseModel
   qblox_scheduler.structure.model.SchedulerSubmodule
   qblox_scheduler.structure.model.DataStructure



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.structure.model.Parameter
   qblox_scheduler.structure.model.is_identifier
   qblox_scheduler.structure.model.deserialize_function
   qblox_scheduler.structure.model.deserialize_class



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.structure.model._Unset


.. py:data:: _Unset
   :type:  Any

.. py:class:: Numbers

   Bases: :py:obj:`TypedDict`


   Dict used to emulate the behaviour of the ``Numbers`` qcodes validator.


   .. py:attribute:: min_value
      :type:  float


   .. py:attribute:: max_value
      :type:  float


   .. py:attribute:: allow_nan
      :type:  bool


.. py:function:: Parameter(*, initial_value: Any = _Unset, label: str | None = _Unset, docstring: str | None = _Unset, unit: str | None = _Unset, vals: Numbers | None = _Unset, **kwargs: Any) -> Any

   Wrapper function around `:func:~pydantic.Field` that tries to emulate qcodes parameters
   as closely as possible, to facilitate migration and reduce diff lines.

   :param initial_value: Maps to ``default`` or ``default_factory`` (if callable).
   :param label: Maps to ``title``, displayed on the JSON schema.
   :param docstring: Maps to ``description``, displayed on the JSON schema.
   :param unit: Stored internally, retrievable using :meth:`~SchedulerBaseModel.get_unit`.
   :param vals: Maps to ``allow_inf_nan``, ``ge`` and ``le``.
   :param kwargs: Other arguments passed on to the original ``Field`` function.

   :returns: Any:
                 To appease the linters; actually a `:class:~pydantic.fields.FieldInfo` instance.



.. py:function:: is_identifier(value: str) -> str

   Pydantic validator for names that are valid identifiers.


.. py:class:: _SerializableBaseModel(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Mixin class that enables dict, JSON and YAML serialization and deserialization
   by attaching `to_` and `from_` helper methods.


   .. py:method:: to_dict() -> dict[str, Any]

      Alias for `BaseModel.model_dump`.



   .. py:method:: from_dict(data: dict[str, Any]) -> typing_extensions.Self
      :classmethod:


      Alias for `BaseModel.model_validate`.



   .. py:method:: to_json(indent: int | None = None) -> str

      Alias for `BaseModel.model_dump_json`.



   .. py:method:: from_json(json_data: str) -> typing_extensions.Self
      :classmethod:


      Alias for `BaseModel.model_validate_json`.



   .. py:method:: _generate_file_name(path: str | None, add_timestamp: bool, extension: str) -> str

      Generate a file name to be used by `to_*_file` methods.



   .. py:method:: to_json_file(path: str | None = None, add_timestamp: bool = True) -> str

      Convert the object's data structure to a JSON string and store it in a file.



   .. py:method:: from_json_file(filename: str | pathlib.Path) -> typing_extensions.Self
      :classmethod:


      Read JSON data from a file and convert it to an instance of the attached class.



   .. py:method:: to_yaml() -> str

      Convert the object's data structure to a YAML string.

      For performance reasons, to save to file use :meth:`~to_yaml_file` instead.



   .. py:method:: from_yaml(yaml_data: str) -> typing_extensions.Self
      :classmethod:


      Convert YAML data to an instance of the attached class.

      For performance reasons, to load from file use :meth:`~from_yaml_file` instead.



   .. py:method:: to_yaml_file(path: str | None = None, add_timestamp: bool = True) -> str

      Convert the object's data structure to a YAML string and store it in a file.



   .. py:method:: from_yaml_file(filename: str | pathlib.Path) -> typing_extensions.Self
      :classmethod:


      Read YAML data from a file and convert it to an instance of the attached class.



.. py:class:: SchedulerBaseModel(/, name, **data: Any)

   Bases: :py:obj:`_SerializableBaseModel`


   Pydantic base model to support qcodes-style instrument and parameter definitions.


   .. py:attribute:: model_config

      Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].


   .. py:attribute:: name
      :type:  Annotated[str, AfterValidator(is_identifier)]
      :value: None



   .. py:property:: parameters
      :type: dict[str, Any]


      Mapping of parameters of this element.


   .. py:property:: submodules
      :type: dict[str, Any]


      Mapping of submodules of this element.


   .. py:method:: get_unit(field_name: str) -> str | None
      :classmethod:


      Get the unit declared for a certain field/parameter.



   .. py:method:: create_submodule_instances(data: Any) -> Any
      :classmethod:


      During model instantiation, create an empty/default instance of all submodules.



   .. py:method:: fill_submodule_parent_defaults() -> typing_extensions.Self

      After module creation, for each submodule, fill in the default values for fields
      that read from an attribute of the parent model.



   .. py:method:: close() -> None

      Does nothing.



   .. py:method:: close_all() -> None
      :classmethod:


      Does nothing.



.. py:class:: SchedulerSubmodule(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`SchedulerBaseModel`


   Compatibility class emulating the behaviour of ``InstrumentModule``/``InstrumentChannel``.


   .. py:attribute:: _parent
      :type:  SchedulerBaseModel | SchedulerSubmodule | None
      :value: None



   .. py:property:: parent
      :type: SchedulerBaseModel | None



.. py:class:: DataStructure(/, **data: Any)

   Bases: :py:obj:`_SerializableBaseModel`


   A parent for all data structures.

   Data attributes are generated from the class' type annotations, similarly to
   `dataclasses <https://docs.python.org/3/library/dataclasses.html>`_. If data
   attributes are JSON-serializable, data structure can be serialized using
   ``json()`` method. This string can be deserialized using ``parse_raw()`` classmethod
   of a correspondent child class.

   If required, data fields can be validated, see examples for more information.
   It is also possible to define custom field types with advanced validation.

   This class is a pre-configured `pydantic <https://docs.pydantic.dev/>`_
   model. See its documentation for details of usage information.

   .. admonition:: Examples
       :class: dropdown

       .. include:: /examples/structure.DataStructure.rst


   .. py:attribute:: model_config

      Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].


.. py:function:: deserialize_function(fun: str) -> collections.abc.Callable[Ellipsis, Any]

   Import a python function from a dotted import string (e.g.,
   "qblox_scheduler.structure.model.deserialize_function").

   :param fun: A dotted import path to a function (e.g.,
               "qblox_scheduler.waveforms.square"), or a function pointer.
   :type fun: str

   :returns: Callable[[Any], Any]


   :raises ValueError: Raised if the function cannot be imported from path in the string.


.. py:function:: deserialize_class(cls: str) -> type

   Import a python class from a dotted import string (e.g.,
   "qblox_scheduler.structure.model.DataStructure").

   :param cls: A dotted import path to a class (e.g.,
               "qblox_scheduler.structure.model.DataStructure"), or a class pointer.
   :type cls: str

   :returns: :
                 The type you are trying to import.

   :raises ValueError: Raised if the class cannot be imported from path in the string.


