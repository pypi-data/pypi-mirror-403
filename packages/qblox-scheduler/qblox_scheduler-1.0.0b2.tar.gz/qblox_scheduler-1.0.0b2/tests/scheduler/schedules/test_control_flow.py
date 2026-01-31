from unittest.mock import Mock

import pytest

from qblox_scheduler.backends.graph_compilation import SerialCompiler
from qblox_scheduler.backends.qblox.analog import (
    AnalogSequencerCompiler,
    BasebandModuleCompiler,
)
from qblox_scheduler.backends.qblox.conditional import (
    FeedbackTriggerCondition,
    FeedbackTriggerOperator,
)
from qblox_scheduler.backends.qblox.operation_handling.virtual import (
    ConditionalStrategy,
)
from qblox_scheduler.backends.qblox_backend import _SequencerCompilationConfig
from qblox_scheduler.backends.types.common import ModulationFrequencies
from qblox_scheduler.backends.types.qblox import (
    BoundedParameter,
    ComplexChannelDescription,
    OpInfo,
    SequencerOptions,
    StaticAnalogModuleProperties,
)
from qblox_scheduler.operations import SquarePulse
from qblox_scheduler.operations.control_flow_library import (
    ConditionalOperation,
    LoopOperation,
)
from qblox_scheduler.operations.expressions import DType
from qblox_scheduler.operations.gate_library import Measure, Rxy, X
from qblox_scheduler.operations.loop_domains import LinearDomain, linspace
from qblox_scheduler.schedules.schedule import TimeableSchedule, TimingConstraint
from qblox_scheduler.schemas.examples import utils

from .compiles_all_backends import _CompilesAllBackends


class TestSubschedules(_CompilesAllBackends):
    @classmethod
    def setup_class(cls):
        inner_schedule = TimeableSchedule("inner", repetitions=1)
        ref = inner_schedule.add(Rxy(0, 0, "q0"), label="inner0")
        inner_schedule.add(Rxy(0, 1, "q0"), rel_time=40e-9, ref_op=ref, label="inner1")

        outer_schedule = TimeableSchedule("outer", repetitions=10)
        ref = outer_schedule.add(Rxy(1, 0, "q0"), label="outer0")
        outer_schedule.add(inner_schedule, rel_time=80e-9, ref_op=ref)
        outer_schedule.add(Measure("q0"), label="measure")
        cls.uncomp_sched = outer_schedule

    def test_repetitions(self):
        assert self.uncomp_sched.repetitions == 10


class TestLoops:
    @classmethod
    def setup_class(cls):
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
        cls.uncomp_sched = outer_schedule

    def test_repetitions(self):
        assert self.uncomp_sched.repetitions == 1


def test_multiple_conditional_without_acquisition_raises(
    mock_setup_basic_transmon_with_standard_params,
):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    hardware_config = utils.load_json_example_scheme("qblox_hardware_config_transmon.json")
    quantum_device.hardware_config = hardware_config
    config = quantum_device.generate_compilation_config()

    schedule = TimeableSchedule("")
    schedule1 = TimeableSchedule("")
    schedule1.add(X("q0"))

    schedule.add(
        ConditionalOperation(body=schedule1, qubit_name="q0"),
    )
    schedule.add(
        ConditionalOperation(body=schedule1, qubit_name="q0"),
    )

    compiler = SerialCompiler(name="compiler")
    with pytest.raises(
        RuntimeError,
        match=(
            "Conditional control flow, "
            "``ConditionalOperation"
            '\\(body=TimeableSchedule "" containing \\(1\\) 1 \\(unique\\) operations.'
            ",qubit_name='q0',t0=0.0,hardware_buffer_time=4e-09\\)``, "
            "found without a preceding Conditional acquisition. "
        ),
    ):
        _ = compiler.compile(
            schedule,
            config=config,
        )


def test_nested_conditional_control_flow_raises_runtime_warning():
    static_hw_properties = StaticAnalogModuleProperties(
        instrument_type="QRM",
        max_acquisition_bin_count=0,
        max_awg_output_voltage=None,
        mixer_dc_offset_range=BoundedParameter(0, 0, ""),
        channel_name_to_digital_marker={},
    )
    sequencer_cfg = _SequencerCompilationConfig(
        sequencer_options=SequencerOptions(),
        hardware_description=ComplexChannelDescription(),
        portclock="q1:mw-q1.01",
        channel_name="complex_out_0",
        channel_name_measure=None,
        latency_correction=0,
        distortion_correction=None,
        lo_name=None,
        modulation_frequencies=ModulationFrequencies.model_validate(
            {"lo_freq": None, "interm_freq": 50e6}
        ),
        mixer_corrections=None,
    )
    mock_parent_module = Mock(BasebandModuleCompiler)
    type(mock_parent_module).instrument_cfg = Mock()
    type(mock_parent_module).qblox_acq_module_resource_manager = Mock()
    sequencer = AnalogSequencerCompiler(
        parent=mock_parent_module,
        index=0,
        static_hw_properties=static_hw_properties,
        sequencer_cfg=sequencer_cfg,
    )

    sequencer.op_strategies = [
        ConditionalStrategy(
            operation_info=OpInfo("Conditional", {}, 0),
            trigger_condition=FeedbackTriggerCondition(
                enable=True, operator=FeedbackTriggerOperator.OR, addresses=[1]
            ),
        ),
        ConditionalStrategy(
            operation_info=OpInfo("Conditional", {}, 0),
            trigger_condition=FeedbackTriggerCondition(
                enable=True, operator=FeedbackTriggerOperator.OR, addresses=[1]
            ),
        ),
    ]

    assert sequencer.parent is mock_parent_module

    with pytest.raises(
        RuntimeError,
        match="Nested conditional playback inside schedules is not supported by the Qblox backend.",
    ):
        sequencer.generate_qasm_program(
            ordered_op_strategies=sequencer._get_ordered_operations(),
            total_sequence_time=0,
            align_qasm_fields=False,
            repetitions=1,
        )


def test_loop_context_manager_simple():
    schedule = TimeableSchedule()
    with schedule.loop(linspace(0, 1.0, 100, DType.AMPLITUDE)) as amp:
        schedule.add(SquarePulse(amp=amp, duration=100e-9, port="port", clock="clock"))

    assert len(schedule.schedulables) == 1
    op_key = list(schedule.schedulables.values())[0]["operation_id"]
    op = schedule.operations[op_key]
    assert isinstance(op, LoopOperation)
    assert isinstance(op.body, TimeableSchedule)
    assert op["control_flow_info"]["domain"][amp] == LinearDomain(
        dtype=DType.AMPLITUDE, start=0, stop=1.0, num=100
    )


def test_loop_with_timing():
    schedule = TimeableSchedule()
    ref_op = schedule.add(SquarePulse(amp=0.5, duration=100e-9, port="port", clock="clock"))
    schedule.add(SquarePulse(amp=0.5, duration=100e-9, port="port", clock="clock"))
    with schedule.loop(
        linspace(0, 1.0, 100, DType.AMPLITUDE), rel_time=240e-9, ref_op=ref_op, ref_pt="end"
    ) as amp:
        schedule.add(SquarePulse(amp=amp, duration=100e-9, port="port", clock="clock"))

    last_added = list(schedule.schedulables)[-1]
    desired_constraints = [
        TimingConstraint(
            ref_schedulable=ref_op["label"],
            ref_pt="end",
            ref_pt_new=None,
            rel_time=2.4e-07,
        )
    ]
    assert schedule.schedulables[last_added]["timing_constraints"] == desired_constraints
