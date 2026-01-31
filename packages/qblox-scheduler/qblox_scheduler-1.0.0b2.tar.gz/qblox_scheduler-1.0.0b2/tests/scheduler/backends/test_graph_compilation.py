"""
This test style covers the classes and functions in the backends/graph_compilation.py
file.
"""

from copy import deepcopy

import networkx as nx
import pytest
from matplotlib.axes import Axes

from qblox_scheduler import TimeableSchedule
from qblox_scheduler.backends.graph_compilation import (
    ScheduleCompiler,
    SerialCompiler,
    SimpleNode,
)
from qblox_scheduler.operations.gate_library import Reset
from qblox_scheduler.schedules.schedule import CompiledSchedule


def dummy_compile_add_reset_q0(schedule: TimeableSchedule, config=None) -> TimeableSchedule:
    schedule.add(Reset("q0"))
    return schedule


dummy_node_a = SimpleNode(
    name="dummy_node_A",
    compilation_func=dummy_compile_add_reset_q0,
)


dummy_node_b = SimpleNode(
    name="dummy_node_B",
    compilation_func=dummy_compile_add_reset_q0,
)

dummy_node_c = SimpleNode(
    name="dummy_node_C",
    compilation_func=dummy_compile_add_reset_q0,
)


dummy_node_d = SimpleNode(
    name="dummy_node_D",
    compilation_func=dummy_compile_add_reset_q0,
)


def test_qblox_compiler_init_defaults():
    compiler = ScheduleCompiler()
    assert compiler.name == "compiler"
    assert compiler.quantum_device is None


def test_multiple_compilers_with_the_same_name():
    compiler1 = ScheduleCompiler("compiler")
    compiler2 = ScheduleCompiler("compiler")
    assert compiler1 != compiler2
    assert compiler1 is not compiler2


def test_draw_backend():
    """
    Tests if we can visualize a graph defined by a generic backend.
    This test will only test if the draw code can be executed and a matplotlib figure
    is created. It will not test the details of how the figure looks.
    """
    qblox_scheduler_compilation = ScheduleCompiler(name="test")

    with pytest.raises(RuntimeError):
        # because the graph is not initialized yet.
        qblox_scheduler_compilation.draw()

    # this is a private attribute, normally this is set using the construct graph
    # based on a config file, but here we want to keep the test of the drawing backend
    # uncoupled from the configs.
    qblox_scheduler_compilation._task_graph = nx.DiGraph()

    qblox_scheduler_compilation._task_graph.add_node(dummy_node_a)
    qblox_scheduler_compilation._task_graph.add_node(dummy_node_b)
    qblox_scheduler_compilation._task_graph.add_edge(dummy_node_a, dummy_node_b)

    qblox_scheduler_compilation._task_graph.add_edge(dummy_node_c, dummy_node_b)
    qblox_scheduler_compilation._task_graph.add_edge(dummy_node_c, dummy_node_a)

    ax = qblox_scheduler_compilation.draw()
    assert isinstance(ax, Axes)


def test_compiled_schedule_invariance(mock_setup_basic_transmon_with_standard_params):
    """If the last compilation step returns an instance of CompiledSchedule (also
    inherited), use this instance instead of creating a new CompiledSchedule.

    This test skips the compilation step and passes the CompiledSchedule directly
    to the compilation.
    """
    mock_setup = mock_setup_basic_transmon_with_standard_params
    schedule = TimeableSchedule("test_schedule")
    _ = schedule.add(Reset("q0"))

    class InheritedFromCompiledSchedule(CompiledSchedule):
        pass

    compiled_schedule = SerialCompiler("test", mock_setup["quantum_device"]).compile(
        InheritedFromCompiledSchedule(schedule)
    )
    assert isinstance(compiled_schedule, CompiledSchedule)
    assert isinstance(compiled_schedule, InheritedFromCompiledSchedule)


def test_schedule_invariance_after_compilation(
    mock_setup_basic_transmon_with_standard_params,
):
    mock_setup = mock_setup_basic_transmon_with_standard_params
    original_schedule = TimeableSchedule("test_schedule")
    original_schedule.add(Reset("q0"))

    quantum_device = mock_setup["quantum_device"]
    quantum_device.keep_original_schedule = True
    config = quantum_device.generate_compilation_config()

    schedule = deepcopy(original_schedule)
    _ = SerialCompiler("test").compile(schedule=schedule, config=config)

    assert schedule == original_schedule


def test_do_not_keep_original_schedule(
    mock_setup_basic_transmon_with_standard_params,
):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]
    schedule = TimeableSchedule("test_schedule")
    schedule.add(Reset("q0"))

    quantum_device.keep_original_schedule = True
    compiled_schedule_kept_schedule = SerialCompiler("test", quantum_device).compile(
        schedule=schedule
    )

    quantum_device.keep_original_schedule = False
    compiled_schedule_not_kept_schedule = SerialCompiler("test", quantum_device).compile(
        schedule=schedule
    )

    assert compiled_schedule_kept_schedule == compiled_schedule_not_kept_schedule
