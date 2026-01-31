operation
=========

.. py:module:: qblox_scheduler.operations.operation 

.. autoapi-nested-parse::

   Module containing the core concepts of the scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.operation.Operation



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.operation._generate_acq_indices_for_gate



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.operation.logger
   qblox_scheduler.operations.operation.cached_locate


.. py:data:: logger

.. py:data:: cached_locate

.. py:class:: Operation(name: str)

   Bases: :py:obj:`qblox_scheduler.json_utils.JSONSchemaValMixin`, :py:obj:`collections.UserDict`


   A representation of quantum circuit operations.

   The :class:`~Operation` class is a JSON-compatible data structure that contains information
   on how to represent the operation on the quantum-circuit and/or the quantum-device
   layer. It also contains information on where the operation should be applied: the
   :class:`~qblox_scheduler.resources.Resource` s used.

   An operation always has the following attributes:

   - duration (float): duration of the operation in seconds (can be 0).
   - hash (str): an auto generated unique identifier.
   - name (str): a readable identifier, does not have to be unique.



   An Operation can contain information  on several levels of abstraction.
   This information is used when different representations are required. Note that when
   initializing an operation  not all of this information needs to be available
   as operations are typically modified during the compilation steps.

   .. tip::

       :mod:`qblox_scheduler` comes with a
       :mod:`~qblox_scheduler.operations.gate_library` and a
       :mod:`~qblox_scheduler.operations.pulse_library` , both containing common
       operations.


   **JSON schema of a valid Operation**

   .. jsonschema:: https://gitlab.com/qblox/packages/software/qblox-scheduler/-/raw/main/src/qblox_scheduler/schemas/operation.json


   .. note::

       Two different Operations containing the same information generate the
       same hash and are considered identical.


   .. py:attribute:: schema_filename
      :value: 'operation.json'



   .. py:attribute:: _class_signature
      :value: None



   .. py:attribute:: _duration
      :type:  float
      :value: 0



   .. py:method:: clone() -> Operation

      Clone this operation into a new independent operation.



   .. py:method:: substitute(substitutions: dict[qblox_scheduler.operations.expressions.Expression, qblox_scheduler.operations.expressions.Expression | int | float | complex]) -> Operation

      Substitute matching expressions in operand, possibly evaluating a result.



   .. py:property:: name
      :type: str


      Return the name of the operation.


   .. py:property:: duration
      :type: float


      Determine operation duration from pulse_info.

      If the operation contains no pulse info, it is assumed to be ideal and
      have zero duration.


   .. py:property:: hash
      :type: str


      A hash based on the contents of the Operation.

      Needs to be a str for easy compatibility with json.


   .. py:method:: _get_signature(parameters: dict) -> str
      :classmethod:


      Returns the constructor call signature of this instance for serialization.

      The string constructor representation can be used to recreate the object
      using eval(signature).

      :param parameters: The current data dictionary.
      :type parameters: dict

      :returns: :




   .. py:method:: add_gate_info(gate_operation: Operation) -> None

      Updates self.data['gate_info'] with contents of gate_operation.

      :param gate_operation: an operation containing gate_info.



   .. py:method:: add_device_representation(device_operation: Operation) -> None

      Adds device-level representation details to the current operation.

      :param device_operation: an operation containing the pulse_info and/or acquisition info describing
                               how to represent the current operation at the quantum-device layer.



   .. py:method:: get_used_port_clocks() -> set[tuple[str, str]]

      Extracts which port-clock combinations are used in this operation.

      :returns: :
                    All (port, clock) combinations this operation uses.




   .. py:method:: is_valid(object_to_be_validated: Operation) -> bool
      :classmethod:


      Validates the object's contents against the schema.

      Additionally, checks if the hash property of the object evaluates correctly.



   .. py:property:: valid_gate
      :type: bool


      An operation is a valid gate if it has gate-level representation details.


   .. py:property:: valid_pulse
      :type: bool


      An operation is a valid pulse if it has pulse-level representation details.


   .. py:property:: valid_acquisition
      :type: bool


      An operation is a valid acquisition
      if it has pulse-level acquisition representation details.


   .. py:property:: is_conditional_acquisition
      :type: bool


      An operation is conditional if one of the following holds, ``self`` is an
      an acquisition with a ``feedback_trigger_label`` assigned to it.


   .. py:property:: is_control_flow
      :type: bool


      Determine if operation is a control flow operation.

      :returns: bool
                    Whether the operation is a control flow operation.


   .. py:property:: has_voltage_offset
      :type: bool


      Checks if the operation contains information for a voltage offset.


.. py:function:: _generate_acq_indices_for_gate(device_elements: list[str], acq_index: collections.abc.Sequence[int] | collections.abc.Sequence[None] | int | None) -> int | None | collections.abc.Iterable[int] | collections.abc.Iterable[None]

