experiment
==========

.. py:module:: qblox_scheduler.experiments.experiment 

.. autoapi-nested-parse::

   Module containing the core experiment concepts.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.experiments.experiment.Step
   qblox_scheduler.experiments.experiment.Experiment




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.experiments.experiment.logger


.. py:data:: logger

.. py:class:: Step(name: str)

   Bases: :py:obj:`qblox_scheduler.json_utils.JSONSchemaValMixin`, :py:obj:`collections.UserDict`, :py:obj:`abc.ABC`


   A step containing a single (possibly) near-time operation to be performed in an experiment.

   An `Experiment` consists of steps, each of which performs a specific operation
   (usually on hardware). There is no real-time guarantee between steps, as opposed to `Operation`.


   .. py:attribute:: schema_filename
      :value: 'step.json'



   .. py:attribute:: _class_signature
      :value: None



   .. py:method:: _update() -> None

      Update the Step's internals.



   .. py:method:: clone() -> Step

      Clone this operation into a new independent operation.



   .. py:method:: substitute(substitutions: dict[qblox_scheduler.operations.expressions.Expression, qblox_scheduler.operations.expressions.Expression | int | float | complex]) -> Step

      Substitute matching expressions in operand, possibly evaluating a result.



   .. py:property:: name
      :type: str


      Return the name of the step.


   .. py:method:: _get_signature(parameters: dict) -> str
      :classmethod:


      Returns the constructor call signature of this instance for serialization.

      The string constructor representation can be used to recreate the object
      using eval(signature).

      :param parameters: The current data dictionary.
      :type parameters: dict

      :returns: :




   .. py:method:: run(device: qblox_scheduler.device_under_test.QuantumDevice, timeout: int) -> xarray.Dataset | None
      :abstractmethod:


      Execute step on quantum device.



.. py:class:: Experiment(name: str, data: dict[str, Any] | None = None)

   Bases: :py:obj:`qblox_scheduler.json_utils.JSONSchemaValMixin`, :py:obj:`qblox_scheduler.json_utils.JSONSerializable`, :py:obj:`collections.UserDict`


   An experiment.


   .. py:attribute:: schema_filename
      :value: 'experiment.json'



   .. py:property:: name
      :type: str


      Return the name of the experiment.


   .. py:property:: steps
      :type: list[Step]


      Return the steps in the experiment.


   .. py:method:: declare(dtype: qblox_scheduler.operations.expressions.DType) -> qblox_scheduler.operations.variables.Variable

      Declare a variable.

      :param dtype: The variable type.



   .. py:method:: define(var: qblox_scheduler.operations.variables.Variable) -> None

      Add a declared variable.

      :param var: The variable.



   .. py:method:: add(step: Step) -> None

      Add step to experiment.



   .. py:method:: run(device: qblox_scheduler.device_under_test.QuantumDevice, timeout: int = 10) -> xarray.Dataset

      Run experiment on quantum device.



   .. py:method:: clone() -> Experiment

      Clone this schedule into a separate independent experiment.



   .. py:method:: substitute(substitutions: dict[qblox_scheduler.operations.expressions.Expression, qblox_scheduler.operations.expressions.Expression | int | float | complex]) -> Experiment

      Substitute matching expressions in this experiment.



