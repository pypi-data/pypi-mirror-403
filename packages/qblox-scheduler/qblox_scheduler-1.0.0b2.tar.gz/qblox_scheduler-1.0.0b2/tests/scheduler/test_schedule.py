# type: ignore[reportCallIssue] # TODO: Remove after refactoring SchedulerBaseModel.__init__
from typing import Any

import pytest

from qblox_scheduler import QuantumDevice
from qblox_scheduler.device_under_test.quantum_device import QuantumDevice
from qblox_scheduler.device_under_test.transmon_element import BasicTransmonElement
from qblox_scheduler.enums import SchedulingStrategy
from qblox_scheduler.experiments import (
    ExecuteSchedule,
    Loop,
    SetHardwareDescriptionField,
    SetHardwareOption,
    SetParameter,
)
from qblox_scheduler.experiments.parameters import UndefinedParameterError
from qblox_scheduler.operations.expressions import DType
from qblox_scheduler.operations.gate_library import Measure
from qblox_scheduler.operations.loop_domains import linspace
from qblox_scheduler.operations.pulse_library import IdlePulse
from qblox_scheduler.qblox.hardware_agent import HardwareAgent
from qblox_scheduler.schedule import Schedule
from qblox_scheduler.schedules.schedule import TimeableSchedule


@pytest.fixture
def simple_hardware_config() -> dict[str, Any]:
    return {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {
                    "2": {"instrument_type": "QCM"},
                    "6": {"instrument_type": "QCM_RF"},
                    "8": {"instrument_type": "QRM_RF"},
                },
                "sequence_to_file": False,
                "ref": "internal",
            }
        },
        "hardware_options": {
            "latency_corrections": {
                "q0:mw-q0.01": 8e-9,
            },
            "modulation_frequencies": {
                "q0:mw-q0.01": {"interm_freq": 80000000.0},
                "q0:res-q0.ro": {"lo_freq": 7500000000.0},
            },
        },
        "connectivity": {
            "graph": [
                ["cluster0.module6.complex_output_0", "q0:mw"],
                ["cluster0.module2.real_output_0", "q0:fl"],
                ["cluster0.module8.complex_output_0", "q0:res"],
            ]
        },
    }


def test_schedule_add():
    schedule = Schedule("test steps")

    # Simple single operation
    schedule.add(IdlePulse(50e-9), rel_time=20e-9)

    assert len(schedule._experiments) == 1
    assert len(schedule._experiment.steps) == 1

    schedule_step = schedule._experiment.steps[0]
    assert isinstance(schedule_step, ExecuteSchedule)
    assert len(schedule.schedulables) == 1
    assert isinstance(schedule_step.schedule, TimeableSchedule)

    # Subsequent timeable operations should be merged
    schedule.add(IdlePulse(20e-9))
    assert len(schedule._experiments) == 1
    assert len(schedule._experiment.steps) == 1
    assert len(schedule.schedulables) == 2

    # Non-timeable operations should add an extra step
    schedule.add(SetParameter("foo", 42))
    assert len(schedule._experiments) == 1
    assert len(schedule._experiment.steps) == 2

    # Convenience attributes should not be accessible anymore now that
    # we have untimed operations.
    with pytest.raises(RuntimeError):
        _ = schedule.schedulables
    with pytest.raises(RuntimeError):
        _ = schedule.operations


def test_schedule_subschedules():
    schedule = Schedule("test sub-schedule parent")

    # Simple single operation
    schedule.add(IdlePulse(50e-9), rel_time=20e-9)

    # Sub-schedule!
    sub_schedule = Schedule("test sub-schedule child")
    sub_schedule.add(IdlePulse(20e-9))
    schedule.add(sub_schedule)

    assert len(schedule._experiments) == 1
    assert len(schedule._experiment.steps) == 1

    schedule_step = schedule._experiment.steps[0]
    assert isinstance(schedule_step, ExecuteSchedule)
    assert len(schedule.schedulables) == 2
    assert isinstance(schedule_step.schedule, TimeableSchedule)


def test_schedule_repetitions():
    schedule = Schedule("test repetitions 1", repetitions=5)
    schedule.add(IdlePulse(50e-9), rel_time=20e-9)

    assert schedule._uses_timeable_repetitions
    assert isinstance(schedule._experiment.steps[0], ExecuteSchedule)
    assert schedule._experiment.steps[0].schedule.repetitions == schedule.repetitions

    # Now add an untimed step to make it non-timeable again
    schedule.add(SetParameter("foo", 42))
    assert not schedule._uses_timeable_repetitions
    assert isinstance(schedule._experiment.steps[0], ExecuteSchedule)
    assert schedule._experiment.steps[0].schedule.repetitions == 1


def test_schedule_native_loop():
    # Only timeable operations, native loop
    schedule = Schedule("test native loop", repetitions=10)
    schedule.add(IdlePulse(50e-9), rel_time=20e-9)
    with schedule.loop(linspace(10e-9, 20e-9, 11, DType.TIME)) as t1:
        schedule.add(IdlePulse(t1))
        with schedule.loop(linspace(50e-9, 100e-9, 11, DType.TIME)) as t2:
            schedule.add(IdlePulse(t2))

    assert len(schedule._experiments) == 1
    assert len(schedule._experiment.steps) == 1
    assert isinstance(schedule._experiment.steps[0], ExecuteSchedule)
    assert schedule._timeable_schedule
    assert schedule._timeable_schedule.repetitions == 10


def test_schedule_hybrid_loop():
    schedule = Schedule("test hybrid loop")
    schedule.add(IdlePulse(50e-9), rel_time=20e-9)
    with schedule.loop(linspace(10e-9, 20e-9, 11, DType.AMPLITUDE)) as amp:
        schedule.add(SetParameter("foo", amp))
        with schedule.loop(linspace(50e-9, 100e-9, 11, DType.TIME)) as t:
            schedule.add(IdlePulse(t))

    assert len(schedule._experiments) == 1
    assert len(schedule._experiment.steps) == 2

    loop_step = schedule._experiment.steps[1]
    assert isinstance(loop_step, Loop)
    assert len(loop_step.steps) == 2
    assert isinstance(loop_step.steps[0], SetParameter)
    assert isinstance(loop_step.steps[1], ExecuteSchedule)


def test_schedule_hybrid_untimeable_loop():
    schedule = Schedule("test untimeable loop")
    schedule.add(IdlePulse(50e-9), rel_time=20e-9)
    with schedule.loop(linspace(10e-9, 20e-9, 11, DType.AMPLITUDE)) as amp:
        schedule.add(SetParameter("foo", amp))
        with schedule.loop(linspace(50e-9, 100e-9, 11, DType.TIME)) as t:
            schedule.add(IdlePulse(t))
            schedule.add(SetParameter("bar", amp))

    assert len(schedule._experiments) == 1
    assert len(schedule._experiment.steps) == 2

    loop_step = schedule._experiment.steps[1]
    assert isinstance(loop_step, Loop)
    assert len(loop_step.steps) == 2
    assert isinstance(loop_step.steps[0], SetParameter)

    inner_loop_step = loop_step.steps[1]
    assert isinstance(inner_loop_step, Loop)
    assert len(inner_loop_step.steps) == 2
    assert isinstance(inner_loop_step.steps[0], ExecuteSchedule)
    assert isinstance(inner_loop_step.steps[1], SetParameter)


def test_schedule_hybrid_untimeable_loop_2():
    schedule = Schedule("test hybrid loop", repetitions=10)
    schedule.add(IdlePulse(50e-9), rel_time=20e-9)
    with schedule.loop(linspace(50e-9, 100e-9, 11, DType.TIME)) as t:
        schedule.add(IdlePulse(t))
        with schedule.loop(linspace(10e-9, 20e-9, 11, DType.AMPLITUDE)) as amp:
            schedule.add(SetParameter("foo", amp))

    assert len(schedule._experiments) == 1
    assert len(schedule._experiment.steps) == 2

    loop_step = schedule._experiment.steps[1]
    assert isinstance(loop_step, Loop)
    assert len(loop_step.steps) == 2
    assert isinstance(loop_step.steps[0], ExecuteSchedule)
    assert loop_step.steps[0].schedule.repetitions == 1
    assert isinstance(loop_step.steps[1], Loop)
    assert schedule.repetitions == 10


def test_schedule_device_parameter_setting(
    mocker, mock_quantum_device_basic_transmon_qblox_hardware
):
    quantum_device = mock_quantum_device_basic_transmon_qblox_hardware

    schedule = Schedule("test hardware parameter")
    step = SetParameter("scheduling_strategy", SchedulingStrategy.ALAP)
    schedule.add(step)

    spy = mocker.spy(step, "run")

    assert quantum_device.scheduling_strategy == SchedulingStrategy.ASAP
    schedule._experiment.run(quantum_device)
    assert quantum_device.scheduling_strategy == SchedulingStrategy.ASAP
    called_with_qdev = spy.call_args[0][0]
    assert called_with_qdev.scheduling_strategy == SchedulingStrategy.ALAP
    # Assert because quantum device is deepcopied
    assert quantum_device.instr_instrument_coordinator is not None


def test_schedule_element_parameter_setting(
    mocker, mock_quantum_device_basic_transmon_qblox_hardware
):
    quantum_device = mock_quantum_device_basic_transmon_qblox_hardware

    schedule = Schedule("test hardware parameter")
    step = SetParameter(("rxy", "amp180"), 0.69, element="q0")
    schedule.add(step)

    spy = mocker.spy(step, "run")

    assert quantum_device.elements["q0"].rxy.amp180 != 0.69
    schedule._experiment.run(quantum_device)
    assert quantum_device.elements["q0"].rxy.amp180 != 0.69
    called_with_qdev = spy.call_args[0][0]
    assert called_with_qdev.elements["q0"].rxy.amp180 == 0.69
    # Assert because quantum device is deepcopied
    assert quantum_device.instr_instrument_coordinator is not None


def test_schedule_hardware_option_setting(
    mocker, mock_quantum_device_basic_transmon_qblox_hardware
):
    quantum_device = mock_quantum_device_basic_transmon_qblox_hardware

    schedule = Schedule("test hardware option")
    step = SetHardwareOption("latency_corrections", 12e-9, port="q4:mw-q4.01")
    schedule.add(step)

    spy = mocker.spy(step, "run")

    hw_options = quantum_device.generate_hardware_compilation_config().hardware_options
    assert hw_options.latency_corrections["q4:mw-q4.01"] != 12e-9
    schedule._experiment.run(quantum_device)
    hw_options = quantum_device.generate_hardware_compilation_config().hardware_options
    assert hw_options.latency_corrections["q4:mw-q4.01"] != 12e-9
    called_with_qdev = spy.call_args[0][0]
    hw_options = called_with_qdev.generate_hardware_compilation_config().hardware_options
    assert hw_options.latency_corrections["q4:mw-q4.01"] == 12e-9
    # Assert because quantum device is deepcopied
    assert quantum_device.instr_instrument_coordinator is not None


def test_schedule_hardware_option_setting_persists_for_experiment(mocker, simple_hardware_config):
    quantum_device = QuantumDevice("quantum_device")
    q0 = BasicTransmonElement("q0")
    q0.rxy.amp180 = 0.115
    q0.rxy.beta = 2.5e-10
    q0.clock_freqs.f01 = 7.3e9
    q0.clock_freqs.f12 = 7.0e9
    q0.clock_freqs.readout = 7.7e9
    q0.measure.acq_delay = 100e-9
    q0.measure.acq_channel = 0
    quantum_device.add_element(q0)
    quantum_device.hardware_config = simple_hardware_config

    schedule = Schedule("test hardware option")
    schedule.add(SetHardwareOption("latency_corrections", 12e-9, port="q0:mw-q0.01"))
    schedule.add(Measure("q0"))

    step = SetParameter(("rxy", "amp180"), 0.69, element="q0")
    with schedule.loop(linspace(0, 10, 11, DType.NUMBER)):
        schedule.add(step)
        schedule.add(Measure("q0"))

    spy = mocker.spy(step, "run")

    hw_agent = HardwareAgent(quantum_device.hardware_config, quantum_device)  # type: ignore

    config = quantum_device.generate_hardware_compilation_config()
    assert config is not None
    hw_options = config.hardware_options
    assert hw_options is not None
    assert hw_options.latency_corrections is not None
    assert hw_options.latency_corrections["q0:mw-q0.01"] != 12e-9
    hw_agent.run(schedule)

    config = quantum_device.generate_hardware_compilation_config()
    assert config is not None
    hw_options = config.hardware_options
    assert hw_options is not None
    assert hw_options.latency_corrections is not None
    assert hw_options.latency_corrections["q0:mw-q0.01"] != 12e-9
    called_with_qdev = spy.call_args[0][0]
    hw_options = called_with_qdev.generate_hardware_compilation_config().hardware_options
    assert hw_options.latency_corrections["q0:mw-q0.01"] == 12e-9


def test_schedule_hardware_option_setting_nonexistent_port_raises(
    mock_quantum_device_basic_transmon_qblox_hardware,
):
    quantum_device = mock_quantum_device_basic_transmon_qblox_hardware

    schedule = Schedule("test hardware option")
    schedule.add(SetHardwareOption("output_att", 12, port="q20:mw-q20.01"))

    with pytest.raises(
        UndefinedParameterError,
        match="in 'set hardware option output_att to 12 for port q20:mw-q20.01'",
    ):
        schedule._experiment.run(quantum_device)


def test_schedule_hardware_option_setting_undefined_option_raises(simple_hardware_config):
    quantum_device = QuantumDevice("quantum_device")
    quantum_device.hardware_config = simple_hardware_config

    schedule = Schedule("test hardware option")
    schedule.add(SetHardwareOption("output_att", 12, port="q20:mw-q20.01"))

    with pytest.raises(
        UndefinedParameterError,
        match="in 'set hardware option output_att to 12 for port q20:mw-q20.01'",
    ):
        schedule._experiment.run(quantum_device)


def test_schedule_hardware_option_setting_undefined_option_create_new(simple_hardware_config):
    quantum_device = QuantumDevice("quantum_device")
    quantum_device.hardware_config = simple_hardware_config

    schedule = Schedule("test hardware option")
    schedule.add(SetHardwareOption("output_att", 12, port="q20:mw-q20.01", create_new=True))

    schedule._experiment.run(quantum_device)


def test_schedule_hardware_option_setting_nonexistent_port(
    mocker,
    mock_quantum_device_basic_transmon_qblox_hardware,
):
    quantum_device = mock_quantum_device_basic_transmon_qblox_hardware

    schedule = Schedule("test hardware option")
    step = SetHardwareOption("latency_corrections", 12e-9, port="q20:mw-q20.01", create_new=True)
    schedule.add(step)

    spy = mocker.spy(step, "run")

    hw_options = quantum_device.generate_hardware_compilation_config().hardware_options
    assert "q20:mw-q20.01" not in hw_options.latency_corrections
    schedule._experiment.run(quantum_device)

    called_with_qdev = spy.call_args[0][0]
    hw_options = called_with_qdev.generate_hardware_compilation_config().hardware_options
    assert hw_options.latency_corrections["q20:mw-q20.01"] == 12e-9


def test_schedule_hardware_description_setting(
    mocker, mock_quantum_device_basic_transmon_qblox_hardware
):
    quantum_device = mock_quantum_device_basic_transmon_qblox_hardware

    schedule = Schedule("test hardware description")
    step = SetHardwareDescriptionField(("modules", 2, "rf_output_on"), False, instrument="cluster0")
    schedule.add(step)

    spy = mocker.spy(step, "run")

    hw_description = quantum_device.generate_hardware_compilation_config().hardware_description
    assert hw_description["cluster0"].modules[2].rf_output_on is True
    schedule._experiment.run(quantum_device)
    hw_description = quantum_device.generate_hardware_compilation_config().hardware_description
    assert hw_description["cluster0"].modules[2].rf_output_on is True
    called_with_qdev = spy.call_args[0][0]
    hw_description = called_with_qdev.generate_hardware_compilation_config().hardware_description
    assert hw_description["cluster0"].modules[2].rf_output_on is False
