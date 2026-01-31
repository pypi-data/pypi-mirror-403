import pytest

from qblox_scheduler import TimeableSchedule
from qblox_scheduler.backends import SerialCompiler
from qblox_scheduler.backends.qblox import constants
from qblox_scheduler.operations import SquarePulse
from qblox_scheduler.operations.acquisition_library import TriggerCount
from qblox_scheduler.operations.gate_library import Measure, Reset
from qblox_scheduler.operations.hardware_operations import long_square_pulse
from qblox_scheduler.operations.nv_native_library import ChargeReset, CRCount
from qblox_scheduler.operations.shared_native_library import SpectroscopyOperation
from qblox_scheduler.schedules.schedule import CompiledSchedule


def test_compilation_spectroscopy_operation_qblox_hardware(
    mock_setup_basic_nv_qblox_hardware,
    get_subschedule_operation,
):
    """SpectroscopyOperation can be compiled to the device layer and to qblox
    instructions.

    Verify that the device representation and the hardware instructions contain
    plausible content.
    """
    schedule = TimeableSchedule(name="Two Spectroscopy Pulses", repetitions=1)

    label1 = "Spectroscopy pulse 1"
    label2 = "Spectroscopy pulse 2"
    _ = schedule.add(SpectroscopyOperation("qe0"), label=label1)
    _ = schedule.add(SpectroscopyOperation("qe0"), label=label2)

    # SpectroscopyOperation is added to the operations.
    # It has "gate_info", but no "pulse_info" yet.
    spec_pulse_hash = SpectroscopyOperation("qe0").hash
    assert spec_pulse_hash in schedule.operations
    assert "gate_info" in schedule.operations[spec_pulse_hash]
    assert schedule.operations[spec_pulse_hash]["pulse_info"] == {}

    # Operation is added twice to schedulables and has no timing information yet.
    assert label1 in schedule.schedulables
    assert label2 in schedule.schedulables
    assert (
        "abs_time" not in schedule.schedulables[label1].data
        or schedule.schedulables[label1].data["abs_time"] is None
    )
    assert (
        "abs_time" not in schedule.schedulables[label2].data
        or schedule.schedulables[label2].data["abs_time"] is None
    )

    # We can plot the circuit diagram
    schedule.plot_circuit_diagram()

    quantum_device = mock_setup_basic_nv_qblox_hardware["quantum_device"]
    pulse_duration = quantum_device.get_element("qe0").spectroscopy_operation.duration
    pulse_amplitude = quantum_device.get_element("qe0").spectroscopy_operation.amplitude

    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Assert the spec pulse has been compiled to a Schedule
    assert spec_pulse_hash in compiled_sched.operations
    assert isinstance(compiled_sched.operations[spec_pulse_hash], TimeableSchedule)

    # Timing info has been added
    assert "abs_time" in compiled_sched.schedulables[label1].data
    assert "abs_time" in compiled_sched.schedulables[label2].data
    assert compiled_sched.schedulables[label1].data["abs_time"] == 0
    duration_pulse_1 = compiled_sched.operations[spec_pulse_hash].duration
    assert compiled_sched.schedulables[label2].data["abs_time"] == pytest.approx(
        0 + duration_pulse_1  # type: ignore  (type should be a float here)
    )

    if pulse_duration >= constants.PULSE_STITCHING_DURATION:
        compiled_long_square_pulse_parts = [
            get_subschedule_operation(compiled_sched.operations[spec_pulse_hash], [0, i])
            for i in range(3)
        ]
        reference_long_square_pulse = long_square_pulse(
            amp=pulse_amplitude,
            duration=pulse_duration,
            port="qe0:mw",
            clock="qe0.spec",
        )
        reference_long_square_pulse_parts = [
            get_subschedule_operation(reference_long_square_pulse, [i]) for i in range(3)
        ]
        assert compiled_long_square_pulse_parts == reference_long_square_pulse_parts
    else:
        assert (
            compiled_sched.operations[spec_pulse_hash].data["pulse_info"]
            == SquarePulse(
                amp=pulse_amplitude,
                duration=pulse_duration,
                port="qe0:mw",
                clock="qe0.spec",
            )["pulse_info"]
        )

    assert isinstance(compiled_sched, CompiledSchedule)
    assert "compiled_instructions" in compiled_sched.data


def test_compilation_reset_qblox_hardware(
    mock_setup_basic_nv_qblox_hardware, get_subschedule_operation
):
    """_Reset can be compiled to the device layer and to qblox
    instructions.

    Verify that the device representation and the hardware instructions contain
    plausible content.
    """
    schedule = TimeableSchedule(name="Reset", repetitions=1)
    label = "reset pulse"

    _ = schedule.add(Reset("qe0"), label=label)
    reset_hash = Reset("qe0").hash

    # We can plot the circuit diagram
    schedule.plot_circuit_diagram()

    quantum_device = mock_setup_basic_nv_qblox_hardware["quantum_device"]
    pulse_duration = quantum_device.get_element("qe0").reset.duration
    pulse_amplitude = quantum_device.get_element("qe0").reset.amplitude

    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    assert reset_hash in compiled_sched.operations

    # Timing info has been added
    assert "abs_time" in compiled_sched.schedulables[label].data
    assert compiled_sched.schedulables[label].data["abs_time"] == 0

    assert isinstance(compiled_sched, CompiledSchedule)
    assert "compiled_instructions" in compiled_sched.data

    operation_id = list(compiled_sched.schedulables.values())[0]["operation_id"]
    # We make the assumption here that the reset pulse is done with a
    # 'long_square_pulse', since the pulse is too long for a regular square
    # pulse.
    compiled_long_square_pulse_parts = [
        get_subschedule_operation(compiled_sched.operations[operation_id], [0, i]) for i in range(3)
    ]
    reference_long_square_pulse = long_square_pulse(
        amp=pulse_amplitude,
        duration=pulse_duration,
        port="qe0:optical_control",
        clock="qe0.ge1",
    )
    reference_long_square_pulse_parts = [
        get_subschedule_operation(reference_long_square_pulse, [i]) for i in range(3)
    ]
    assert compiled_long_square_pulse_parts == reference_long_square_pulse_parts


def test_compilation_measure_qblox_hardware(
    mock_setup_basic_nv_qblox_hardware, get_subschedule_operation
):
    """Measure can be compiled to the device layer and to qblox
    instructions.

    Verify that the device representation and the hardware instructions contain
    plausible content.
    """
    schedule = TimeableSchedule(name="Measure", repetitions=1)
    label = "measure pulse"

    _ = schedule.add(Measure("qe0"), label=label)
    measure_hash = Measure("qe0").hash

    # We can plot the circuit diagram
    schedule.plot_circuit_diagram()

    quantum_device = mock_setup_basic_nv_qblox_hardware["quantum_device"]

    quantum_device.get_element("qe0").measure.acq_delay = 1e-7

    pulse_duration = quantum_device.get_element("qe0").measure.pulse_duration
    pulse_amplitude = quantum_device.get_element("qe0").measure.pulse_amplitude
    acq_duration = quantum_device.get_element("qe0").measure.acq_duration

    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    assert measure_hash in compiled_sched.operations
    acquisition = get_subschedule_operation(compiled_sched, [0, 1])
    acquisition_info = acquisition["acquisition_info"]
    assert acquisition_info["t0"] == 1e-7
    assert acquisition_info["protocol"] == "TriggerCount"

    # Timing info has been added
    assert "abs_time" in compiled_sched.schedulables[label].data
    assert compiled_sched.schedulables[label].data["abs_time"] == 0

    assert isinstance(compiled_sched, CompiledSchedule)
    assert "compiled_instructions" in compiled_sched.data

    schedulables = list(compiled_sched.schedulables.values())
    assert len(schedulables) == 1
    operation_id = schedulables[0]["operation_id"]
    # We make the assumption here that the measure pulse is done with a
    # 'long_square_pulse', since the pulse is too long for a regular square
    # pulse.
    compiled_long_square_pulse_parts = [
        get_subschedule_operation(compiled_sched.operations[operation_id], [0, 0, i])
        for i in range(3)
    ]
    reference_long_square_pulse = long_square_pulse(
        amp=pulse_amplitude,
        duration=pulse_duration,
        port="qe0:optical_control",
        clock="qe0.ge0",
    )
    reference_long_square_pulse_parts = [
        get_subschedule_operation(reference_long_square_pulse, [i]) for i in range(3)
    ]
    assert compiled_long_square_pulse_parts == reference_long_square_pulse_parts
    assert (
        TriggerCount(port="qe0:optical_readout", clock="qe0.ge0", duration=acq_duration, t0=1e-7)[
            "acquisition_info"
        ]
        == acquisition["acquisition_info"]
    )


def test_compilation_charge_reset_qblox_hardware(
    mock_setup_basic_nv_qblox_hardware, get_subschedule_operation
):
    """ChargeReset can be compiled to the device layer and to qblox
    instructions.

    Verify that the device representation and the hardware instructions contain
    plausible content.
    """
    schedule = TimeableSchedule(name="ChargeReset", repetitions=1)
    label = "charge reset pulse"

    _ = schedule.add(ChargeReset("qe0"), label=label)
    charge_reset_hash = ChargeReset("qe0").hash

    # We can plot the circuit diagram
    schedule.plot_circuit_diagram()

    quantum_device = mock_setup_basic_nv_qblox_hardware["quantum_device"]
    pulse_duration = quantum_device.get_element("qe0").charge_reset.duration
    pulse_amplitude = quantum_device.get_element("qe0").charge_reset.amplitude

    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    assert charge_reset_hash in compiled_sched.operations

    # Timing info has been added
    assert "abs_time" in compiled_sched.schedulables[label].data
    assert compiled_sched.schedulables[label].data["abs_time"] == 0

    assert isinstance(compiled_sched, CompiledSchedule)
    assert "compiled_instructions" in compiled_sched.data

    schedulables = list(compiled_sched.schedulables.values())
    assert len(schedulables) == 1
    operation_id = schedulables[0]["operation_id"]
    # We make the assumption here that the reset pulse is done with a
    # 'long_square_pulse', since the pulse is too long for a regular square
    # pulse.
    compiled_long_square_pulse_parts = [
        get_subschedule_operation(compiled_sched.operations[operation_id], [0, i]) for i in range(3)
    ]
    reference_long_square_pulse = long_square_pulse(
        amp=pulse_amplitude,
        duration=pulse_duration,
        port="qe0:optical_control",
        clock="qe0.ionization",
    )
    reference_long_square_pulse_parts = [
        get_subschedule_operation(reference_long_square_pulse, [i]) for i in range(3)
    ]
    assert compiled_long_square_pulse_parts == reference_long_square_pulse_parts


def test_compilation_cr_count_qblox_hardware(mock_setup_basic_nv, get_subschedule_operation):
    """cr_count can be compiled to the device layer and to qblox
    instructions.

    Verify that the device representation and the hardware instructions contain
    plausible content.
    """
    schedule = TimeableSchedule(name="cr_count", repetitions=1)
    label = "cr_count pulse"

    _ = schedule.add(CRCount("qe0"), label=label)
    cr_count_hash = CRCount("qe0").hash

    # We can plot the circuit diagram
    schedule.plot_circuit_diagram()

    quantum_device = mock_setup_basic_nv["quantum_device"]
    quantum_device.get_element("qe0").cr_count.acq_delay = 1e-8

    pulse_duration = quantum_device.get_element("qe0").measure.pulse_duration
    acq_duration = quantum_device.get_element("qe0").measure.acq_duration

    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # The gate_info and acquisition_info remains unchanged, but the pulse info has been
    # added
    assert cr_count_hash in compiled_sched.operations
    acquisition = get_subschedule_operation(compiled_sched, [0, 2])
    acquisition_info = acquisition["acquisition_info"]
    assert acquisition_info["t0"] == 1e-8
    assert acquisition_info["protocol"] == "TriggerCount"

    ro_pulse = get_subschedule_operation(compiled_sched, [0, 0])
    sp_pulse = get_subschedule_operation(compiled_sched, [0, 1])

    # Timing info has been added
    assert "abs_time" in compiled_sched.schedulables[label].data
    assert compiled_sched.schedulables[label].data["abs_time"] == 0

    assert isinstance(compiled_sched, CompiledSchedule)
    assert "compiled_instructions" in compiled_sched.data
    assert ro_pulse["pulse_info"]["duration"] == pulse_duration
    assert ro_pulse.valid_pulse
    assert sp_pulse["pulse_info"]["duration"] == pulse_duration
    assert sp_pulse.valid_pulse
    assert acquisition["acquisition_info"]["duration"] == acq_duration
    assert acquisition.valid_acquisition
