"""
The tests in this file require pytest-mpl:
https://pytest-mpl.readthedocs.io/en/stable/

In brief, the tests will be run if you specify the `--mpl` option: `pytest --mpl`. If
any tests fail, you can generate new images with `pytest --mpl-generate-path=baseline`,
where "baseline" is the directory that the new images will end up in. You can then
verify the new images, and move them to
`tests/scheduler/schedules/visualization/baseline`.
"""

import pytest

from qblox_scheduler import TimeableSchedule
from qblox_scheduler.operations.acquisition_library import SSBIntegrationComplex
from qblox_scheduler.operations.control_flow_library import (
    ConditionalOperation,
    LoopOperation,
)
from qblox_scheduler.operations.gate_library import (
    CNOT,
    X90,
    Measure,
    Reset,
    Rxy,
    X,
    Y,
)
from qblox_scheduler.operations.pulse_library import SquarePulse
from qblox_scheduler.resources import ClockResource
from qblox_scheduler.schedules._visualization.circuit_diagram import (
    circuit_diagram_matplotlib,
)


@pytest.mark.mpl_image_compare(style="default", savefig_kwargs={"dpi": 300})
def test_hybrid_circuit_diagram_matplotlib():
    schedule = TimeableSchedule("Test experiment")

    q0, q1 = ("q0", "q1")
    ref_label_1 = "my_label"

    schedule.add(Reset(q0, q1))
    schedule.add(Rxy(90, 0, qubit=q0), label=ref_label_1)
    schedule.add(operation=CNOT(qC=q0, qT=q1))
    schedule.add(Measure(q0, q1), label="M0")

    f, _ = circuit_diagram_matplotlib(schedule)
    return f


@pytest.mark.mpl_image_compare(style="default", savefig_kwargs={"dpi": 300})
def test_hybrid_circuit_diagram_baseband_matplotlib():
    schedule = TimeableSchedule("Test experiment")

    q0, q1 = ("q0", "q1")
    ref_label_1 = "my_label"

    schedule.add(Reset(q0, q1))
    schedule.add(Rxy(90, 0, qubit=q0), label=ref_label_1)
    schedule.add(SquarePulse(0.8, 20e-9, port="q0:mw", clock="cl0.baseband"))
    schedule.add(operation=CNOT(qC=q0, qT=q1))
    schedule.add(Measure(q0, q1), label="M0")

    f, _ = circuit_diagram_matplotlib(schedule)
    return f


@pytest.mark.mpl_image_compare(style="default", savefig_kwargs={"dpi": 300})
def test_hybrid_circuit_acquisitions_matplotlib():
    """Tests drawing acquisitions"""
    schedule = TimeableSchedule("Test experiment")

    q0, q1 = ("q0", "q1")
    ref_label_1 = "my_label"

    schedule.add(Reset(q0, q1))
    schedule.add(Rxy(90, 0, qubit=q0), label=ref_label_1)
    schedule.add(SSBIntegrationComplex(port="q0:mw", clock="cl0.baseband", duration=1e-6))
    schedule.add(operation=CNOT(qC=q0, qT=q1))
    schedule.add(Measure(q0, q1), label="M0")

    f, _ = circuit_diagram_matplotlib(schedule)
    return f


@pytest.mark.mpl_image_compare(style="default", savefig_kwargs={"dpi": 300})
def test_hybrid_circuit_diagram_modulated_matplotlib():
    schedule = TimeableSchedule("Test experiment")

    q0, q1 = ("q0", "q1")
    ref_label_1 = "my_label"

    schedule.add_resource(ClockResource(name="q0.01", freq=6.02e9))

    schedule.add(Reset(q0, q1))
    schedule.add(Rxy(90, 0, qubit=q0), label=ref_label_1)
    schedule.add(SquarePulse(0.8, 20e-9, port="q0:mw", clock="q0.01"))
    schedule.add(operation=CNOT(qC=q0, qT=q1))
    schedule.add(Measure(q0, q1), label="M0")

    f, _ = circuit_diagram_matplotlib(schedule)
    return f


@pytest.mark.mpl_image_compare(style="default", savefig_kwargs={"dpi": 300})
def test_hybrid_circuit_diagram_unknown_port_matplotlib():
    schedule = TimeableSchedule("Test experiment")

    q0, q1 = ("q0", "q1")
    ref_label_1 = "my_label"

    schedule.add_resource(ClockResource(name="q0.01", freq=6.02e9))

    schedule.add(Reset(q0, q1))
    schedule.add(Rxy(90, 0, qubit=q0), label=ref_label_1)
    schedule.add(SquarePulse(0.8, 20e-9, port="unknown_port", clock="q0.01"))
    schedule.add(operation=CNOT(qC=q0, qT=q1))
    schedule.add(Measure(q0, q1), label="M0")

    f, _ = circuit_diagram_matplotlib(schedule)
    return f


@pytest.mark.mpl_image_compare(style="default", savefig_kwargs={"dpi": 300})
def test_circuit_diagram_simple_subschedule():
    inner_schedule = TimeableSchedule("inner", repetitions=1)
    ref = inner_schedule.add(Rxy(0, 0, "q0"), label="inner0")
    inner_schedule.add(Rxy(0, 1, "q0"), rel_time=40e-9, ref_op=ref, label="inner1")

    outer_schedule = TimeableSchedule("outer", repetitions=10)
    ref = outer_schedule.add(Rxy(1, 0, "q0"), label="outer0")
    outer_schedule.add(inner_schedule, rel_time=80e-9, ref_op=ref)
    outer_schedule.add(Measure("q0"), label="measure")

    f, _ = outer_schedule.plot_circuit_diagram()
    return f


@pytest.mark.mpl_image_compare(style="default", savefig_kwargs={"dpi": 300})
def test_circuit_diagram_simple_loop():
    inner_schedule = TimeableSchedule("inner", repetitions=1)
    ref = inner_schedule.add(Rxy(0, 0, "q0"), label="inner0")
    inner_schedule.add(Rxy(0, 1, "q0"), rel_time=40e-9, ref_op=ref, label="inner1")

    outer_schedule = TimeableSchedule("outer", repetitions=1)
    ref = outer_schedule.add(Rxy(1, 0, "q0"), label="outer0")

    outer_schedule.add(
        LoopOperation(body=inner_schedule, repetitions=10),
        label="loop",
    )

    outer_schedule.add(Measure("q0"), label="measure")
    f, _ = outer_schedule.plot_circuit_diagram()
    return f


@pytest.mark.mpl_image_compare(style="default", savefig_kwargs={"dpi": 300})
def test_circuit_diagram_one_conditional_op():
    schedule = TimeableSchedule("test")
    schedule.add_resource(ClockResource(name="q0.ro", freq=7e9))
    schedule.add(
        Measure(
            "q0",
            acq_protocol="ThresholdedAcquisition",
            feedback_trigger_label="q0",
        )
    )
    schedule.add(
        ConditionalOperation(body=X("q0"), qubit_name="q0"),
        rel_time=364e-9,
    )
    schedule.add(
        SquarePulse(amp=0.1, duration=16e-9, port="q0:res", clock="q0.ro"),
        ref_pt="start",
        rel_time=96e-9,
    )
    f, _ = schedule.plot_circuit_diagram()
    return f


@pytest.mark.mpl_image_compare(style="default", savefig_kwargs={"dpi": 300})
def test_circuit_diagram_complex_loops():
    inner = TimeableSchedule("inner")
    inner.add(X("q2"))

    inner2 = TimeableSchedule("inner2")
    inner2.add(Y("q1"))

    inner.add(
        LoopOperation(body=inner2, repetitions=2),
    )
    inner.add(Measure("q0"))

    sched = TimeableSchedule("amp_ref")
    sched.add(X90("q0"))
    sched.add(LoopOperation(body=inner, repetitions=3))
    sched.add(X90("q0"))
    sched.add(LoopOperation(body=inner2, repetitions=4))
    sched.add(X90("q0"))
    sched.add(LoopOperation(X("q0"), repetitions=2))

    f, _ = sched.plot_circuit_diagram()
    return f


@pytest.mark.mpl_image_compare(style="default", savefig_kwargs={"dpi": 300})
def test_circuit_diagram_mixed_control_flow():
    inner = TimeableSchedule("inner")
    inner.add(X("q1"))

    inner2 = TimeableSchedule("inner2")
    inner2.add(Y("q0"))

    inner.add(
        LoopOperation(body=inner2, repetitions=2),
    )
    inner.add(Measure("q0"))

    sched = TimeableSchedule("amp_ref")
    sched.add(Measure("q0", acq_protocol="ThresholdedAcquisition", feedback_trigger_label="q0"))
    sched.add(ConditionalOperation(body=inner, qubit_name="q0"), rel_time=364e-9)
    sched.add(X90("q1"))
    sched.add(LoopOperation(body=inner2, repetitions=4))
    sched.add(X90("q2"))
    sched.add(LoopOperation(X("q0"), repetitions=2))

    f, _ = sched.plot_circuit_diagram()
    return f
