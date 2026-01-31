schedule
========

.. py:module:: qblox_scheduler.schedules.schedule 

.. autoapi-nested-parse::

   Module containing the core concepts of the scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules.schedule.TimeableScheduleBase
   qblox_scheduler.schedules.schedule.TimeableSchedule
   qblox_scheduler.schedules.schedule.Schedulable
   qblox_scheduler.schedules.schedule.TimingConstraint
   qblox_scheduler.schedules.schedule.AcquisitionChannelData
   qblox_scheduler.schedules.schedule.CompiledSchedule




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules.schedule.OperationReferencePoint
   qblox_scheduler.schedules.schedule.AcquisitionChannelsData


.. py:data:: OperationReferencePoint

   Type hint for operation reference points.

.. py:class:: TimeableScheduleBase(dict=None, /, **kwargs)

   Bases: :py:obj:`qblox_scheduler.json_utils.JSONSchemaValMixin`, :py:obj:`qblox_scheduler.json_utils.JSONSerializable`, :py:obj:`collections.UserDict`, :py:obj:`abc.ABC`


   Interface to be used for :class:`~.TimeableSchedule`.

   The :class:`~.TimeableScheduleBase` is a data structure that is at
   the core of the qblox-scheduler and describes when what operations are applied
   where.

   The :class:`~.TimeableScheduleBase` is a collection of
   :class:`qblox_scheduler.operations.operation.Operation` objects and timing
   constraints that define relations between the operations.

   The schedule data structure is based on a dictionary.
   This dictionary contains:

   - operation_dict - a hash table containing the unique
       :class:`qblox_scheduler.operations.operation.Operation` s added to the
       schedule.
   - schedulables - an ordered dictionary of all timing constraints added
       between operations; when multiple schedulables have the same
       absolute time, the order defined in the dictionary decides precedence.

   The :class:`~.TimeableSchedule` provides an API to create schedules.
   The :class:`~.CompiledSchedule` represents a schedule after
   it has been compiled for execution on a backend.


   The :class:`~.TimeableSchedule` contains information on the
   :attr:`~.TimeableScheduleBase.operations` and
   :attr:`~.TimeableScheduleBase.schedulables`.
   The :attr:`~.TimeableScheduleBase.operations` is a dictionary of all
   unique operations used in the schedule and contain the information on *what*
   operation to apply *where*.
   The :attr:`~.TimeableScheduleBase.schedulables` is a dictionary of
   Schedulables describing timing constraints between operations, i.e. when to apply
   an operation.


   **JSON schema of a valid Schedule**

   .. jsonschema:: ../../../../../../src/qblox_scheduler/schemas/schedule.json



   .. py:property:: name
      :type: str


      Returns the name of the schedule.


   .. py:property:: repetitions
      :type: int


      Returns the amount of times this TimeableSchedule will be repeated.

      :returns: :
                    The repetitions count.


   .. py:property:: operations
      :type: dict[str, qblox_scheduler.operations.operation.Operation | TimeableSchedule]


      A dictionary of all unique operations used in the schedule.

      This specifies information on *what* operation to apply *where*.

      The keys correspond to the :attr:`~.Operation.hash` and values are instances
      of :class:`qblox_scheduler.operations.operation.Operation`.


   .. py:property:: schedulables
      :type: dict[str, Schedulable]


      Ordered dictionary of schedulables describing timing and order of operations.

      A schedulable uses timing constraints to constrain the operation in time by
      specifying the time (:code:`"rel_time"`) between a reference operation and the
      added operation. The time can be specified with respect to a reference point
      (:code:`"ref_pt"') on the reference operation (:code:`"ref_op"`) and a reference
      point on the next added operation (:code:`"ref_pt_new"').
      A reference point can be either the "start", "center", or "end" of an
      operation. The reference operation (:code:`"ref_op"`) is specified using its
      label property.

      Each item in the list represents a timing constraint and is a dictionary with
      the following keys:

      .. code-block::

          ['label', 'rel_time', 'ref_op', 'ref_pt_new', 'ref_pt', 'operation_id']

      The label is used as a unique identifier that can be used as a reference for
      other operations, the operation_id refers to the hash of an
      operation in :attr:`~.TimeableScheduleBase.operations`.

      .. note::

          timing constraints are not intended to be modified directly.
          Instead use the :meth:`~.TimeableSchedule.add`


   .. py:property:: resources
      :type: dict[str, qblox_scheduler.resources.Resource]


      A dictionary containing resources.

      Keys are names (str), values are instances of
      :class:`~qblox_scheduler.resources.Resource`.


   .. py:property:: hash
      :type: str


      A hash based on the contents of the TimeableSchedule.


   .. py:method:: clone() -> TimeableScheduleBase
      :abstractmethod:


      Clone this schedule into a separate independent schedule.



   .. py:method:: substitute(substitutions: dict[qblox_scheduler.operations.expressions.Expression, qblox_scheduler.operations.expressions.Expression | int | float | complex]) -> TimeableScheduleBase
      :abstractmethod:


      Substitute matching expressions of operations in this schedule.



   .. py:method:: get_used_port_clocks() -> set[tuple[str, str]]

      Extracts which port-clock combinations are used in this schedule.

      :returns: :
                    All (port, clock) combinations that operations in this schedule uses




   .. py:method:: plot_circuit_diagram(figsize: tuple[int, int] | None = None, ax: matplotlib.axes.Axes | None = None, plot_backend: Literal['mpl'] = 'mpl') -> tuple[matplotlib.figure.Figure | None, matplotlib.axes.Axes | list[matplotlib.axes.Axes]]

      Create a circuit diagram visualization of the schedule using the specified plotting backend.

      The circuit diagram visualization depicts the schedule at the quantum circuit
      layer. Because qblox-scheduler uses a hybrid gate-pulse paradigm, operations
      for which no information is specified at the gate level are visualized using an
      icon (e.g., a stylized wavy pulse) depending on the information specified at
      the quantum device layer.

      Alias of :func:`qblox_scheduler.schedules._visualization.circuit_diagram.circuit_diagram_matplotlib`.

      :param schedule: the schedule to render.
      :param figsize: matplotlib figsize.
      :param ax: Axis handle to use for plotting.
      :param plot_backend: Plotting backend to use, currently only 'mpl' is supported

      :returns: fig
                    matplotlib figure object.
                ax
                    matplotlib axis object.



      Each gate, pulse, measurement, and any other operation are plotted in the order
      of execution, but no timing information is provided.

      .. admonition:: Example
          :class: tip

          .. jupyter-execute::

              from qblox_scheduler import TimeableSchedule
              from qblox_scheduler.operations.gate_library import Reset, X90, CZ, Rxy, Measure

              sched = TimeableSchedule(f"Bell experiment on q0-q1")

              sched.add(Reset("q0", "q1"))
              sched.add(X90("q0"))
              sched.add(X90("q1"), ref_pt="start", rel_time=0)
              sched.add(CZ(qC="q0", qT="q1"))
              sched.add(Rxy(theta=45, phi=0, qubit="q0") )
              sched.add(Measure("q0"))
              sched.add(Measure("q1"), ref_pt="start")

              sched.plot_circuit_diagram();

      .. note::

          Gates that are started simultaneously on the same qubit will overlap.

          .. jupyter-execute::

              from qblox_scheduler import TimeableSchedule
              from qblox_scheduler.operations.gate_library import X90, Measure

              sched = TimeableSchedule(f"overlapping gates")

              sched.add(X90("q0"))
              sched.add(Measure("q0"), ref_pt="start", rel_time=0)
              sched.plot_circuit_diagram();

      .. note::

          If the pulse's port address was not found then the pulse will be plotted on the
          'other' timeline.




   .. py:method:: plot_pulse_diagram(port_list: list[str] | None = None, sampling_rate: float = 1000000000.0, modulation: Literal['off', 'if', 'clock'] = 'off', modulation_if: float = 0.0, plot_backend: Literal['mpl', 'plotly'] = 'mpl', x_range: tuple[float, float] = (-np.inf, np.inf), combine_waveforms_on_same_port: bool = True, **backend_kwargs) -> tuple[matplotlib.figure.Figure, matplotlib.axes.Axes] | plotly.graph_objects.Figure

      Create a visualization of all the pulses in a schedule using the specified plotting backend.

      The pulse diagram visualizes the schedule at the quantum device layer.
      For this visualization to work, all operations need to have the information
      present (e.g., pulse info) to represent these on the quantum-circuit level and
      requires the absolute timing to have been determined.
      This information is typically added when the quantum-device level compilation is
      performed.

      Alias of
      :func:`qblox_scheduler.schedules._visualization.pulse_diagram.pulse_diagram_matplotlib`
      and
      :func:`qblox_scheduler.schedules._visualization.pulse_diagram.pulse_diagram_plotly`.

      :param port_list: A list of ports to show. If ``None`` (default) the first 8 ports encountered in the sequence are used.
      :param modulation: Determines if modulation is included in the visualization.
      :param modulation_if: Modulation frequency used when modulation is set to "if".
      :param sampling_rate: The time resolution used to sample the schedule in Hz.
      :param plot_backend: Plotting library to use, can either be 'mpl' or 'plotly'.
      :param x_range: The range of the x-axis that is plotted, given as a tuple (left limit, right
                      limit). This can be used to reduce memory usage when plotting a small section of
                      a long pulse sequence. By default (-np.inf, np.inf).
      :param combine_waveforms_on_same_port: By default True. If True, combines all waveforms on the same port into one
                                             single waveform. The resulting waveform is the sum of all waveforms on that
                                             port (small inaccuracies may occur due to floating point approximation). If
                                             False, the waveforms are shown individually.
      :param backend_kwargs: Keyword arguments to be passed on to the plotting backend. The arguments
                             that can be used for either backend can be found in the documentation of
                             :func:`qblox_scheduler.schedules._visualization.pulse_diagram.pulse_diagram_matplotlib`
                             and
                             :func:`qblox_scheduler.schedules._visualization.pulse_diagram.pulse_diagram_plotly`.

      :returns: Union[tuple[Figure, Axes], :class:`!plotly.graph_objects.Figure`]
                    the plot


      .. admonition:: Example
          :class: tip

          A simple plot with matplotlib can be created as follows:

          .. jupyter-execute::

              from qblox_scheduler.backends.graph_compilation import SerialCompiler
              from qblox_scheduler.device_under_test.quantum_device import QuantumDevice
              from qblox_scheduler.operations.pulse_library import (
                  DRAGPulse, SquarePulse, RampPulse, VoltageOffset,
              )
              from qblox_scheduler.resources import ClockResource

              schedule = TimeableSchedule("Multiple waveforms")
              schedule.add(DRAGPulse(amplitude=0.2, beta=2e-9, phase=0, duration=4e-6, port="P", clock="C"))
              schedule.add(RampPulse(amp=0.2, offset=0.0, duration=6e-6, port="P"))
              schedule.add(SquarePulse(amp=0.1, duration=4e-6, port="Q"), ref_pt='start')
              schedule.add_resource(ClockResource(name="C", freq=4e9))

              quantum_device = QuantumDevice("quantum_device")
              device_compiler = SerialCompiler("Device compiler", quantum_device)
              compiled_schedule = device_compiler.compile(schedule)

              _ = compiled_schedule.plot_pulse_diagram(sampling_rate=20e6)

          The backend can be changed to the plotly backend by specifying the
          ``plot_backend=plotly`` argument. With the plotly backend, pulse
          diagrams include a separate plot for each port/clock
          combination:

          .. jupyter-execute::

              _ = compiled_schedule.plot_pulse_diagram(sampling_rate=20e6, plot_backend='plotly')

          The same can be achieved in the default ``plot_backend`` (``matplotlib``)
          by passing the keyword argument ``multiple_subplots=True``:

          .. jupyter-execute::

              _ = compiled_schedule.plot_pulse_diagram(sampling_rate=20e6, multiple_subplots=True)

          By default, waveforms overlapping in time on the same port are shown separately:

          .. jupyter-execute::

              schedule = TimeableSchedule("Overlapping waveforms")
              schedule.add(VoltageOffset(offset_path_I=0.25, offset_path_Q=0.0, port="Q"))
              schedule.add(SquarePulse(amp=0.1, duration=4e-6, port="Q"), rel_time=2e-6)
              schedule.add(VoltageOffset(offset_path_I=0.0, offset_path_Q=0.0, port="Q"), ref_pt="start", rel_time=2e-6)

              compiled_schedule = device_compiler.compile(schedule)

              _ = compiled_schedule.plot_pulse_diagram(sampling_rate=20e6)

          This behaviour can be changed with the parameter ``combine_waveforms_on_same_port``:

          .. jupyter-execute::

              _ = compiled_schedule.plot_pulse_diagram(sampling_rate=20e6, combine_waveforms_on_same_port=True)




   .. py:method:: _generate_timing_table_list(operation: qblox_scheduler.operations.operation.Operation | TimeableScheduleBase, time_offset: float, timing_table_list: list, operation_id: str | None) -> None
      :classmethod:



   .. py:property:: timing_table
      :type: pandas.io.formats.style.Styler


      A styled pandas dataframe containing the absolute timing of pulses and acquisitions in a schedule.

      This table is constructed based on the ``abs_time`` key in the
      :attr:`~qblox_scheduler.schedules.schedule.TimeableScheduleBase.schedulables`.
      This requires the timing to have been determined.

      The table consists of the following columns:

      - `operation`: a ``repr`` of :class:`~qblox_scheduler.operations.operation.Operation` corresponding to the pulse/acquisition.
      - `waveform_op_id`: an id corresponding to each pulse/acquisition inside an :class:`~qblox_scheduler.operations.operation.Operation`.
      - `port`: the port the pulse/acquisition is to be played/acquired on.
      - `clock`: the clock used to (de)modulate the pulse/acquisition.
      - `abs_time`: the absolute time the pulse/acquisition is scheduled to start.
      - `duration`: the duration of the pulse/acquisition that is scheduled.
      - `is_acquisition`: whether the pulse/acquisition is an acquisition or not (type ``numpy.bool_``).
      - `wf_idx`: the waveform index of the pulse/acquisition belonging to the Operation.
      - `operation_hash`: the unique hash corresponding to the :class:`~.Schedulable` that the pulse/acquisition belongs to.

      .. admonition:: Example

          .. jupyter-execute::
              :hide-code:

              from qblox_scheduler.backends import SerialCompiler
              from qblox_scheduler.device_under_test.quantum_device import QuantumDevice
              from qblox_scheduler.device_under_test.transmon_element import BasicTransmonElement
              from qblox_scheduler.operations.gate_library import (
                  Measure,
                  Reset,
                  X,
                  Y,
              )
              from qblox_scheduler.schedules.schedule import TimeableSchedule
              from qblox_scheduler.schemas.examples import utils

              compiler = SerialCompiler("compiler")
              q0 = BasicTransmonElement("q0")
              q4 = BasicTransmonElement("q4")

              for device_element in [q0, q4]:
                  device_element.rxy.amp180 = 0.115
                  device_element.rxy.beta = 2.5e-10
                  device_element.clock_freqs.f01 = 7.3e9
                  device_element.clock_freqs.f12 = 7.0e9
                  device_element.clock_freqs.readout = 8.0e9
                  device_element.measure.acq_delay = 100e-9

              quantum_device = QuantumDevice(name="quantum_device0")
              quantum_device.add_element(q0)
              quantum_device.add_element(q4)

              device_config = quantum_device.generate_device_config()
              hardware_config = utils.load_json_example_scheme(
                  "qblox_hardware_config_transmon.json"
              )
              hardware_config["hardware_options"].pop("distortion_corrections")
              quantum_device.hardware_config = hardware_config

              compiler = SerialCompiler("compiler")
              compiler.quantum_device = quantum_device

          .. jupyter-execute::

              schedule = TimeableSchedule("demo timing table")
              schedule.add(Reset("q0", "q4"))
              schedule.add(X("q0"))
              schedule.add(Y("q4"))
              schedule.add(Measure("q0", acq_channel=0))
              schedule.add(Measure("q4", acq_channel=1))

              compiled_schedule = compiler.compile(schedule)
              compiled_schedule.timing_table

      :param schedule: a schedule for which the absolute timing has been determined.

      :returns: :
                    styled_timing_table, a pandas Styler containing a dataframe with
                    an overview of the timing of the pulses and acquisitions present in the
                    schedule. The dataframe can be accessed through the .data attribute of
                    the Styler.

      :raises ValueError: When the absolute timing has not been determined during compilation.


   .. py:method:: get_schedule_duration() -> float

      Return the duration of the schedule.

      :returns: schedule_duration : float
                    Duration of current schedule




   .. py:property:: duration
      :type: float | None


      Determine the cached duration of the schedule.

      Will return None if get_schedule_duration() has not been called before.


   .. py:method:: is_valid(schedule: TimeableScheduleBase) -> bool
      :classmethod:


      Check if schedule adheres to JSON schema.



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


.. py:class:: TimingConstraint

   Datastructure to store the information on a Timing Constraint.


   .. py:attribute:: ref_schedulable
      :type:  str

      The schedulable against which `ref_pt` and `rel_time` are defined.


   .. py:attribute:: ref_pt
      :type:  Literal['start', 'center', 'end']

      The point on `ref_schedulable` against which `rel_time` is defined.


   .. py:attribute:: ref_pt_new
      :type:  Literal['start', 'center', 'end'] | None

      The point on the to be added schedulable against which `rel_time` is defined.


   .. py:attribute:: rel_time
      :type:  float

      The time between `ref_pt` and `ref_pt_new`.


   .. py:property:: data
      :type: dict


      Representation of this TimingConstraint as a dictionary.


   .. py:method:: copy() -> TimingConstraint

      Copy this TimingConstraint to a fresh new instance.



.. py:class:: AcquisitionChannelData

   Datastructure to store metadata for the given acquisition channel.


   .. py:attribute:: acq_index_dim_name
      :type:  str

      Acquisition index dimension name.


   .. py:attribute:: protocol
      :type:  str

      Acquisition protocol.


   .. py:attribute:: bin_mode
      :type:  qblox_scheduler.enums.BinMode

      Bin mode.


   .. py:attribute:: coords
      :type:  dict | list[dict]

      Coords for each acquisition.

      For binned types this is a list of coords for each acquisition index,
      and for trace and trigger count types, this is only one value.


.. py:data:: AcquisitionChannelsData

   Dictionary mapping each acq_channel to their corresponding
   hardware independent acquisition channel data.

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



