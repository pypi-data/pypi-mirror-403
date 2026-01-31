# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2025, Qblox B.V.
"""High-level schedule API."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Literal, overload

import numpy as np

from qblox_scheduler.experiments.experiment import Experiment, Step
from qblox_scheduler.experiments.loops import Loop
from qblox_scheduler.experiments.schedules import ExecuteSchedule
from qblox_scheduler.operations.expressions import DType
from qblox_scheduler.operations.loop_domains import linspace
from qblox_scheduler.operations.operation import Operation
from qblox_scheduler.schedules.schedule import CompiledSchedule, Schedulable, TimeableSchedule

if TYPE_CHECKING:
    from collections.abc import Iterator

    import pandas as pd
    import plotly.graph_objects as go
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from qblox_scheduler.operations.control_flow_library import LoopStrategy
    from qblox_scheduler.operations.expressions import Expression
    from qblox_scheduler.operations.loop_domains import LinearDomain
    from qblox_scheduler.operations.variables import Variable
    from qblox_scheduler.resources import Resource
    from qblox_scheduler.schedules.schedule import OperationReferencePoint, TimeableScheduleBase


class Schedule:
    """High-level hybrid schedule."""

    def __init__(self, name: str, repetitions: int = 1) -> None:
        self._experiments = [Experiment(name=name)]
        self._resources = []
        self._schedule_count = None
        self._repetitions = repetitions
        self._uses_timeable_repetitions = False
        self._duration = None

    def clone(self) -> Schedule:
        """Clone this schedule into a separate independent schedule."""
        new_schedule = self.__class__(self._experiment.name)
        new_schedule._experiments = [e.clone() for e in self._experiments]
        new_schedule._schedule_count = self._schedule_count
        return new_schedule

    def substitute(
        self, substitutions: dict[Expression, Expression | int | float | complex]
    ) -> Schedule:
        """Substitute matching expressions of operations in this schedule."""
        changed = False
        new_experiments = []
        for experiment in self._experiments:
            new_experiment = experiment.substitute(substitutions)
            new_experiments.append(new_experiment)
            if new_experiment is not experiment:
                changed = True
        if changed:
            new_schedule = self.clone()
            new_schedule._experiments = new_experiments
            return new_schedule
        else:
            return self

    @property
    def repetitions(self) -> int:
        """Returns the amount of times this schedule should be repeated."""
        return self._repetitions

    @repetitions.setter
    def repetitions(self, value: int) -> None:
        if value <= 0:
            raise ValueError(
                f"Attempting to set repetitions for the schedule. "
                f"Must be a positive number. Got {value}."
            )

        repetitions = int(value)
        if self._uses_timeable_repetitions:
            timeable_schedule = self._timeable_schedule
            assert timeable_schedule is not None
            timeable_schedule.repetitions = repetitions
        self._repetitions = repetitions

    @property
    def _experiment(self) -> Experiment:
        """Returns the current experiment."""
        return self._experiments[-1]

    @property
    def name(self) -> str:
        """Returns the name of the schedule."""
        return self._experiment.name

    @property
    def _timeable_schedules(self) -> list[TimeableSchedule]:
        """Returns a list of timeable schedules in this schedule."""
        schedules = []
        for experiment in self._experiments:
            for step in experiment.steps:
                if isinstance(step, ExecuteSchedule) and isinstance(
                    step.schedule, TimeableSchedule
                ):
                    schedules.append(step.schedule)  # noqa: PERF401
        return schedules

    @property
    def _last_timeable_schedule(self) -> TimeableSchedule | None:
        """Returns the last timeable schedule in this schedule."""
        for experiment in reversed(self._experiments):
            for step in reversed(experiment.steps):
                if isinstance(step, ExecuteSchedule) and isinstance(
                    step.schedule, TimeableSchedule
                ):
                    return step.schedule
        return None

    @property
    def _last_compiled_timeable_schedule(self) -> CompiledSchedule | None:
        """Returns the last compiled timeable schedule in this schedule."""
        for experiment in reversed(self._experiments):
            for step in reversed(experiment.steps):
                if isinstance(step, ExecuteSchedule) and isinstance(
                    step.compiled_schedule, CompiledSchedule
                ):
                    return step.compiled_schedule
        return None

    @property
    def _timeable_schedule(self) -> TimeableScheduleBase | None:
        """Returns the single timeable schedule in this schedule, or None."""
        steps = []
        for experiment in self._experiments:
            steps.extend(experiment.steps)
        if len(steps) == 1 and isinstance(steps[0], ExecuteSchedule):
            return steps[0].schedule
        return None

    def get_schedule_duration(self) -> float:
        """
        Return total duration of all timeable schedules.

        Returns
        -------
        schedule_duration : float
            Duration of current schedule

        """
        duration = sum(sched.get_schedule_duration() for sched in self._timeable_schedules)
        if not self._uses_timeable_repetitions:
            self._duration = duration * self._repetitions
        assert isinstance(self._duration, (int, float))
        return self._duration

    @property
    def duration(self) -> float | None:
        """
        Determine the cached duration of the schedule.

        Will return None if get_schedule_duration() has not been called before.
        """
        return self._duration

    @property
    def data(self) -> dict:
        """The dictionary data of a single contained timeable schedule."""
        timeable_schedule = self._timeable_schedule
        if timeable_schedule is None:
            raise RuntimeError("`data` dict unavailable on schedule with untimed operations")
        return timeable_schedule.data

    @property
    def operations(self) -> dict[str, Operation | TimeableSchedule]:
        """
        A dictionary of all unique operations used in the schedule.

        This specifies information on *what* operation to apply *where*.

        The keys correspond to the :attr:`~.Operation.hash` and values are instances
        of :class:`qblox_scheduler.operations.operation.Operation`.
        """
        timeable_schedule = self._timeable_schedule
        if timeable_schedule is None:
            raise RuntimeError("`operations` dict unavailable on schedule with untimed operations")
        return timeable_schedule.operations

    @property
    def schedulables(self) -> dict[str, Schedulable]:
        """
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

        """
        timeable_schedule = self._timeable_schedule
        if timeable_schedule is None:
            raise RuntimeError(
                "`schedulables` dict unavailable on schedule with untimed operations"
            )
        return timeable_schedule.schedulables

    def plot_circuit_diagram(
        self,
        figsize: tuple[int, int] | None = None,
        ax: Axes | None = None,
        plot_backend: Literal["mpl"] = "mpl",
        timeable_schedule_index: int | None = None,
    ) -> tuple[Figure | None, Axes | list[Axes]]:
        """
        Create a circuit diagram visualization of the schedule using the specified plotting backend.

        The circuit diagram visualization depicts the schedule at the quantum circuit
        layer. Because qblox-scheduler uses a hybrid gate-pulse paradigm, operations
        for which no information is specified at the gate level are visualized using an
        icon (e.g., a stylized wavy pulse) depending on the information specified at
        the quantum device layer.

        Alias of :func:`qblox_scheduler.schedules._visualization.circuit_diagram.circuit_diagram_matplotlib`.

        Parameters
        ----------
        figsize
            matplotlib figsize.
        ax
            Axis handle to use for plotting.
        plot_backend
            Plotting backend to use, currently only 'mpl' is supported
        timeable_schedule_index:
            Index of timeable schedule in schedule to plot. If None (the default),
            will only plot if the schedule contains a single timeable schedule.

        Returns
        -------
        fig
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

        """  # noqa: E501
        if timeable_schedule_index is None:
            timeable_schedule = self._timeable_schedule
            if timeable_schedule is None:
                raise RuntimeError("Can not plot schedules with untimed operations")
        else:
            timeable_schedules = self._timeable_schedules
            if timeable_schedule_index >= len(timeable_schedules):
                raise IndexError(f"No timeable schedule at index {timeable_schedule_index}")
            timeable_schedule = timeable_schedules[timeable_schedule_index]
        return timeable_schedule.plot_circuit_diagram(figsize, ax, plot_backend)

    def plot_pulse_diagram(
        self,
        port_list: list[str] | None = None,
        sampling_rate: float = 1e9,
        modulation: Literal["off", "if", "clock"] = "off",
        modulation_if: float = 0.0,
        plot_backend: Literal["mpl", "plotly"] = "mpl",
        x_range: tuple[float, float] = (-np.inf, np.inf),
        combine_waveforms_on_same_port: bool = True,
        timeable_schedule_index: int | None = None,
        **backend_kwargs,
    ) -> tuple[Figure, Axes] | go.Figure:
        """
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

        Parameters
        ----------
        port_list :
            A list of ports to show. If ``None`` (default) the first 8 ports encountered in the sequence are used.
        modulation :
            Determines if modulation is included in the visualization.
        modulation_if :
            Modulation frequency used when modulation is set to "if".
        sampling_rate :
            The time resolution used to sample the schedule in Hz.
        plot_backend:
            Plotting library to use, can either be 'mpl' or 'plotly'.
        x_range:
            The range of the x-axis that is plotted, given as a tuple (left limit, right
            limit). This can be used to reduce memory usage when plotting a small section of
            a long pulse sequence. By default (-np.inf, np.inf).
        combine_waveforms_on_same_port:
            By default True. If True, combines all waveforms on the same port into one
            single waveform. The resulting waveform is the sum of all waveforms on that
            port (small inaccuracies may occur due to floating point approximation). If
            False, the waveforms are shown individually.
        timeable_schedule_index:
            Index of timeable schedule in schedule to plot. If None (the default),
            will only plot if the schedule contains a single timeable schedule.
        backend_kwargs:
            Keyword arguments to be passed on to the plotting backend. The arguments
            that can be used for either backend can be found in the documentation of
            :func:`qblox_scheduler.schedules._visualization.pulse_diagram.pulse_diagram_matplotlib`
            and
            :func:`qblox_scheduler.schedules._visualization.pulse_diagram.pulse_diagram_plotly`.

        Returns
        -------
        Union[tuple[Figure, Axes], :class:`!plotly.graph_objects.Figure`]
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

        """  # noqa: E501
        if timeable_schedule_index is None:
            timeable_schedule = self._timeable_schedule
            if timeable_schedule is None:
                raise RuntimeError("Can not plot schedules with untimed operations")
        else:
            timeable_schedules = self._timeable_schedules
            if timeable_schedule_index >= len(timeable_schedules):
                raise IndexError(f"No timeable schedule at index {timeable_schedule_index}")
            timeable_schedule = timeable_schedules[timeable_schedule_index]
        return timeable_schedule.plot_pulse_diagram(
            port_list,
            sampling_rate,
            modulation,
            modulation_if,
            plot_backend,
            x_range,
            combine_waveforms_on_same_port,
            **backend_kwargs,
        )

    @property
    def timing_table(self) -> pd.io.formats.style.Styler:
        """
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

        Returns
        -------
        :
            styled_timing_table, a pandas Styler containing a dataframe with
            an overview of the timing of the pulses and acquisitions present in the
            schedule. The dataframe can be accessed through the .data attribute of
            the Styler.

        Raises
        ------
        ValueError
            When the absolute timing has not been determined during compilation.

        """  # noqa: E501
        timeable_schedule = self._timeable_schedule
        if timeable_schedule is None:
            raise ValueError("can not plot timing table for schedules with untimed operations")
        return timeable_schedule.timing_table

    def _add_timeable_schedule(self, timeable_schedule: TimeableSchedule) -> None:
        if len(self._experiments) == 1 and not self._experiment.steps:
            # First timeable schedule addition, set repetitions
            timeable_schedule.repetitions *= self._repetitions
            self._uses_timeable_repetitions = True
        elif self._timeable_schedule and self._uses_timeable_repetitions:
            # switch away from native repetitions
            self._timeable_schedule.repetitions //= self._repetitions
            self._uses_timeable_repetitions = False
        timeable_schedule.add_resources(self._resources)
        self._experiment.add(ExecuteSchedule(timeable_schedule))

    def _get_current_timeable_schedule(self) -> TimeableSchedule | None:
        if self._experiment.steps and isinstance(self._experiment.steps[-1], ExecuteSchedule):
            sched_step = self._experiment.steps[-1]
            if isinstance(sched_step.schedule, TimeableSchedule):
                return sched_step.schedule
        return None

    def _get_timeable_schedule(self) -> TimeableSchedule:
        # Can we reuse the still-pending schedule?
        timeable_schedule = self._get_current_timeable_schedule()
        if timeable_schedule is not None:
            return timeable_schedule

        # No, make a new schedule.
        if self._schedule_count is None:
            self._schedule_count = len(self._timeable_schedules)
        self._schedule_count += 1

        timeable_schedule = TimeableSchedule(
            f"{self._experiment.name} schedule {self._schedule_count}"
        )
        self._add_timeable_schedule(timeable_schedule)
        return timeable_schedule

    def get_used_port_clocks(self) -> set[tuple[str, str]]:
        """
        Extracts which port-clock combinations are used in this schedule.

        Returns
        -------
        :
            All (port, clock) combinations that operations in this schedule uses

        """
        port_clocks_used = set()
        for sched in self._timeable_schedules:
            port_clocks_used |= sched.get_used_port_clocks()
        return port_clocks_used

    def add_resources(self, resources_list: list) -> None:
        """Add wrapper for adding multiple resources."""
        timeable_schedule = self._last_timeable_schedule
        if timeable_schedule is not None:
            timeable_schedule.add_resources(resources_list)
        self._resources.extend(resources_list)

    def add_resource(self, resource: Resource) -> None:
        """Add a resource such as a channel or device element to the schedule."""
        timeable_schedule = self._last_timeable_schedule
        if timeable_schedule is not None:
            timeable_schedule.add_resource(resource)
        self._resources.append(resource)

    def declare(self, dtype: DType) -> Variable:
        """
        Declare a new variable.

        Parameters
        ----------
        dtype
            The data type of the variable.

        """
        return self._experiment.declare(dtype)

    def add(
        self,
        operation: Schedule | Operation | TimeableSchedule | Step,
        rel_time: float | Expression = 0,
        ref_op: Schedulable | str | None = None,
        ref_pt: OperationReferencePoint | None = None,
        ref_pt_new: OperationReferencePoint | None = None,
        label: str | None = None,
    ) -> Schedulable | None:
        """Add step, operation or timeable schedule to this schedule."""
        specified_timing_info = (
            rel_time != 0
            or ref_op is not None
            or ref_pt not in (None, "end")
            or ref_pt_new not in (None, "start")
            or label is not None
        )

        if isinstance(operation, Schedule):
            return self._add_schedule(
                operation,
                rel_time=rel_time,
                ref_op=ref_op,
                ref_pt=ref_pt,
                ref_pt_new=ref_pt_new,
                label=label,
            )
        elif isinstance(operation, Operation):
            timeable_schedule = self._get_timeable_schedule()
            return timeable_schedule.add(
                operation,
                rel_time=rel_time,
                ref_op=ref_op,
                ref_pt=ref_pt,
                ref_pt_new=ref_pt_new,
                label=label,
            )
        elif isinstance(operation, TimeableSchedule):
            last_schedule = self._get_current_timeable_schedule()
            if last_schedule is None and not specified_timing_info:
                self._add_timeable_schedule(operation)
            else:
                if last_schedule is None:
                    last_schedule = self._get_timeable_schedule()
                return last_schedule.add(
                    operation,
                    rel_time=rel_time,
                    ref_op=ref_op,
                    ref_pt=ref_pt,
                    ref_pt_new=ref_pt_new,
                    label=label,
                )
        elif isinstance(operation, Step):
            if rel_time != 0:
                raise ValueError("can not specify `rel_time` when adding experiment step")
            if ref_op is not None:
                raise ValueError("can not specify `ref_op` when adding experiment step")
            if ref_pt not in (None, "end"):
                raise ValueError("can not specify `ref_pt` when adding experiment step")
            if ref_pt_new not in (None, "start"):
                raise ValueError("can not specify `ref_pt_new` when adding experiment step")
            if label is not None:
                raise ValueError("can not specify `label` when adding experiment step")
            # switch away from timeable repetitions
            if self._uses_timeable_repetitions:
                timeable_schedule = self._timeable_schedule
                assert timeable_schedule is not None
                timeable_schedule.repetitions //= self._repetitions
                self._uses_timeable_repetitions = False
            self._experiment.steps.append(operation)
        else:
            raise TypeError(f"Unsupported type for adding to a schedule: {operation}")

    def _add_schedule(
        self,
        schedule: Schedule,
        rel_time: float | Expression = 0,
        ref_op: Schedulable | str | None = None,
        ref_pt: OperationReferencePoint | None = None,
        ref_pt_new: OperationReferencePoint | None = None,
        label: str | None = None,
    ) -> Schedulable | None:
        self._resources.extend(schedule._resources)
        # Merge single timeable schedule if available
        timeable_schedule = schedule._timeable_schedule
        if timeable_schedule is not None:
            assert isinstance(timeable_schedule, TimeableSchedule)
            target_timeable_schedule = self._get_timeable_schedule()
            return target_timeable_schedule.add(
                timeable_schedule,
                rel_time=rel_time,
                ref_op=ref_op,
                ref_pt=ref_pt,
                ref_pt_new=ref_pt_new,
                label=label,
            )
        else:
            if schedule.repetitions != 1:
                raise ValueError("can not add sub-schedule with repetitions")
            if rel_time != 0:
                raise ValueError("can not specify `rel_time` when adding sub-schedule")
            if ref_op is not None:
                raise ValueError("can not specify `ref_op` when adding sub-schedule")
            if ref_pt not in (None, "end"):
                raise ValueError("can not specify `ref_pt` when adding sub-schedule")
            if ref_pt_new not in (None, "start"):
                raise ValueError("can not specify `ref_pt_new` when adding sub-schedule")
            if label is not None:
                raise ValueError("can not specify `label` when adding sub-schedule")
            # Merge all steps
            for step in schedule._experiment.steps:
                self.add(step)

    @overload
    @contextmanager
    def loop(
        self,
        domain: LinearDomain,
        rel_time: float = 0,
        ref_op: Schedulable | str | None = None,
        ref_pt: OperationReferencePoint | None = None,
        ref_pt_new: OperationReferencePoint | None = None,
        strategy: LoopStrategy | None = None,
    ) -> Iterator[Variable]: ...
    @overload
    @contextmanager
    def loop(
        self,
        *domains: LinearDomain,
        rel_time: float = 0,
        ref_op: Schedulable | str | None = None,
        ref_pt: OperationReferencePoint | None = None,
        ref_pt_new: OperationReferencePoint | None = None,
        strategy: LoopStrategy | None = None,
    ) -> Iterator[list[Variable]]: ...
    @contextmanager
    def loop(
        self,
        domain: LinearDomain,
        *domains: LinearDomain,
        rel_time: float = 0,
        ref_op: Schedulable | str | None = None,
        ref_pt: OperationReferencePoint | None = None,
        ref_pt_new: OperationReferencePoint | None = None,
        strategy: LoopStrategy | None = None,
    ) -> Iterator[Variable | list[Variable]]:
        """
        Add a loop operation to the schedule, using a with-statement.

        Every operation added while the context manager is active, will be added to the loop body.

        Example:

        .. code-block::

            sched = Schedule()
            with sched.loop(linspace(start_amp, start_amp + 1.0, 11, dtype=DType.AMP)) as amp:
                sched.add(SquarePulse(amp=amp, duration=100e-9, port="q0:mw", clock="q0.01"))

        Parameters
        ----------
        domain
            The object that describes the domain to be looped over.
        domains
            Optional extra domains that will be looped over in parallel, in a zip-like fashion.
        rel_time
            relative time between the reference operation and the added operation.
            the time is the time between the "ref_pt" in the reference operation and
            "ref_pt_new" of the operation that is added.
        ref_op
            reference schedulable. If set to :code:`None`, will default
            to the last added operation.
        ref_pt
            reference point in reference operation must be one of
            :code:`"start"`, :code:`"center"`, :code:`"end"`, or :code:`None`; in case
            of :code:`None`,
            :func:`~qblox_scheduler.compilation._determine_absolute_timing` assumes
            :code:`"end"`.
        ref_pt_new
            reference point in added operation must be one of
            :code:`"start"`, :code:`"center"`, :code:`"end"`, or :code:`None`; in case
            of :code:`None`,
            :func:`~qblox_scheduler.compilation._determine_absolute_timing` assumes
            :code:`"start"`.
        strategy
            Strategy to use for implementing this loop, will default to
            :code:`None` indicating no preference.

        Yields
        ------
        variables
            The Variable objects that are created for each domain.

        """
        new_experiment = Experiment(name=self._experiment.name)
        self._experiments.append(new_experiment)

        variables: dict[Variable, LinearDomain] = {}
        all_domains = [domain, *domains]
        for dom in all_domains:
            var = self._experiment.declare(dom.dtype)
            variables[var] = dom

        # We created a temporary new Experiment for the loop body. This makes Schedule.add think we
        # cannot use timeable repetitions. We store the current status in case we can optimize to a
        # pure timeable loop.
        old_uses_timeable_repetitions = self._uses_timeable_repetitions

        try:
            if len(variables) == 1:
                yield next(iter(variables.keys()))
            else:
                yield list(variables.keys())
        finally:
            new_experiment = self._experiments.pop()

        # Figure out whether to optimize into a pure timeable schedule loop
        if (
            len(new_experiment.steps) == 1
            and isinstance(new_experiment.steps[0], ExecuteSchedule)
            and isinstance(new_experiment.steps[0].schedule, TimeableSchedule)
        ):
            sub_timeable_schedule = new_experiment.steps[0].schedule
            timeable_schedule = self._get_timeable_schedule()
            with timeable_schedule.loop(
                variables,
                rel_time=rel_time,
                ref_op=ref_op,
                ref_pt=ref_pt,
                ref_pt_new=ref_pt_new,
                strategy=strategy,
            ):
                timeable_schedule.add(sub_timeable_schedule)
            if old_uses_timeable_repetitions and not self._uses_timeable_repetitions:
                # Adding operations to the loop body modified the repetitions of the containing
                # schedule. Revert this.
                timeable_schedule.repetitions *= self.repetitions
                self._uses_timeable_repetitions = True
        else:
            # Else, make it an experiment loop
            if rel_time != 0:
                raise ValueError("can not specify `rel_time` when adding non-real-time loop")
            if ref_op is not None:
                raise ValueError("can not specify `ref_op` when adding non-real-time loop")
            if ref_pt not in (None, "end"):
                raise ValueError("can not specify `ref_pt` when adding non-real-time loop")
            if ref_pt_new not in (None, "start"):
                raise ValueError("can not specify `ref_pt_new` when adding non-real-time loop")
            if strategy is not None:
                raise ValueError("can not specify `strategy` when adding non-real-time loop")
            self.add(Loop(variables, new_experiment.steps))

    @contextmanager
    def repeat(self, n: int) -> Iterator[None]:
        """
        Add a loop operation to the schedule for a given amount of iterations,
        using a with-statement.

        Example:

        .. code-block::

            sched = Schedule()
            with sched.repeat(5):
                sched.add(SquarePulse(amp=some_amp, duration=100e-9, port="q0:mw", clock="q0.01"))

        Parameters
        ----------
        n
            The amount of times to repeat the loop body.

        """
        with self.loop(linspace(1, n, n, dtype=DType.NUMBER)) as _i:
            yield
