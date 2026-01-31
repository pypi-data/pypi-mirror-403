experiments
===========

.. py:module:: qblox_scheduler.experiments 


Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   experiment/index.rst
   loops/index.rst
   parameters/index.rst
   schedules/index.rst


Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.experiments.Experiment
   qblox_scheduler.experiments.Step
   qblox_scheduler.experiments.Loop
   qblox_scheduler.experiments.SetHardwareDescriptionField
   qblox_scheduler.experiments.SetHardwareOption
   qblox_scheduler.experiments.SetParameter
   qblox_scheduler.experiments.ExecuteSchedule




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



.. py:class:: Loop(domains: dict[qblox_scheduler.operations.variables.Variable, qblox_scheduler.operations.loop_domains.LinearDomain], steps: list[qblox_scheduler.experiments.experiment.Step])

   Bases: :py:obj:`qblox_scheduler.experiments.experiment.Step`


   Experiment step that loops other steps over some values.


   .. py:property:: domains
      :type: dict[qblox_scheduler.operations.variables.Variable, qblox_scheduler.operations.loop_domains.LinearDomain]


      Domains to loop over.


   .. py:property:: steps
      :type: list[qblox_scheduler.experiments.experiment.Step]


      Steps to execute.


   .. py:method:: run(device: qblox_scheduler.device_under_test.QuantumDevice, timeout: int = 10) -> xarray.Dataset | None

      Execute step on quantum device.



.. py:class:: SetHardwareDescriptionField(name: str | int | tuple[str | int, Ellipsis], value: Any, instrument: str, create_new: bool = False)

   Bases: :py:obj:`qblox_scheduler.experiments.experiment.Step`


   Experiment step that sets a hardware description parameter for a given instrument.

   .. rubric:: Example

   .. code-block:: python

       schedule = Schedule("test")
       # corresponds to:
       #   hardware_config = device.generate_hardware_compilation_config()
       #   cluster0_description = hardware_config.hardware_description["cluster0"]
       #   cluster0_description.modules[2].rf_output_on = False
       schedule.add(
           SetHardwareDescriptionField(("modules", 2, "rf_output_on"), False, instrument="cluster0")
       )
       schedule.add(Measure("q0"))

   :param name: one of:

                - a str, corresponding to a hardware option on the port/clock.
                - a tuple of str, corresponding to a nested hardware option on the
                  port/clock
   :param value: Value to set the parameter to.
   :param instrument: Instrument to set the parameter for.
   :param create_new: If True, create a new entry in the hardware configuration if no entry
                      exists for this port-clock and hardware option. Otherwise, raise an
                      error if the entry does not exist. Optional, by default False.


   .. py:property:: instrument
      :type: str


      Instrument to set field for.


   .. py:property:: field
      :type: list[str | int]


      Field path to set.


   .. py:property:: value
      :type: Any


      Field value to set.


   .. py:property:: create_new
      :type: bool


      Whether to create a new configuration field if it did not previously exist.


   .. py:method:: run(device: qblox_scheduler.device_under_test.QuantumDevice, timeout: int = 10) -> None

      Execute step on quantum device.



.. py:class:: SetHardwareOption(name: str | int | tuple[str | int, Ellipsis], value: Any, port: str, create_new: bool = False)

   Bases: :py:obj:`qblox_scheduler.experiments.experiment.Step`


   Experiment step that sets a hardware option for a given port/clock.

   .. rubric:: Example

   .. code-block:: python

       schedule = Schedule("resonator flux spectroscopy")
       with schedule.loop(linspace(36e6, 38e6, 300, DType.FREQUENCY)) as lo_freq:
           # corresponds to:
           #   hardware_config = device.generate_hardware_compilation_config()
           #   hardware_options = hardware_config.hardware_options
           #   hardware_options.modulation_frequencies["q0:mw-q0.f_larmor"].lo_freq = lo_freq
           schedule.add(
               SetHardwareOption(("modulation_frequencies", "lo_freq"), lo_freq, port="q0:mw-q0.f_larmor")
           )
           schedule.add(Measure("q0"))

   :param name: One of:

                - a str, corresponding to a hardware option on the port/clock.
                - a tuple of str, corresponding to a nested hardware option on the
                  port/clock
   :param value: Value to set the option to.
   :param port: Port/clock combination to set the option for.
   :param create_new: If True, create a new entry in the hardware configuration if no entry
                      exists for this port-clock and hardware option. Otherwise, raise an
                      error if the entry does not exist. Optional, by default False.


   .. py:property:: port
      :type: str


      Port/clock combination to set option for.


   .. py:property:: option
      :type: list[str | int]


      Option name to set.


   .. py:property:: value
      :type: Any


      Option value to set.


   .. py:property:: create_new
      :type: bool


      Whether to create a new configuration field if it did not previously exist.


   .. py:method:: run(device: qblox_scheduler.device_under_test.QuantumDevice, timeout: int = 10) -> None

      Execute step on quantum device.



.. py:class:: SetParameter(name: qcodes.parameters.Parameter | str | int | tuple[str | int, Ellipsis], value: Any, element: str | None = None, create_new: bool = False)

   Bases: :py:obj:`qblox_scheduler.experiments.experiment.Step`


   Experiment step that sets a QCoDeS parameter, or device element parameter.

   .. rubric:: Examples

   Set a QCoDeS parameter:

   .. code-block:: python

       dc_offset = agent.get_clusters()["cluster0"].module4.out0_offset

       schedule = Schedule("resonator flux spectroscopy")
       with schedule.loop(linspace(0, 0.5, 30, DType.NUMBER)) as offset:
           schedule.add(SetParameter(dc_offset, offset))
           with schedule.loop(linspace(360e6, 380e6, 300, DType.FREQUENCY)) as freq:
               schedule.add(Reset("q0"))
               schedule.add(
                   Measure("q0", freq=freq, coords={"frequency": freq, "dc_offset": offset})
               )
               schedule.add(IdlePulse(4e-9))

   Set a device element parameter:

   .. code-block:: python

       schedule = Schedule("hello")
       with schedule.loop(linspace(0, 0.5, 3, DType.AMPLITUDE)) as amp:
           # corresponds to q0.measure.pulse_amp = amp
           schedule.add(SetParameter(("measure", "pulse_amp"), amp, element="q0"))
           schedule.add(Reset("q0"))
           schedule.add(
               Measure("q0", coords={"frequency": freq, "pulse_amp": amp})
           )

   :param name: One of:

                - QCoDeS parameter
                - a str, corresponding to a parameter on the quantum device.
                - a tuple of str, corresponding to a nested parameter on the
                  quantum device or device element or edge.
   :param value: Value to set the parameter to.
   :param element: Optional. If provided, the parameter is set on the device element with the given name.
   :param create_new: If True, create a new entry in the device configuration if no entry
                      exists for this port-clock and hardware option. Otherwise, raise an
                      error if the entry does not exist. Optional, by default False.


   .. py:property:: element
      :type: str | None


      Element to set QCoDeS parameter on.


   .. py:property:: parameter
      :type: list[str | int] | qcodes.parameters.Parameter


      QCoDeS parameter name to set.


   .. py:property:: value
      :type: Any


      QCoDeS parameter value to set.


   .. py:property:: create_new
      :type: bool


      Whether to create a new parameter if it did not previously exist.


   .. py:method:: run(device: qblox_scheduler.device_under_test.QuantumDevice, timeout: int = 10) -> None

      Execute step on quantum device.



.. py:class:: ExecuteSchedule(schedule: qblox_scheduler.schedules.schedule.TimeableScheduleBase)

   Bases: :py:obj:`qblox_scheduler.experiments.experiment.Step`


   Experiment step that runs a schedule.


   .. py:attribute:: compiled_schedule
      :type:  qblox_scheduler.schedules.schedule.CompiledSchedule | None
      :value: None



   .. py:property:: schedule
      :type: qblox_scheduler.schedules.schedule.TimeableScheduleBase


      The schedule to run.


   .. py:method:: run(device: qblox_scheduler.device_under_test.QuantumDevice, timeout: int = 10) -> xarray.Dataset

      Run a schedule on the quantum device.



