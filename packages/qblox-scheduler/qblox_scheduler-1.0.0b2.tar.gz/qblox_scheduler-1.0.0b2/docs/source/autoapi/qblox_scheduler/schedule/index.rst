schedule
========

.. py:module:: qblox_scheduler.schedule 

.. autoapi-nested-parse::

   High-level schedule API.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedule.Schedule




.. py:class:: Schedule(name: str, repetitions: int = 1)

   High-level hybrid schedule.


   .. py:attribute:: _experiments


   .. py:attribute:: _resources
      :value: []



   .. py:attribute:: _schedule_count
      :value: None



   .. py:attribute:: _repetitions
      :value: 1



   .. py:attribute:: _uses_timeable_repetitions
      :value: False



   .. py:attribute:: _duration
      :value: None



   .. py:method:: clone() -> Schedule

      Clone this schedule into a separate independent schedule.



   .. py:method:: substitute(substitutions: dict[qblox_scheduler.operations.expressions.Expression, qblox_scheduler.operations.expressions.Expression | int | float | complex]) -> Schedule

      Substitute matching expressions of operations in this schedule.



   .. py:property:: repetitions
      :type: int


      Returns the amount of times this schedule should be repeated.


   .. py:property:: _experiment
      :type: qblox_scheduler.experiments.experiment.Experiment


      Returns the current experiment.


   .. py:property:: name
      :type: str


      Returns the name of the schedule.


   .. py:property:: _timeable_schedules
      :type: list[qblox_scheduler.schedules.schedule.TimeableSchedule]


      Returns a list of timeable schedules in this schedule.


   .. py:property:: _last_timeable_schedule
      :type: qblox_scheduler.schedules.schedule.TimeableSchedule | None


      Returns the last timeable schedule in this schedule.


   .. py:property:: _last_compiled_timeable_schedule
      :type: qblox_scheduler.schedules.schedule.CompiledSchedule | None


      Returns the last compiled timeable schedule in this schedule.


   .. py:property:: _timeable_schedule
      :type: qblox_scheduler.schedules.schedule.TimeableScheduleBase | None


      Returns the single timeable schedule in this schedule, or None.


   .. py:method:: get_schedule_duration() -> float

      Return total duration of all timeable schedules.

      :returns: schedule_duration : float
                    Duration of current schedule




   .. py:property:: duration
      :type: float | None


      Determine the cached duration of the schedule.

      Will return None if get_schedule_duration() has not been called before.


   .. py:property:: data
      :type: dict


      The dictionary data of a single contained timeable schedule.


   .. py:property:: operations
      :type: dict[str, qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule]


      A dictionary of all unique operations used in the schedule.

      This specifies information on *what* operation to apply *where*.

      The keys correspond to the :attr:`~.Operation.hash` and values are instances
      of :class:`qblox_scheduler.operations.operation.Operation`.


   .. py:property:: schedulables
      :type: dict[str, qblox_scheduler.schedules.schedule.Schedulable]


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
          Instead use the :meth:`~.Schedule.add`


   .. py:method:: plot_circuit_diagram(figsize: tuple[int, int] | None = None, ax: matplotlib.axes.Axes | None = None, plot_backend: Literal['mpl'] = 'mpl', timeable_schedule_index: int | None = None) -> tuple[matplotlib.figure.Figure | None, matplotlib.axes.Axes | list[matplotlib.axes.Axes]]

      Create a circuit diagram visualization of the schedule using the specified plotting backend.

      The circuit diagram visualization depicts the schedule at the quantum circuit
      layer. Because qblox-scheduler uses a hybrid gate-pulse paradigm, operations
      for which no information is specified at the gate level are visualized using an
      icon (e.g., a stylized wavy pulse) depending on the information specified at
      the quantum device layer.

      Alias of :func:`qblox_scheduler.schedules._visualization.circuit_diagram.circuit_diagram_matplotlib`.

      :param figsize: matplotlib figsize.
      :param ax: Axis handle to use for plotting.
      :param plot_backend: Plotting backend to use, currently only 'mpl' is supported
      :param timeable_schedule_index: Index of timeable schedule in schedule to plot. If None (the default),
                                      will only plot if the schedule contains a single timeable schedule.

      :returns: fig
                    matplotlib figure object.
                ax
                    matplotlib axis object.



      Each gate, pulse, measurement, and any other operation are plotted in the order
      of execution, but no timing information is provided.

      .. admonition:: Example
          :class: tip

          .. jupyter-execute::

              from qblox_scheduler import Schedule
              from qblox_scheduler.operations.gate_library import Reset, X90, CZ, Rxy, Measure

              sched = Schedule(f"Bell experiment on q0-q1")

              sched.add(Reset("q0", "q1"))
              sched.add(X90("q0"))
              sched.add(X90("q1"), ref_pt="start", rel_time=0)
              sched.add(CZ(qC="q0", qT="q1"))
              sched.add(Rxy(theta=45, phi=0, qubit="q0") )
              sched.add(Measure("q0", acq_index=0))
              sched.add(Measure("q1", acq_index=0), ref_pt="start")

              sched.plot_circuit_diagram()

      .. note::

          Gates that are started simultaneously on the same qubit will overlap.

          .. jupyter-execute::

              from qblox_scheduler import Schedule
              from qblox_scheduler.operations.gate_library import X90, Measure

              sched = Schedule(f"overlapping gates")

              sched.add(X90("q0"))
              sched.add(Measure("q0"), ref_pt="start", rel_time=0)
              sched.plot_circuit_diagram();

      .. note::

          If the pulse's port address was not found then the pulse will be plotted on the
          'other' timeline.




   .. py:method:: plot_pulse_diagram(port_list: list[str] | None = None, sampling_rate: float = 1000000000.0, modulation: Literal['off', 'if', 'clock'] = 'off', modulation_if: float = 0.0, plot_backend: Literal['mpl', 'plotly'] = 'mpl', x_range: tuple[float, float] = (-np.inf, np.inf), combine_waveforms_on_same_port: bool = True, timeable_schedule_index: int | None = None, **backend_kwargs) -> tuple[matplotlib.figure.Figure, matplotlib.axes.Axes] | plotly.graph_objects.Figure

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
      :param timeable_schedule_index: Index of timeable schedule in schedule to plot. If None (the default),
                                      will only plot if the schedule contains a single timeable schedule.
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

              schedule = Schedule("Multiple waveforms")
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

              schedule = Schedule("Overlapping waveforms")
              schedule.add(VoltageOffset(offset_path_I=0.25, offset_path_Q=0.0, port="Q"))
              schedule.add(SquarePulse(amp=0.1, duration=4e-6, port="Q"), rel_time=2e-6)
              schedule.add(VoltageOffset(offset_path_I=0.0, offset_path_Q=0.0, port="Q"), ref_pt="start", rel_time=2e-6)

              compiled_schedule = device_compiler.compile(schedule)

              _ = compiled_schedule.plot_pulse_diagram(sampling_rate=20e6)

          This behaviour can be changed with the parameter ``combine_waveforms_on_same_port``:

          .. jupyter-execute::

              _ = compiled_schedule.plot_pulse_diagram(sampling_rate=20e6, combine_waveforms_on_same_port=True)




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
              from qblox_scheduler import Schedule
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

              schedule = Schedule("demo timing table")
              schedule.add(Reset("q0", "q4"))
              schedule.add(X("q0"))
              schedule.add(Y("q4"))
              schedule.add(Measure("q0", acq_channel=0))
              schedule.add(Measure("q4", acq_channel=1))

              compiled_schedule = compiler.compile(schedule)
              compiled_schedule.timing_table

      :returns: :
                    styled_timing_table, a pandas Styler containing a dataframe with
                    an overview of the timing of the pulses and acquisitions present in the
                    schedule. The dataframe can be accessed through the .data attribute of
                    the Styler.

      :raises ValueError: When the absolute timing has not been determined during compilation.


   .. py:method:: _add_timeable_schedule(timeable_schedule: qblox_scheduler.schedules.schedule.TimeableSchedule) -> None


   .. py:method:: _get_current_timeable_schedule() -> qblox_scheduler.schedules.schedule.TimeableSchedule | None


   .. py:method:: _get_timeable_schedule() -> qblox_scheduler.schedules.schedule.TimeableSchedule


   .. py:method:: get_used_port_clocks() -> set[tuple[str, str]]

      Extracts which port-clock combinations are used in this schedule.

      :returns: :
                    All (port, clock) combinations that operations in this schedule uses




   .. py:method:: add_resources(resources_list: list) -> None

      Add wrapper for adding multiple resources.



   .. py:method:: add_resource(resource: qblox_scheduler.resources.Resource) -> None

      Add a resource such as a channel or device element to the schedule.



   .. py:method:: declare(dtype: qblox_scheduler.operations.expressions.DType) -> qblox_scheduler.operations.variables.Variable

      Declare a new variable.

      :param dtype: The data type of the variable.



   .. py:method:: add(operation: Schedule | qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.experiments.experiment.Step, rel_time: float | qblox_scheduler.operations.expressions.Expression = 0, ref_op: qblox_scheduler.schedules.schedule.Schedulable | str | None = None, ref_pt: qblox_scheduler.schedules.schedule.OperationReferencePoint | None = None, ref_pt_new: qblox_scheduler.schedules.schedule.OperationReferencePoint | None = None, label: str | None = None) -> qblox_scheduler.schedules.schedule.Schedulable | None

      Add step, operation or timeable schedule to this schedule.



   .. py:method:: _add_schedule(schedule: Schedule, rel_time: float | qblox_scheduler.operations.expressions.Expression = 0, ref_op: qblox_scheduler.schedules.schedule.Schedulable | str | None = None, ref_pt: qblox_scheduler.schedules.schedule.OperationReferencePoint | None = None, ref_pt_new: qblox_scheduler.schedules.schedule.OperationReferencePoint | None = None, label: str | None = None) -> qblox_scheduler.schedules.schedule.Schedulable | None


   .. py:method:: loop(domain: qblox_scheduler.operations.loop_domains.LinearDomain, rel_time: float = 0, ref_op: qblox_scheduler.schedules.schedule.Schedulable | str | None = None, ref_pt: qblox_scheduler.schedules.schedule.OperationReferencePoint | None = None, ref_pt_new: qblox_scheduler.schedules.schedule.OperationReferencePoint | None = None, strategy: qblox_scheduler.operations.control_flow_library.LoopStrategy | None = None) -> collections.abc.Iterator[qblox_scheduler.operations.variables.Variable]
                  loop(*domains: qblox_scheduler.operations.loop_domains.LinearDomain, rel_time: float = 0, ref_op: qblox_scheduler.schedules.schedule.Schedulable | str | None = None, ref_pt: qblox_scheduler.schedules.schedule.OperationReferencePoint | None = None, ref_pt_new: qblox_scheduler.schedules.schedule.OperationReferencePoint | None = None, strategy: qblox_scheduler.operations.control_flow_library.LoopStrategy | None = None) -> collections.abc.Iterator[list[qblox_scheduler.operations.variables.Variable]]

      Add a loop operation to the schedule, using a with-statement.

      Every operation added while the context manager is active, will be added to the loop body.

      Example:

      .. code-block::

          sched = Schedule()
          with sched.loop(linspace(start_amp, start_amp + 1.0, 11, dtype=DType.AMP)) as amp:
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



