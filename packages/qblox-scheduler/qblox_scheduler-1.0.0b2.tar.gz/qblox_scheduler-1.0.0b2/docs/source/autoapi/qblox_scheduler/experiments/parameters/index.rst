parameters
==========

.. py:module:: qblox_scheduler.experiments.parameters 

.. autoapi-nested-parse::

   Module containing the step to a set a parameter.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.experiments.parameters.SetParameter
   qblox_scheduler.experiments.parameters.SetHardwareOption
   qblox_scheduler.experiments.parameters.SetHardwareDescriptionField



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.experiments.parameters._resolve_path
   qblox_scheduler.experiments.parameters._path_to_dict
   qblox_scheduler.experiments.parameters._set_value_checked



.. py:exception:: UndefinedParameterError(operation_name: str, parameter_type: str)

   Bases: :py:obj:`LookupError`


   Raised when a parameter was not previously defined.


.. py:function:: _resolve_path(target: pydantic.BaseModel | dict, path: list[str | int], value: Any) -> tuple[pydantic.BaseModel | dict, str | int, Any]

.. py:function:: _path_to_dict(target: str | int, path: list[str | int], value: Any) -> dict[str | int, Any]

.. py:function:: _set_value_checked(target: pydantic.BaseModel | dict, key: Any, value: Any, create_new: bool) -> None

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



