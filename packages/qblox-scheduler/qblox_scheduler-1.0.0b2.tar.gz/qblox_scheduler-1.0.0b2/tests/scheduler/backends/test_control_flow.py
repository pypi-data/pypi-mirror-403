"""
This test style covers the control flow passes in `compilation.py`.
file.
"""

from qblox_scheduler.backends.graph_compilation import SerialCompiler
from qblox_scheduler.operations.control_flow_library import LoopOperation, LoopStrategy
from qblox_scheduler.operations.expressions import DType
from qblox_scheduler.operations.gate_library import Reset
from qblox_scheduler.operations.loop_domains import linspace
from qblox_scheduler.operations.pulse_library import SquarePulse
from qblox_scheduler.schedules.schedule import TimeableSchedule, TimeableScheduleBase


def test_rolled_loops(
    mock_setup_basic_transmon_with_standard_params,
):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    schedule = TimeableSchedule("rolled_schedule")
    schedule.add(Reset("q0"))
    with schedule.loop(
        linspace(0.1, 1.0, 10, dtype=DType.AMPLITUDE), strategy=LoopStrategy.REALTIME
    ) as amp:
        schedule.add(SquarePulse(amp=amp, duration=20e-9, port="q0:f1"))

    compiled_schedule = SerialCompiler("test", quantum_device).compile(schedule=schedule)
    loop_operation_id = list(compiled_schedule.schedulables.values())[1]["operation_id"]
    loop_operation = compiled_schedule.operations[loop_operation_id]
    assert isinstance(loop_operation, LoopOperation)


def test_unrolled_loops(
    mock_setup_basic_transmon_with_standard_params,
):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]
    domain_outer = linspace(0.1, 1.0, 2, dtype=DType.AMPLITUDE)
    domain_inner = linspace(0.1, 1.0, 10, dtype=DType.AMPLITUDE)

    schedule = TimeableSchedule("unrolled_schedule")
    schedule.add(Reset("q0"))
    with (
        schedule.loop(domain_outer),
        schedule.loop(domain_inner, strategy=LoopStrategy.UNROLLED) as amp_inner,
    ):
        schedule.add(SquarePulse(amp=amp_inner, duration=20e-9, port="q0:f1"))

    compiled_schedule = SerialCompiler("test", quantum_device).compile(schedule=schedule)

    assert len(compiled_schedule.schedulables.values()) == 2
    outer_loop_id = list(compiled_schedule.schedulables.values())[1]["operation_id"]
    outer_loop = compiled_schedule.operations[outer_loop_id]
    assert isinstance(outer_loop, LoopOperation)

    assert isinstance(outer_loop.body, TimeableScheduleBase)
    assert len(outer_loop.body.schedulables) == 1
    inner_loop_subschedule_id = list(outer_loop.body.schedulables.values())[0]["operation_id"]
    inner_loop_subschedule = outer_loop.body.operations[inner_loop_subschedule_id]
    assert isinstance(inner_loop_subschedule, TimeableScheduleBase)
    assert len(inner_loop_subschedule.schedulables) == len(domain_inner)

    for schedulable, cur_amp in zip(
        inner_loop_subschedule.schedulables.values(), domain_inner.values(), strict=False
    ):
        cur_op = inner_loop_subschedule.operations[schedulable["operation_id"]]
        if isinstance(cur_op, TimeableScheduleBase):
            cur_op = list(cur_op.operations.values())[0]
        assert isinstance(cur_op, SquarePulse)
        assert cur_op.data["pulse_info"]["amp"] == cur_amp


def test_repeat(
    mock_setup_basic_transmon_with_standard_params,
):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    schedule = TimeableSchedule("unrolled_schedule")
    schedule.add(Reset("q0"))
    with schedule.repeat(5):
        schedule.add(SquarePulse(amp=2, duration=20e-9, port="q0:f1"))

    compiled_schedule = SerialCompiler("test", quantum_device).compile(schedule=schedule)
    loop_operation_id = list(compiled_schedule.schedulables.values())[1]["operation_id"]
    loop_operation = compiled_schedule.operations[loop_operation_id]
    assert isinstance(loop_operation, LoopOperation)

    loop_domains = loop_operation.domain
    assert len(loop_domains) == 1
    loop_domain = next(iter(loop_domains.values()))
    assert loop_domain.num_steps == 5
