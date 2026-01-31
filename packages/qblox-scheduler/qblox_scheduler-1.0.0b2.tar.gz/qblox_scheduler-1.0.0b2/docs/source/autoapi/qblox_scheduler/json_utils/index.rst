json_utils
==========

.. py:module:: qblox_scheduler.json_utils 

.. autoapi-nested-parse::

   Module containing quantify JSON utilities.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.json_utils.JSONSchemaValMixin
   qblox_scheduler.json_utils.SchedulerJSONDecoder
   qblox_scheduler.json_utils.SchedulerJSONEncoder
   qblox_scheduler.json_utils.JSONSerializable



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.json_utils.validate_json
   qblox_scheduler.json_utils.load_json_schema
   qblox_scheduler.json_utils.load_json_schema_url
   qblox_scheduler.json_utils.load_json_validator



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.json_utils.lru_cache
   qblox_scheduler.json_utils.DEFAULT_TYPES


.. py:data:: lru_cache

.. py:data:: DEFAULT_TYPES

.. py:function:: validate_json(data: dict, schema: str) -> object

   Validate schema using jsonschema-rs.


.. py:function:: load_json_schema(relative_to: str | pathlib.Path, filename: str) -> str

   Load a JSON schema from file. Expects a 'schemas' directory in the same directory
   as ``relative_to``.

   .. tip::

       Typical usage of the form
       ``schema = load_json_schema(__file__, 'definition.json')``

   :param relative_to: the file to begin searching from
   :param filename: the JSON file to load

   :returns: dict
                 the schema



.. py:function:: load_json_schema_url(relative_to: str | pathlib.Path, url: str) -> str

   Load a JSON schema from ID URL. Expects a 'schemas' directory in the same directory
   as ``relative_to``.

   :param relative_to: the file to begin searching from
   :param url: the JSON ID URL to load

   :returns: dict
                 the schema



.. py:function:: load_json_validator(relative_to: str | pathlib.Path, filename: str) -> collections.abc.Callable

   Load a JSON validator from file. Expects a 'schemas' directory in the same directory
   as ``relative_to``.


   :param relative_to: the file to begin searching from
   :param filename: the JSON file to load

   :returns: Callable
                 The validator



.. py:exception:: UnknownDeserializationTypeError

   Bases: :py:obj:`Exception`


   Raised when an unknown deserialization type is encountered.


.. py:class:: JSONSchemaValMixin

   A mixin that adds validation utilities to classes that have
   a data attribute like a :class:`UserDict` based on JSONSchema.

   This requires the class to have a class variable "schema_filename"


   .. py:attribute:: schema_filename
      :type:  str


   .. py:method:: is_valid(object_to_be_validated: qblox_scheduler.operations.Operation) -> bool
      :classmethod:


      Checks if the object is valid according to its schema.

      :raises fastjsonschema.JsonSchemaException: if the data is invalid

      :returns: :




.. py:class:: SchedulerJSONDecoder(*args, **kwargs)

   Bases: :py:obj:`json.JSONDecoder`


   The Quantify Scheduler JSONDecoder.

   The SchedulerJSONDecoder is used to convert a string with JSON content into
   instances of classes in qblox-scheduler.

   For a few types, :data:`~.DEFAULT_TYPES` contains the mapping from type name to the
   python object. This dictionary can be expanded with classes from modules specified
   in the keyword argument ``modules``.

   Classes not contained in :data:`~.DEFAULT_TYPES` by default must implement
   ``__getstate__``, such that it returns a dictionary containing at least the keys
   ``"deserialization_type"`` and ``"data"``, and ``__setstate__``, which should be
   able to parse the data from ``__getstate__``.

   The value of ``"deserialization_type"`` must be either the name of the class
   specified in :data:`~.DEFAULT_TYPES` or the fully qualified name of the class, which
   can be obtained from
   :func:`~qblox_scheduler.helpers.importers.export_python_object_to_path_string`.

   :keyword modules: A list of custom modules containing serializable classes, by default []
   :kwtype modules: list[ModuleType], Optional


   .. py:attribute:: _classes
      :type:  dict[str, type[Any]]


   .. py:method:: decode_dict(obj: dict[str, Any]) -> dict[str, Any] | numpy.ndarray | object | qcodes.instrument.Instrument

      Returns the deserialized JSON dictionary.

      :param obj: The dictionary to deserialize.

      :returns: :
                    The deserialized result.




   .. py:method:: custom_object_hook(obj: object) -> object

      The ``object_hook`` hook will be called with the result of every JSON object
      decoded and its return value will be used in place of the given ``dict``.

      :param obj: A pair of JSON objects.

      :returns: :
                    The deserialized result.




   .. py:method:: _get_type_from_string(deserialization_type: str) -> type

      Get the python type based on the description string.

      The following methods are tried, in order:

          1. Try to find the string in :data:`~.DEFAULT_TYPES` or the extended modules
              passed to this class' initializer.
          2. Try to import the type. This works only if ``deserialization_type`` is
              formatted as a dot-separated path to the type. E.g.
              ``qblox_scheduler.json_utils.SchedulerJSONDecoder``.

      :param deserialization_type: Description of a type.

      :raises UnknownDeserializationTypeError: If the type cannot be found by any of the methods described.

      :returns: Type
                    The ``Type`` found.




.. py:class:: SchedulerJSONEncoder(*, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, sort_keys=False, indent=None, separators=None, default=None)

   Bases: :py:obj:`json.JSONEncoder`


   Custom JSONEncoder which encodes a Quantify Scheduler object into a JSON file format
   string.


   .. py:method:: default(o: object) -> object

      Overloads the json.JSONEncoder default method that returns a serializable
      object. It will try 3 different serialization methods which are, in order,
      check if the object is to be serialized to a string using repr. If not, try
      to use ``__getstate__``. Finally, try to serialize the ``__dict__`` property.



.. py:class:: JSONSerializable

   Mixin to allow de/serialization of arbitrary objects using :class:`~SchedulerJSONEncoder`
   and :class:`~SchedulerJSONDecoder`.


   .. py:method:: to_dict() -> dict[str, Any]

      Convert the object to a dictionary representation.

      :returns: Dictionary representation of the object.




   .. py:method:: from_dict(data: dict[str, Any]) -> typing_extensions.Self
      :classmethod:


      Convert a dictionary to an instance of the attached class.

      :param data: The dictionary data to convert.

      :returns: The deserialized object.




   .. py:method:: to_json() -> str

      Convert the object's data structure to a JSON string.

      :returns: :
                    The json string containing the serialized object.




   .. py:method:: to_json_file(path: str | None = None, add_timestamp: bool = True) -> str

      Convert the object's data structure to a JSON string and store it in a file.

      .. rubric:: Examples

      Saving a :class:`~qblox_scheduler.QuantumDevice` will use its name and current timestamp

      .. code-block:: python

          from qblox_scheduler import QuantumDevice

          single_qubit_device = QuantumDevice("single_qubit_device")
          ...
          single_qubit_device.to_json_file()

          single_qubit_device = QuantumDevice.from_json_file("/tmp/single_qubit_device_2024-11-14_13-36-59_UTC.json")

      :param path: The path to the directory where the file is created. Default
                   is `None`, in which case the file will be saved in the directory
                   determined by :func:`~qblox_scheduler.analysis.data_handling.OutputDirectoryManager.get_datadir()`.
      :param add_timestamp: Specify whether to append timestamp to the filename.
                            Default is True.

      :returns: :
                    The name of the file containing the serialized object.




   .. py:method:: from_json(data: str) -> typing_extensions.Self
      :classmethod:


      Convert the JSON data to an instance of the attached class.

      :param data: The JSON data in str format.

      :returns: :
                    The deserialized object.




   .. py:method:: from_json_file(filename: str | pathlib.Path) -> typing_extensions.Self
      :classmethod:


      Read JSON data from a file and convert it to an instance of the attached class.

      .. rubric:: Examples

      .. code-block:: python

          from qblox_scheduler import QuantumDevice

          single_qubit_device = QuantumDevice.from_json_file("/tmp/single_qubit_device_2024-11-14_13-36-59_UTC.json")

      :param filename: The name of the file containing the serialized object.

      :returns: :
                    The deserialized object.




