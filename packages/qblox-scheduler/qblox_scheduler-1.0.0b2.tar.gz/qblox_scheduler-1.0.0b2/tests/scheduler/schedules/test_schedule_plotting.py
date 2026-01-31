# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch

import matplotlib as mpl
import plotly

from qblox_scheduler import TimeableSchedule
from qblox_scheduler.backends import SerialCompiler
from qblox_scheduler.compilation import _determine_absolute_timing
from qblox_scheduler.operations import LoopOperation
from qblox_scheduler.operations.pulse_library import SquarePulse


def test_schedule_plotting() -> None:
    sched = TimeableSchedule("test")
    sched.add(SquarePulse(amp=0.2, duration=4e-6, port="SDP"))
    sched = _determine_absolute_timing(schedule=sched)

    circuit_fig_mpl, _ = sched.plot_circuit_diagram()
    pulse_fig_mpl, _ = sched.plot_pulse_diagram()
    pulse_fig_plt = sched.plot_pulse_diagram(plot_backend="plotly")

    assert isinstance(circuit_fig_mpl, mpl.figure.Figure)
    assert isinstance(pulse_fig_mpl, mpl.figure.Figure)
    assert isinstance(pulse_fig_plt, plotly.graph_objects.Figure)


def test_plot_loop_operation(mock_setup_basic_nv_qblox_hardware):
    ramp = SquarePulse(amp=0.5, duration=3e-6, port="qe0:optical_readout")
    loop = LoopOperation(body=ramp, repetitions=5)
    schedule = TimeableSchedule("s")
    schedule.add(loop)
    quantum_device = mock_setup_basic_nv_qblox_hardware["quantum_device"]
    compiler = SerialCompiler(name="compiler")
    compiled_schedule = compiler.compile(
        schedule=schedule,
        config=quantum_device.generate_compilation_config(),
    )
    assert compiled_schedule.duration == 15e-6
    fig, _ax = compiled_schedule.plot_pulse_diagram()
    assert isinstance(fig, mpl.figure.Figure)
