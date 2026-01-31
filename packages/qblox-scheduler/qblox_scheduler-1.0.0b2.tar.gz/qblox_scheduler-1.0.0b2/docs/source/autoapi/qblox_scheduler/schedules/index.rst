schedules
=========

.. py:module:: qblox_scheduler.schedules 

.. autoapi-nested-parse::

   Module containing a standard library of schedules for common experiments as well as the
   :class:`.TimeableScheduleBase`, :class:`.TimeableSchedule`, and :class:`.CompiledSchedule` classes.


   .. tip::

       The source code of the schedule generating functions in this module can
       serve as examples when creating schedules for custom experiments.



Subpackages
-----------
.. toctree::
   :titlesonly:
   :maxdepth: 3

   _visualization/index.rst


Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   schedule/index.rst
   spectroscopy_schedules/index.rst
   timedomain_schedules/index.rst
   trace_schedules/index.rst
   two_qubit_transmon_schedules/index.rst
   verification/index.rst


Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules.CompiledSchedule
   qblox_scheduler.schedules.Schedulable
   qblox_scheduler.schedules.TimeableSchedule



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules.heterodyne_spec_sched
   qblox_scheduler.schedules.heterodyne_spec_sched_nco
   qblox_scheduler.schedules.nv_dark_esr_sched
   qblox_scheduler.schedules.two_tone_spec_sched
   qblox_scheduler.schedules.two_tone_spec_sched_nco
   qblox_scheduler.schedules.allxy_sched
   qblox_scheduler.schedules.echo_sched
   qblox_scheduler.schedules.rabi_pulse_sched
   qblox_scheduler.schedules.rabi_sched
   qblox_scheduler.schedules.ramsey_sched
   qblox_scheduler.schedules.readout_calibration_sched
   qblox_scheduler.schedules.t1_sched
   qblox_scheduler.schedules.trace_schedule
   qblox_scheduler.schedules.trace_schedule_circuit_layer
   qblox_scheduler.schedules.two_tone_trace_schedule



.. py:class:: CompiledSchedule(schedule: TimeableSchedule)

   Bases: :py:obj:`TimeableScheduleBase`


   A schedule that contains compiled instructions ready for execution using the :class:`~.InstrumentCoordinator`.

   The :class:`CompiledSchedule` differs from a :class:`.TimeableSchedule` in
   that it is considered immutable (no new operations or resources can be added), and
   that it contains :attr:`~.compiled_instructions`.

   .. tip::

       A :class:`~.TimeableSchedule` can be obtained by compiling a
       :class:`~.TimeableSchedule` using :meth:`~qblox_scheduler.backends.graph_compilation.ScheduleCompiler.compile`.



   .. py:attribute:: schema_filename
      :value: 'schedule.json'



   .. py:attribute:: _hardware_timing_table
      :type:  pandas.DataFrame


   .. py:attribute:: _hardware_waveform_dict
      :type:  dict[str, numpy.ndarray]


   .. py:property:: compiled_instructions
      :type: collections.abc.MutableMapping[str, qblox_scheduler.resources.Resource]


      A dictionary containing compiled instructions.

      The contents of this dictionary depend on the backend it was compiled for.
      However, we assume that the general format consists of a dictionary in which
      the keys are instrument names corresponding to components added to a
      :class:`~.InstrumentCoordinator`, and the
      values are the instructions for that component.

      These values typically contain a combination of sequence files, waveform
      definitions, and parameters to configure on the instrument.


   .. py:method:: is_valid(object_to_be_validated: Any) -> bool
      :classmethod:


      Check if the contents of the object_to_be_validated are valid.

      Additionally checks if the object_to_be_validated is
      an instance of :class:`~.CompiledSchedule`.



   .. py:property:: hardware_timing_table
      :type: pandas.io.formats.style.Styler


      Return a timing table representing all operations at the Control-hardware layer.

      Note that this timing table is typically different from the `.timing_table` in
      that it contains more hardware specific information such as channels, clock
      cycles and samples and corrections for things such as gain.

      This hardware timing table is intended to provide a more

      This table is constructed based on the timing_table and modified during
      compilation in one of the hardware back ends and optionally added to the
      schedule. Not all back ends support this feature.


   .. py:property:: hardware_waveform_dict
      :type: dict[str, numpy.ndarray]


      Return a waveform dictionary representing all waveforms at the Control-hardware layer.

      Where the waveforms are represented as abstract waveforms in the Operations,
      this dictionary contains the numerical arrays that are uploaded to the hardware.

      This dictionary is constructed during compilation in the hardware back ends and
       optionally added to the schedule. Not all back ends support this feature.


   .. py:method:: clone() -> CompiledSchedule

      Clone this schedule into a separate independent schedule.



   .. py:method:: substitute(substitutions: dict[qblox_scheduler.operations.expressions.Expression, qblox_scheduler.operations.expressions.Expression | int | float | complex]) -> CompiledSchedule

      Substitute matching expressions of operations in this schedule.



.. py:class:: Schedulable(name: str, operation_id: str)

   Bases: :py:obj:`qblox_scheduler.json_utils.JSONSchemaValMixin`, :py:obj:`collections.UserDict`


   A representation of an element on a schedule.

   All elements on a schedule are schedulables. A schedulable contains all
   information regarding the timing of this element as well as the operation
   being executed by this element. This operation is currently represented by
   an operation ID.

   Schedulables can contain an arbitrary number of timing constraints to
   determine the timing. Multiple different constraints are currently resolved
   by delaying the element until after all timing constraints have been met, to
   aid compatibility. To specify an exact timing between two schedulables,
   please ensure to only specify exactly one timing constraint.

   :param name: The name of this schedulable, by which it can be referenced by other
                schedulables. Separate schedulables cannot share the same name.
   :param operation_id: Reference to the operation which is to be executed by this schedulable.


   .. py:attribute:: schema_filename
      :value: 'schedulable.json'



   .. py:method:: clone() -> Schedulable

      Clone this schedulable into a separate independent schedulable.



   .. py:method:: substitute(substitutions: dict[qblox_scheduler.operations.expressions.Expression, qblox_scheduler.operations.expressions.Expression | int | float | complex]) -> Schedulable

      Substitute matching expressions in this schedulable.



   .. py:method:: add_timing_constraint(rel_time: float | qblox_scheduler.operations.expressions.Expression = 0, ref_schedulable: Schedulable | str | None = None, ref_pt: OperationReferencePoint | None = None, ref_pt_new: OperationReferencePoint | None = None) -> None

      Add timing constraint.

      A timing constraint constrains the operation in time by specifying the time
      (:code:`"rel_time"`) between a reference schedulable and the added schedulable.
      The time can be specified with respect to the "start", "center", or "end" of
      the operations.
      The reference schedulable (:code:`"ref_schedulable"`) is specified using its
      name property.
      See also :attr:`~.TimeableScheduleBase.schedulables`.

      :param rel_time: relative time between the reference schedulable and the added schedulable.
                       the time is the time between the "ref_pt" in the reference operation and
                       "ref_pt_new" of the operation that is added.
      :param ref_schedulable: name of the reference schedulable. If set to :code:`None`, will default
                              to the last added operation.
      :param ref_pt: reference point in reference operation must be one of
                     :code:`"start"`, :code:`"center"`, :code:`"end"`, or :code:`None`; in case
                     of :code:`None`,
                     :meth:`~qblox_scheduler.compilation._determine_absolute_timing` assumes
                     :code:`"end"`.
      :param ref_pt_new: reference point in added operation must be one of
                         :code:`"start"`, :code:`"center"`, :code:`"end"`, or :code:`None`; in case
                         of :code:`None`,
                         :meth:`~qblox_scheduler.compilation._determine_absolute_timing` assumes
                         :code:`"start"`.



   .. py:property:: hash
      :type: str


      A hash based on the contents of the Operation.


.. py:class:: TimeableSchedule(name: str = 'schedule', repetitions: int = 1, data: dict | None = None)

   Bases: :py:obj:`TimeableScheduleBase`


   A modifiable schedule.

   Operations :class:`qblox_scheduler.operations.operation.Operation` can be added
   using the :meth:`~.Schedule.add` method, allowing precise
   specification *when* to perform an operation using timing constraints.

   When adding an operation, it is not required to specify how to represent this
   :class:`qblox_scheduler.operations.operation.Operation` on all layers.
   Instead, this information can be added later during
   :ref:`compilation <sec-compilation>`.
   This allows the user to effortlessly mix the gate- and pulse-level descriptions as
   required for many (calibration) experiments.

   :param name: The name of the schedule, by default "schedule"
   :param repetitions: The amount of times the schedule will be repeated, by default 1
   :param data: A dictionary containing a pre-existing schedule, by default None


   .. py:attribute:: schema_filename
      :value: 'schedule.json'



   .. py:property:: _scope_stack
      :type: list[TimeableSchedule]



   .. py:method:: add_resources(resources_list: list) -> None

      Add wrapper for adding multiple resources.



   .. py:method:: add_resource(resource: qblox_scheduler.resources.Resource) -> None

      Add a resource such as a channel or device element to the schedule.



   .. py:method:: add(operation: qblox_scheduler.operations.operation.Operation | TimeableSchedule, rel_time: float | qblox_scheduler.operations.expressions.Expression = 0, ref_op: Schedulable | str | None = None, ref_pt: OperationReferencePoint | None = None, ref_pt_new: OperationReferencePoint | None = None, label: str | None = None) -> Schedulable

      Add an operation or a subschedule to the schedule.

      :param operation: The operation to add to the schedule, or another schedule to add
                        as a subschedule.
      :param rel_time: relative time between the reference operation and the added operation.
                       the time is the time between the "ref_pt" in the reference operation and
                       "ref_pt_new" of the operation that is added.
      :param ref_op: reference schedulable. If set to :code:`None`, will default
                     based on the chosen :code:`SchedulingStrategy`. If ASAP is chosen, the
                     previously added schedulable is the reference schedulable. If ALAP is chose,
                     the reference schedulable is the schedulable added immediately after this
                     schedulable.
      :param ref_pt: reference point in reference operation must be one of
                     :code:`"start"`, :code:`"center"`, :code:`"end"`, or :code:`None`; in case
                     of :code:`None`,
                     :func:`~qblox_scheduler.compilation._determine_absolute_timing` assumes
                     :code:`"end"`.
      :param ref_pt_new: reference point in added operation must be one of
                         :code:`"start"`, :code:`"center"`, :code:`"end"`, or :code:`None`; in case
                         of :code:`None`,
                         :func:`~qblox_scheduler.compilation._determine_absolute_timing` assumes
                         :code:`"start"`.
      :param label: a unique string that can be used as an identifier when adding operations.
                    if set to `None`, a random hash will be generated instead.

      :returns: :
                    Returns the schedulable created in the schedule.




   .. py:method:: _add(operation: qblox_scheduler.operations.operation.Operation | TimeableSchedule, rel_time: float | qblox_scheduler.operations.expressions.Expression = 0, ref_op: Schedulable | str | None = None, ref_pt: OperationReferencePoint | None = None, ref_pt_new: OperationReferencePoint | None = None, label: str | None = None) -> Schedulable


   .. py:method:: _validate_add_arguments(operation: qblox_scheduler.operations.operation.Operation | TimeableSchedule, label: str) -> None


   .. py:method:: declare(dtype: qblox_scheduler.operations.expressions.DType) -> qblox_scheduler.operations.variables.Variable

      Declare a new variable.

      :param dtype: The data type of the variable.



   .. py:method:: define(var: qblox_scheduler.operations.variables.Variable) -> None

      Add a declared variable.

      :param var: The variable.



   .. py:method:: clone() -> TimeableSchedule

      Clone this schedule into a separate independent schedule.



   .. py:method:: substitute(substitutions: dict[qblox_scheduler.operations.expressions.Expression, qblox_scheduler.operations.expressions.Expression | int | float | complex]) -> TimeableSchedule

      Substitute matching expressions in this schedule.



   .. py:method:: loop(domain: dict[qblox_scheduler.operations.variables.Variable, qblox_scheduler.operations.loop_domains.LinearDomain], rel_time: float = 0, ref_op: Schedulable | str | None = None, ref_pt: OperationReferencePoint | None = None, ref_pt_new: OperationReferencePoint | None = None, strategy: qblox_scheduler.operations.control_flow_library.LoopStrategy | None = None) -> collections.abc.Iterator[qblox_scheduler.operations.variables.Variable]
                  loop(domain: qblox_scheduler.operations.loop_domains.LinearDomain, rel_time: float = 0, ref_op: Schedulable | str | None = None, ref_pt: OperationReferencePoint | None = None, ref_pt_new: OperationReferencePoint | None = None, strategy: qblox_scheduler.operations.control_flow_library.LoopStrategy | None = None) -> collections.abc.Iterator[qblox_scheduler.operations.variables.Variable]
                  loop(*domains: qblox_scheduler.operations.loop_domains.LinearDomain, rel_time: float = 0, ref_op: Schedulable | str | None = None, ref_pt: OperationReferencePoint | None = None, ref_pt_new: OperationReferencePoint | None = None, strategy: qblox_scheduler.operations.control_flow_library.LoopStrategy | None = None) -> collections.abc.Iterator[list[qblox_scheduler.operations.variables.Variable]]

      Add a loop operation to the schedule, using a with-statement.

      Every operation added while the context manager is active, will be added to the loop body.

      Example:

      .. code-block::

          sched = TimeableSchedule()
          with sched.loop(linspace(start_amp, start_amp + 1.0, 11, dtype=DType.AMPLITUDE)) as amp:
              sched.add(SquarePulse(amp=amp, duration=100e-9, port="q0:mw", clock="q0.01"))

      :param domain: The object that describes the domain to be looped over.
      :param domains: Optional extra domains that will be looped over in parallel, in a zip-like fashion.
      :param rel_time: relative time between the reference operation and the added operation.
                       the time is the time between the "ref_pt" in the reference operation and
                       "ref_pt_new" of the operation that is added.
      :param ref_op: reference schedulable. If set to :code:`None`, will default
                     to the last added operation.
      :param ref_pt: reference point in reference operation must be one of
                     :code:`"start"`, :code:`"center"`, :code:`"end"`, or :code:`None`; in case
                     of :code:`None`,
                     :func:`~qblox_scheduler.compilation._determine_absolute_timing` assumes
                     :code:`"end"`.
      :param ref_pt_new: reference point in added operation must be one of
                         :code:`"start"`, :code:`"center"`, :code:`"end"`, or :code:`None`; in case
                         of :code:`None`,
                         :func:`~qblox_scheduler.compilation._determine_absolute_timing` assumes
                         :code:`"start"`.
      :param strategy: Strategy to use for implementing this loop, will default to
                       :code:`None` indicating no preference.

      :Yields: *variables* -- The Variable objects that are created for each domain.



   .. py:method:: repeat(n: int) -> collections.abc.Iterator[None]

      Add a loop operation to the schedule for a given amount of iterations,
      using a with-statement.

      Example:

      .. code-block::

          sched = Schedule()
          with sched.repeat(5):
              sched.add(SquarePulse(amp=some_amp, duration=100e-9, port="q0:mw", clock="q0.01"))

      :param n: The amount of times to repeat the loop body.



.. py:function:: heterodyne_spec_sched(pulse_amp: float, pulse_duration: float, frequency: float, acquisition_delay: float, integration_time: float, port: str, clock: str, init_duration: float = 1e-05, repetitions: int = 1, port_out: str | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing heterodyne spectroscopy.

   :param pulse_amp: Amplitude of the spectroscopy pulse in Volt.
   :param pulse_duration: Duration of the spectroscopy pulse in seconds.
   :param frequency: Frequency of the spectroscopy pulse in Hertz.
   :param acquisition_delay: Start of the data acquisition with respect to the start of the spectroscopy
                             pulse in seconds.
   :param integration_time: Integration time of the data acquisition in seconds.
   :param port: Location on the device where the acquisition is performed.
   :param clock: Reference clock used to track the spectroscopy frequency.
   :param init_duration: The relaxation time or dead time.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.
   :param port_out: Output port on the device where the pulse should be applied. If `None`, then use
                    the same as `port`.


.. py:function:: heterodyne_spec_sched_nco(pulse_amp: float, pulse_duration: float, frequencies: numpy.ndarray, acquisition_delay: float, integration_time: float, port: str, clock: str, init_duration: float = 1e-05, repetitions: int = 1, port_out: str | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a batched schedule for performing fast heterodyne spectroscopy
   using the :class:`~qblox_scheduler.operations.pulse_library.SetClockFrequency`
   operation for doing an NCO sweep.

   .. admonition:: Example use of the ``heterodyne_spec_sched_nco`` schedule
       :class: tip

       .. jupyter-execute::

           import numpy as np
           from qcodes.parameters.parameter import ManualParameter

           from qblox_scheduler.gettables import ScheduleGettable
           from qblox_scheduler.device_under_test.quantum_device import QuantumDevice
           from qblox_scheduler.device_under_test.transmon_element import BasicTransmonElement
           from qblox_scheduler.schedules.spectroscopy_schedules import heterodyne_spec_sched_nco

           quantum_device = QuantumDevice(name="quantum_device")
           q0 = BasicTransmonElement("q0")
           quantum_device.add_element(q0)

           ...

           # Manual parameter for batched schedule
           ro_freq = ManualParameter("ro_freq", unit="Hz")
           ro_freq.batched = True
           ro_freqs = np.linspace(start=4.5e9, stop=5.5e9, num=11)
           quantum_device.cfg_sched_repetitions = 5

           # Configure the gettable
           device_element = quantum_device.get_element("q0")
           schedule_kwargs = {
               "pulse_amp": device_element.measure.pulse_amp,
               "pulse_duration": device_element.measure.pulse_duration,
               "frequencies": ro_freqs,
               "acquisition_delay": device_element.measure.acq_delay,
               "integration_time": device_element.measure.integration_time,
               "port": device_element.ports.readout,
               "clock": device_element.name + ".ro",
               "init_duration": device_element.reset.duration,
           }
           spec_gettable = ScheduleGettable(
               quantum_device=quantum_device,
               schedule_function=heterodyne_spec_sched_nco,
               schedule_kwargs=schedule_kwargs,
               real_imag=False,
               batched=True,
           )


   :param pulse_amp: Amplitude of the spectroscopy pulse in Volt.
   :param pulse_duration: Duration of the spectroscopy pulse in seconds.
   :param frequencies: Sample frequencies for the spectroscopy pulse in Hertz.
   :param acquisition_delay: Start of the data acquisition with respect to the start of the spectroscopy
                             pulse in seconds.
   :param integration_time: Integration time of the data acquisition in seconds.
   :param port: Location on the device where the acquisition is performed.
   :param clock: Reference clock used to track the spectroscopy frequency.
   :param init_duration: The relaxation time or dead time.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.
   :param port_out: Output port on the device where the pulse should be applied. If `None`, then use
                    the same as `port`.


.. py:function:: nv_dark_esr_sched(qubit: str, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generates a schedule for a dark ESR experiment on an NV-center.

   The spectroscopy frequency is taken from the device element. Please use the clock
   specified in the `spectroscopy_operation` entry of the device config.

   :param qubit: Name of the `DeviceElement` representing the NV-center.
   :param repetitions: Number of schedule repetitions.

   :returns: :
                 TimeableSchedule with a single frequency



.. py:function:: two_tone_spec_sched(spec_pulse_amp: float, spec_pulse_duration: float, spec_pulse_port: str, spec_pulse_clock: str, spec_pulse_frequency: float, ro_pulse_amp: float, ro_pulse_duration: float, ro_pulse_delay: float, ro_pulse_port: str, ro_pulse_clock: str, ro_pulse_frequency: float, ro_acquisition_delay: float, ro_integration_time: float, init_duration: float = 1e-05, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing two-tone spectroscopy.

   :param spec_pulse_amp: Amplitude of the spectroscopy pulse in Volt.
   :param spec_pulse_duration: Duration of the spectroscopy pulse in seconds.
   :param spec_pulse_port: Location on the device where the spectroscopy pulse should be applied.
   :param spec_pulse_clock: Reference clock used to track the spectroscopy frequency.
   :param spec_pulse_frequency: Frequency of the spectroscopy pulse in Hertz.
   :param ro_pulse_amp: Amplitude of the readout (spectroscopy) pulse in Volt.
   :param ro_pulse_duration: Duration of the readout (spectroscopy) pulse in seconds.
   :param ro_pulse_delay: Time between the end of the spectroscopy pulse and the start of the readout
                          (spectroscopy) pulse.
   :param ro_pulse_port: Location on the device where the readout (spectroscopy) pulse should be applied.
   :param ro_pulse_clock: Reference clock used to track the readout (spectroscopy) frequency.
   :param ro_pulse_frequency: Frequency of the readout (spectroscopy) pulse in Hertz.
   :param ro_acquisition_delay: Start of the data acquisition with respect to the start of the readout pulse in
                                seconds.
   :param ro_integration_time: Integration time of the data acquisition in seconds.
   :param init_duration: The relaxation time or dead time.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.


.. py:function:: two_tone_spec_sched_nco(spec_pulse_amp: float, spec_pulse_duration: float, spec_pulse_port: str, spec_pulse_clock: str, spec_pulse_frequencies: numpy.ndarray, ro_pulse_amp: float, ro_pulse_duration: float, ro_pulse_delay: float, ro_pulse_port: str, ro_pulse_clock: str, ro_pulse_frequency: float, ro_acquisition_delay: float, ro_integration_time: float, init_duration: float, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a batched schedule for performing fast two-tone spectroscopy using
   the :class:`~qblox_scheduler.operations.pulse_library.SetClockFrequency`
   operation for doing an NCO sweep.

   For long-lived qubits, it is advisable to use a small number of repetitions and
   compensate by doing continuous spectroscopy (low amplitude, long duration pulse with
   simultaneous long readout).

   The "dead-time" between two data points needs to be sufficient to properly reset the
   qubit. That means that `init_duration` should be >> T1 (so typically >200us).

   .. admonition:: Example use of the ``two_tone_spec_sched_nco`` schedule
       :class: tip

       .. jupyter-execute::

           import numpy as np
           from qcodes.parameters.parameter import ManualParameter

           from qblox_scheduler.gettables import ScheduleGettable
           from qblox_scheduler.device_under_test.quantum_device import QuantumDevice
           from qblox_scheduler.device_under_test.transmon_element import BasicTransmonElement
           from qblox_scheduler.schedules.spectroscopy_schedules import two_tone_spec_sched_nco

           quantum_device = QuantumDevice(name="quantum_device")
           q0 = BasicTransmonElement("q0")
           quantum_device.add_element(q0)

           ...

           # Manual parameter for batched schedule
           spec_freq = ManualParameter("spec_freq", unit="Hz")
           spec_freq.batched = True
           spec_freqs = np.linspace(start=4.5e9, stop=5.5e9, num=11)
           quantum_device.cfg_sched_repetitions = 5

           # Configure the gettable
           device_element = quantum_device.get_element("q0")
           schedule_kwargs = {
               "spec_pulse_amp": 0.5,
               "spec_pulse_duration": 8e-6,
               "spec_pulse_port": device_element.ports.microwave,
               "spec_pulse_clock": device_element.name + ".01",
               "spec_pulse_frequencies": spec_freqs,
               "ro_pulse_amp": device_element.measure.pulse_amp,
               "ro_pulse_duration": device_element.measure.pulse_duration,
               "ro_pulse_delay": 300e-9,
               "ro_pulse_port": device_element.ports.readout,
               "ro_pulse_clock": device_element.name + ".ro",
               "ro_pulse_frequency": 7.04e9,
               "ro_acquisition_delay": device_element.measure.acq_delay,
               "ro_integration_time": device_element.measure.integration_time,
               "init_duration": 300e-6,
           }
           spec_gettable = ScheduleGettable(
               quantum_device=quantum_device,
               schedule_function=two_tone_spec_sched_nco,
               schedule_kwargs=schedule_kwargs,
               real_imag=False,
               batched=True,
           )


   :param spec_pulse_amp: Amplitude of the spectroscopy pulse in Volt.
   :param spec_pulse_duration: Duration of the spectroscopy pulse in seconds.
   :param spec_pulse_port: Location on the device where the spectroscopy pulse should be applied.
   :param spec_pulse_clock: Reference clock used to track the spectroscopy frequency.
   :param spec_pulse_frequencies: Sample frequencies for the spectroscopy pulse in Hertz.
   :param ro_pulse_amp: Amplitude of the readout (spectroscopy) pulse in Volt.
   :param ro_pulse_duration: Duration of the readout (spectroscopy) pulse in seconds.
   :param ro_pulse_delay: Time between the end of the spectroscopy pulse and the start of the readout
                          (spectroscopy) pulse.
   :param ro_pulse_port: Location on the device where the readout (spectroscopy) pulse should be applied.
   :param ro_pulse_clock: Reference clock used to track the readout (spectroscopy) frequency.
   :param ro_pulse_frequency: Frequency of the readout (spectroscopy) pulse in Hertz.
   :param ro_acquisition_delay: Start of the data acquisition with respect to the start of the readout pulse in
                                seconds.
   :param ro_integration_time: Integration time of the data acquisition in seconds.
   :param init_duration: The relaxation time or dead time.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.


.. py:function:: allxy_sched(qubit: str, element_select_idx: collections.abc.Iterable[int] | int = np.arange(21), repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing an AllXY experiment.

   TimeableSchedule sequence
       .. centered:: Reset -- Rxy[0] -- Rxy[1] -- Measure

   for a specific set of combinations of x90, x180, y90, y180 and idle rotations.

   See section 5.2.3 of :cite:t:`reed_entanglement_2013` for an explanation of
   the AllXY experiment and it's applications in diagnosing errors in single-qubit
   control pulses.

   :param qubit: the name of the device element e.g., :code:`"q0"` to perform the experiment on.
   :param element_select_idx: the index of the particular element of the AllXY experiment to execute.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 An experiment schedule.



.. py:function:: echo_sched(times: numpy.ndarray | float, qubit: str, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing an Echo experiment to measure the qubit
   echo-dephasing time :math:`T_2^{E}`.

   TimeableSchedule sequence
       .. centered:: Reset -- pi/2 -- Idle(tau/2) -- pi -- Idle(tau/2) -- pi/2 -- Measure

   See section III.B.2. of :cite:t:`krantz_quantum_2019` for an explanation of the Bloch-Redfield
   model of decoherence and the echo experiment.

   :param qubit: the name of the device element e.g., "q0" to perform the echo experiment on.
   :param times: an array of wait times. Used as
                 tau/2 wait time between the start of the first pi/2 pulse and pi pulse,
                 tau/2 wait time between the start of the pi pulse and the final pi/2 pulse.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 An experiment schedule.



.. py:function:: rabi_pulse_sched(mw_amplitude: float, mw_beta: float, mw_frequency: float, mw_clock: str, mw_port: str, mw_pulse_duration: float, ro_pulse_amp: float, ro_pulse_duration: float, ro_pulse_delay: float, ro_pulse_port: str, ro_pulse_clock: str, ro_pulse_frequency: float, ro_acquisition_delay: float, ro_integration_time: float, init_duration: float, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing a Rabi experiment using a
   :func:`qblox_scheduler.waveforms.drag` pulse.

   .. note::

       This function allows specifying a Rabi experiment directly using the pulse-level
       abstraction. For most applications we recommend using :func:`rabi_sched`
       instead.

   :param mw_amplitude: amplitude of the gaussian component of a DRAG pulse.
   :param mw_beta: amplitude of the derivative-of-gaussian component of a DRAG pulse.
   :param mw_frequency: frequency of the DRAG pulse.
   :param mw_clock: reference clock used to track the qubit 01 transition.
   :param mw_port: location on the device where the pulse should be applied.
   :param mw_pulse_duration: duration of the DRAG pulse. Corresponds to 4 sigma.
   :param ro_pulse_amp: amplitude of the readout pulse in Volt.
   :param ro_pulse_duration: duration of the readout pulse in seconds.
   :param ro_pulse_delay: time between the end of the spectroscopy pulse and the start of the readout
                          pulse.
   :param ro_pulse_port: location on the device where the readout pulse should be applied.
   :param ro_pulse_clock: reference clock used to track the readout frequency.
   :param ro_pulse_frequency: frequency of the spectroscopy pulse and of the data acquisition in Hertz.
   :param ro_acquisition_delay: start of the data acquisition with respect to the start of the readout pulse
                                in seconds.
   :param ro_integration_time: integration time of the data acquisition in seconds.
   :param init_duration: The relaxation time or dead time.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.


.. py:function:: rabi_sched(pulse_amp: numpy.ndarray | float, pulse_duration: numpy.ndarray | float, frequency: float, qubit: str, port: str = None, clock: str = None, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing a Rabi using a Gaussian pulse.

   TimeableSchedule sequence
       .. centered:: Reset -- DRAG -- Measure

   :param pulse_amp: amplitude of the Rabi pulse in V.
   :param pulse_duration: duration of the Gaussian shaped Rabi pulse. Corresponds to 4 sigma.
   :param frequency: frequency of the qubit 01 transition.
   :param qubit: the device element name on which to perform a Rabi experiment.
   :param port: location on the chip where the Rabi pulse should be applied.
                if set to :code:`None`, will use the naming convention :code:`"<device element name>:mw"` to
                infer the port.
   :param clock: name of the location in frequency space where to apply the Rabi pulse.
                 if set to :code:`None`, will use the naming convention :code:`"<device_element>.01"` to
                 infer the clock.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.


.. py:function:: ramsey_sched(times: numpy.ndarray | float, qubit: str, artificial_detuning: float = 0, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing a Ramsey experiment to measure the
   dephasing time :math:`T_2^{\star}`.

   TimeableSchedule sequence
       .. centered:: Reset -- pi/2 -- Idle(tau) -- pi/2 -- Measure

   See section III.B.2. of :cite:t:`krantz_quantum_2019` for an explanation of the Bloch-Redfield
   model of decoherence and the Ramsey experiment.

   :param times: an array of wait times tau between the start of the first pi/2 pulse and
                 the start of the second pi/2 pulse.
   :param artificial_detuning: frequency in Hz of the software emulated, or ``artificial`` qubit detuning, which is
                               implemented by changing the phase of the second pi/2 (recovery) pulse. The
                               artificial detuning changes the observed frequency of the Ramsey oscillation,
                               which can be useful to distinguish a slow oscillation due to a small physical
                               detuning from the decay of the dephasing noise.
   :param qubit: the name of the device element e.g., :code:`"q0"` to perform the Ramsey experiment on.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 An experiment schedule.



.. py:function:: readout_calibration_sched(qubit: str, prepared_states: list[int], repetitions: int = 1, acq_protocol: Literal['SSBIntegrationComplex', 'ThresholdedAcquisition'] = 'SSBIntegrationComplex') -> qblox_scheduler.schedules.schedule.TimeableSchedule

   A schedule for readout calibration. Prepares a state and immediately performs
   a measurement.

   :param qubit: the name of the device element e.g., :code:`"q0"` to perform the experiment on.
   :param prepared_states: the states to prepare the qubit in before measuring as in integer corresponding
                           to the ground (0), first-excited (1) or second-excited (2) state.
   :param repetitions: The number of shots to acquire, sets the number of times the schedule will
                       be repeated.
   :param acq_protocol: The acquisition protocol used for the readout calibration. By default
                        "SSBIntegrationComplex", but "ThresholdedAcquisition" can be
                        used for verifying thresholded acquisition parameters with this function (see
                        :doc:`/tutorials/Conditional Reset`).

   :returns: :
                 An experiment schedule.

   :raises ValueError: If the prepared state is not either 0, 1, or 2.
   :raises NotImplementedError: If the prepared state is 2.


.. py:function:: t1_sched(times: numpy.ndarray | float, qubit: str, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing a :math:`T_1` experiment to measure the qubit
   relaxation time.

   TimeableSchedule sequence
       .. centered:: Reset -- pi -- Idle(tau) -- Measure

   See section III.B.2. of :cite:t:`krantz_quantum_2019` for an explanation of the Bloch-Redfield
   model of decoherence and the :math:`T_1` experiment.

   :param times: an array of wait times tau between the start of pi-pulse and the measurement.
   :param qubit: the name of the device element e.g., :code:`"q0"` to perform the T1 experiment on.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 An experiment schedule.



.. py:function:: trace_schedule(pulse_amp: float, pulse_duration: float, pulse_delay: float, frequency: float, acquisition_delay: float, integration_time: float, port: str, clock: str, init_duration: float = 0.0002, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule to perform raw trace acquisition.

   :param pulse_amp: The amplitude of the pulse in Volt.
   :param pulse_duration: The duration of the pulse in seconds.
   :param pulse_delay: The pulse delay in seconds.
   :param frequency: The frequency of the pulse and of the data acquisition in Hertz.
   :param acquisition_delay: The start of the data acquisition with respect to the start of the pulse in
                             seconds.
   :param integration_time: The time in seconds to integrate.
   :param port: The location on the device where the
                pulse should be applied.
   :param clock: The reference clock used to track the pulse frequency.
   :param init_duration: The relaxation time or dead time.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 The Raw Trace acquisition TimeableSchedule.



.. py:function:: trace_schedule_circuit_layer(qubit_name: str, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a simple schedule at circuit layer to perform raw trace acquisition.

   :param qubit_name: Name of a device element.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 The Raw Trace acquisition TimeableSchedule.



.. py:function:: two_tone_trace_schedule(qubit_pulse_amp: float, qubit_pulse_duration: float, qubit_pulse_frequency: float, qubit_pulse_port: str, qubit_pulse_clock: str, ro_pulse_amp: float, ro_pulse_duration: float, ro_pulse_delay: float, ro_pulse_port: str, ro_pulse_clock: str, ro_pulse_frequency: float, ro_acquisition_delay: float, ro_integration_time: float, init_duration: float = 0.0002, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing a two-tone raw trace acquisition.

   :param qubit_pulse_amp: The amplitude of the pulse in Volt.
   :param qubit_pulse_duration: The duration of the pulse in seconds.
   :param qubit_pulse_frequency: The pulse frequency in Hertz.
   :param qubit_pulse_port: The location on the device where the
                            qubit pulse should be applied.
   :param qubit_pulse_clock: The reference clock used to track the
                             pulse frequency.
   :param ro_pulse_amp: The amplitude of the readout pulse in Volt.
   :param ro_pulse_duration: The duration of the readout pulse in seconds.
   :param ro_pulse_delay: The time between the end of the pulse and the start
                          of the readout pulse.
   :param ro_pulse_port: The location on the device where the
                         readout pulse should be applied.
   :param ro_pulse_clock: The reference clock used to track the
                          readout pulse frequency.
   :param ro_pulse_frequency: The readout pulse frequency in Hertz.
   :param ro_acquisition_delay: The start of the data acquisition with respect to
                                the start of the pulse in seconds.
   :param ro_integration_time: The integration time of the data acquisition in seconds.
   :param init_duration: The relaxation time or dead time.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 The Two-tone Trace acquisition TimeableSchedule.



