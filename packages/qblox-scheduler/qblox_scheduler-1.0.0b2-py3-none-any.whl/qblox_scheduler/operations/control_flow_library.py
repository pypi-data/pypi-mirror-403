# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Standard control flow operations for use with the qblox_scheduler."""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

from qblox_scheduler.backends.qblox import constants
from qblox_scheduler.enums import StrEnum
from qblox_scheduler.operations.operation import Operation

if TYPE_CHECKING:
    from qblox_scheduler.operations.loop_domains import LinearDomain
    from qblox_scheduler.operations.variables import Variable
    from qblox_scheduler.schedule import Schedule
    from qblox_scheduler.schedules.schedule import TimeableSchedule


class ControlFlowOperation(Operation, metaclass=ABCMeta):
    """
    Control flow operation that can be used as an ``Operation`` in ``.TimeableSchedule``.

    This is an abstract class. Each concrete implementation
    of the control flow operation decides how and when
    their ``body`` operation is executed.
    """

    @property
    @abstractmethod
    def body(self) -> Operation | TimeableSchedule:
        """Body of a control flow."""
        pass

    @body.setter
    @abstractmethod
    def body(self, value: Operation | TimeableSchedule) -> None:
        """Body of a control flow."""
        pass

    def __str__(self) -> str:
        """
        Represent the Operation as a string.

        Returns
        -------
        str
            description

        """
        return self._get_signature(self.data["control_flow_info"])

    def get_used_port_clocks(self) -> set[tuple[str, str]]:
        """
        Extracts which port-clock combinations are used in this control flow operation.

        Returns
        -------
        :
            All (port, clock) combinations that operations
            in the body of this control flow operation uses.

        """
        return self.body.get_used_port_clocks()


class LoopStrategy(StrEnum):
    """
    Strategy to use for implementing loops.

    REALTIME: Use native loops.
    UNROLLED: Unroll loop at compilation time into separate instructions.
    """

    REALTIME = "realtime"
    UNROLLED = "unrolled"


class LoopOperation(ControlFlowOperation):
    """
    Loop over another operation predefined times.

    Repeats the operation defined in ``body`` ``repetitions`` times.
    The actual implementation depends on the backend.

    One of ``domain`` or ``repetitions`` must be specified.

    Parameters
    ----------
    body
        Operation to be repeated
    repetitions
        Number of repetitions, by default None
    domain
        Linear domain to loop over, by default None
    t0
        Time offset, by default 0
    strategy
        Strategy to use for implementing this loop, by default None to make own decision

    """

    def __init__(
        self,
        body: Operation | TimeableSchedule | Schedule,
        *,
        repetitions: int | None = None,
        domain: dict[Variable, LinearDomain] | None = None,
        t0: float = 0.0,
        strategy: LoopStrategy | None = None,
    ) -> None:
        # Delayed to prevent circular imports
        from qblox_scheduler.schedules.schedule import TimeableSchedule

        if not isinstance(body, (Operation, TimeableSchedule)):
            timeable_schedule = body._timeable_schedule
            if timeable_schedule is None:
                raise ValueError(
                    "LoopOperation can not be defined over schedules "
                    "that contain non-realtime operations"
                )
            assert isinstance(timeable_schedule, TimeableSchedule)
            body = timeable_schedule

        if (repetitions is None and domain is None) or (
            repetitions is not None and domain is not None
        ):
            raise ValueError("One of `repetitions` or `domain` must be specified.")

        if domain is not None:
            nums = {d.num_steps for d in domain.values()}
            if len(nums) > 1:
                raise ValueError("Domains have different amount of steps.")
            repetitions = nums.pop()

        super().__init__(name="LoopOperation")
        self.data.update(
            {
                "control_flow_info": {
                    "body": body,
                    "domain": domain,
                    "repetitions": repetitions,
                    "t0": t0,
                    "strategy": strategy,
                },
            }
        )

    @property
    def body(self) -> Operation | TimeableSchedule:
        """Body of a control flow."""
        return self.data["control_flow_info"]["body"]

    @body.setter
    def body(self, value: Operation | TimeableSchedule) -> None:
        """Body of a control flow."""
        self.data["control_flow_info"]["body"] = value

    @property
    def duration(self) -> float:
        """Duration of a control flow."""
        return self.repetitions * self.data["control_flow_info"]["body"].duration

    @property
    def domain(self) -> dict[Variable, LinearDomain]:
        """Linear domain to loop over."""
        return self.data["control_flow_info"]["domain"]

    @property
    def repetitions(self) -> int:
        """Number of times the body will execute."""
        return self.data["control_flow_info"]["repetitions"]

    @property
    def strategy(self) -> LoopStrategy | None:
        """What strategy to use for implementing this loop."""
        return self.data["control_flow_info"].get("strategy", None)


class ConditionalOperation(ControlFlowOperation):
    """
    Conditional over another operation.

    If a preceding thresholded acquisition on ``qubit_name`` results in a "1", the
    body will be executed, otherwise it will generate a wait time that is
    equal to the time of the subschedule, to ensure the absolute timing of later
    operations remains consistent.

    Parameters
    ----------
    body
        Operation to be conditionally played
    qubit_name
        Name of the device element on which the body will be conditioned
    t0
        Time offset, by default 0
    hardware_buffer_time
        Time buffer, by default the minimum time between operations on the hardware

    Example
    -------

    A conditional reset can be implemented as follows:


    .. jupyter-execute::

        # relevant imports
        from qblox_scheduler import Schedule
        from qblox_scheduler.operations import ConditionalOperation, Measure, X

        # define conditional reset as a Schedule
        conditional_reset = Schedule("conditional reset")
        conditional_reset.add(Measure("q0", feedback_trigger_label="q0"))
        conditional_reset.add(
            ConditionalOperation(body=X("q0"), qubit_name="q0"),
            rel_time=364e-9,
        )

    .. versionadded:: 0.22.0

        For some hardware specific implementations, a ``hardware_buffer_time``
        might be required to ensure the correct timing of the operations. This will
        be added to the duration of the ``body`` to prevent overlap with other
        operations.

    """

    def __init__(
        self,
        body: Operation | TimeableSchedule | Schedule,
        qubit_name: str,
        t0: float = 0.0,
        hardware_buffer_time: float = constants.MIN_TIME_BETWEEN_OPERATIONS * 1e-9,
    ) -> None:
        # Delayed to prevent circular imports
        from qblox_scheduler.schedules.schedule import TimeableSchedule

        if not isinstance(body, (Operation, TimeableSchedule)):
            timeable_schedule = body._timeable_schedule
            if timeable_schedule is None:
                raise ValueError(
                    "ConditionalOperation can not be defined over schedules "
                    "that contain non-realtime operations"
                )
            assert isinstance(timeable_schedule, TimeableSchedule)
            body = timeable_schedule
        device_element_name = qubit_name
        super().__init__(name="ConditionalOperation")
        self.data.update(
            {
                "control_flow_info": {
                    "body": body,
                    "qubit_name": device_element_name,
                    "t0": t0,
                    "feedback_trigger_label": device_element_name,
                    "feedback_trigger_address": None,  # Filled in at compilation.
                    "hardware_buffer_time": hardware_buffer_time,
                },
            }
        )

    @property
    def body(self) -> Operation | TimeableSchedule:
        """Body of a control flow."""
        return self.data["control_flow_info"]["body"]

    @body.setter
    def body(self, value: Operation | TimeableSchedule) -> None:
        """Body of a control flow."""
        self.data["control_flow_info"]["body"] = value

    @property
    def duration(self) -> float:
        """Duration of a control flow."""
        return (
            self.data["control_flow_info"]["body"].duration
            + self.data["control_flow_info"]["hardware_buffer_time"]
        )


class ControlFlowSpec(metaclass=ABCMeta):
    """
    Control flow specification to be used at ``Schedule.add``.

    The users can specify any concrete control flow with
    the ``control_flow`` argument to ``Schedule.add``.
    The ``ControlFlowSpec`` is only a type which by itself
    cannot be used for the ``control_flow`` argument,
    use any concrete control flow derived from it.
    """

    @abstractmethod
    def create_operation(self, body: Operation | TimeableSchedule) -> Operation | TimeableSchedule:
        """Transform the control flow specification to an operation or schedule."""
        pass


class Loop(ControlFlowSpec):
    """
    Loop control flow specification to be used at ``Schedule.add``.

    For more information, see ``LoopOperation``.

    Parameters
    ----------
    repetitions
        Number of repetitions
    t0
        Time offset, by default 0
    strategy
        Strategy to use for implementing the loop, by default None

    """

    def __init__(
        self, repetitions: int, t0: float = 0.0, strategy: LoopStrategy | None = None
    ) -> None:
        self.repetitions = repetitions
        self.t0 = t0
        self.strategy = strategy

    def create_operation(self, body: Operation | TimeableSchedule) -> LoopOperation:
        """Transform the control flow specification to an operation or schedule."""
        return LoopOperation(body, repetitions=self.repetitions, t0=self.t0, strategy=self.strategy)


class Conditional(ControlFlowSpec):
    """
    Conditional control flow specification to be used at ``Schedule.add``.

    For more information, see ``ConditionalOperation``.

    Parameters
    ----------
    qubit_name
        Target device element.
    t0
        Time offset, by default 0

    """

    def __init__(self, qubit_name: str, t0: float = 0.0) -> None:
        self.device_element_name = qubit_name
        self.t0 = t0

    def create_operation(self, body: Operation | TimeableSchedule) -> ConditionalOperation:
        """Transform the control flow specification to an operation or schedule."""
        return ConditionalOperation(body, self.device_element_name, self.t0)
