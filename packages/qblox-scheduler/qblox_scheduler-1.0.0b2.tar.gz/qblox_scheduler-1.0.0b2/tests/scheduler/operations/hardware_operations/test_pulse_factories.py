"""Tests for pulse factory functions."""

from functools import partial

import pytest

from qblox_scheduler import ClockResource, QuantumDevice, SerialCompiler, TimeableSchedule
from qblox_scheduler.backends.qblox import constants
from qblox_scheduler.backends.qblox_backend import (
    ClusterDescription,
    QbloxHardwareCompilationConfig,
    QbloxHardwareOptions,
)
from qblox_scheduler.backends.types.qblox import QCMDescription
from qblox_scheduler.compilation import _unroll_single_loop
from qblox_scheduler.operations import IdlePulse, RampPulse
from qblox_scheduler.operations.control_flow_library import LoopOperation
from qblox_scheduler.operations.hardware_operations.pulse_factories import (
    long_chirp_pulse,
    long_ramp_pulse,
    long_square_pulse,
    staircase_pulse,
)
from qblox_scheduler.operations.operation import Operation
from qblox_scheduler.operations.pulse_factories import (
    non_implemented_pulse,
    nv_spec_pulse_mw,
    rxy_drag_pulse,
    rxy_gauss_pulse,
    rxy_pulse,
)
from qblox_scheduler.operations.pulse_library import (
    ReferenceMagnitude,
    SquarePulse,
    VoltageOffset,
)


def test_rxy_drag_pulse():
    """Test a long_ramp_pulse that is composed of one part."""
    pulse = rxy_drag_pulse(
        amp180=0.6,
        beta=5e-10,
        theta=200,
        phi=19,
        port="q0:res",
        duration=1e-7,
        clock="q0.ro",
    )
    assert pulse.data["pulse_info"] == {
        "wf_func": "qblox_scheduler.waveforms.drag",
        "amplitude": 0.6 * 200 / 180,
        "beta": 5e-10,
        "reference_magnitude": None,
        "duration": 1e-7,
        "phase": 19,
        "nr_sigma": 4,
        "sigma": None,
        "clock": "q0.ro",
        "port": "q0:res",
        "t0": 0,
    }


def test_rxy_gauss_pulse():
    """Test a long_ramp_pulse that is composed of one part."""
    pulse = rxy_gauss_pulse(
        amp180=0.8, theta=180, phi=10, port="q0:res", duration=1e-7, clock="q0.ro"
    )
    assert pulse.data["pulse_info"] == {
        "wf_func": "qblox_scheduler.waveforms.drag",
        "amplitude": 0.8,
        "beta": 0,
        "reference_magnitude": None,
        "duration": 1e-7,
        "phase": 10,
        "nr_sigma": 4,
        "sigma": None,
        "clock": "q0.ro",
        "port": "q0:res",
        "t0": 0,
    }


def test_rxy_pulse():
    """Test the rxy_pulse"""
    pulse = rxy_pulse(
        amp180=0.8,
        theta=180,
        phi=10,
        port="q0:res",
        duration=100e-9,
        clock="q0.ro",
        skewness=0.0,
        pulse_shape="SkewedHermitePulse",
    )
    assert pulse.data["pulse_info"] == {
        "wf_func": "qblox_scheduler.waveforms.skewed_hermite",
        "duration": 100e-9,
        "amplitude": 0.8,
        "skewness": 0.0,
        "phase": 10,
        "port": "q0:res",
        "clock": "q0.ro",
        "reference_magnitude": None,
        "t0": 0.0,
    }


def test_unsupported_pulse_shape_rxy():
    """Test rxy_pulse with unsupported pulse shape."""
    with pytest.raises(
        ValueError,
        match=r"Unsupported pulse shape: \w+\. Use 'SkewedHermitePulse' or 'GaussPulse'\.",
    ):
        rxy_pulse(
            amp180=0.8,
            theta=180,
            phi=10,
            port="q0:res",
            duration=100e-9,
            clock="q0.ro",
            skewness=0.0,
            pulse_shape="Staircase",  # type: ignore
        )


def test_unsupported_pulse_shape_nv_spec():
    """Test nv_spec_pulse_mw with unsupported pulse shape."""
    with pytest.raises(
        ValueError,
        match=(
            r"Unsupported pulse shape: \w+\. "
            r"Use 'SquarePulse', 'SkewedHermitePulse', or 'GaussPulse'\."
        ),
    ):
        nv_spec_pulse_mw(
            duration=10e-9,
            amplitude=0.5,
            clock="q0.ro",
            port="q0:res",
            pulse_shape="Staircase",  # type: ignore
        )


def test_nv_spec_pulse_mw_square():
    """Test the nv_spec_pulse_mw with SquarePulse."""
    pulse = nv_spec_pulse_mw(
        duration=1e-7,
        amplitude=0.8,
        clock="q0.ro",
        port="q0:res",
        pulse_shape="SquarePulse",
    )
    assert pulse.data["pulse_info"] == {
        "wf_func": "qblox_scheduler.waveforms.square",
        "amp": 0.8,
        "duration": 1e-7,
        "port": "q0:res",
        "clock": "q0.ro",
        "reference_magnitude": None,
        "t0": 0,
    }


def test_nv_spec_pulse_mw_skewed_hermite():
    """Test the nv_spec_pulse_mw with SkewedHermitePulse."""
    pulse = nv_spec_pulse_mw(
        duration=1e-7,
        amplitude=0.8,
        clock="q0.ro",
        port="q0:res",
        pulse_shape="SkewedHermitePulse",
    )
    assert pulse.data["pulse_info"] == {
        "wf_func": "qblox_scheduler.waveforms.skewed_hermite",
        "amplitude": 0.8,
        "duration": 1e-7,
        "skewness": 0.0,
        "phase": 0,
        "port": "q0:res",
        "clock": "q0.ro",
        "reference_magnitude": None,
        "t0": 0.0,
    }


def test_nv_spec_pulse_mw_gauss():
    """Test the nv_spec_pulse_mw with GaussPulse."""
    pulse = nv_spec_pulse_mw(
        duration=1e-7,
        amplitude=0.8,
        clock="q0.ro",
        port="q0:res",
        pulse_shape="GaussPulse",
    )
    assert pulse.data["pulse_info"] == {
        "wf_func": "qblox_scheduler.waveforms.drag",
        "amplitude": 0.8,
        "beta": 0,
        "reference_magnitude": None,
        "duration": 100e-9,
        "phase": 0,
        "nr_sigma": 4,
        "sigma": None,
        "clock": "q0.ro",
        "port": "q0:res",
        "t0": 0,
    }


def test_short_long_ramp_pulse():
    """Test a long_ramp_pulse that is composed of one part."""
    pulse = long_ramp_pulse(amp=0.8, duration=1e-7, port="q0:res")
    operations = list(pulse.operations.values())
    assert len(operations) == 1
    assert operations[0].data["pulse_info"] == {
        "wf_func": "qblox_scheduler.waveforms.ramp",
        "amp": 0.8,
        "reference_magnitude": None,
        "duration": pytest.approx(1e-07),
        "offset": 0,
        "t0": 0.0,
        "clock": "cl0.baseband",
        "port": "q0:res",
    }


def test_long_ramp_pulse():
    """Test a long_ramp_pulse that is composed of multiple parts."""
    pulse = long_ramp_pulse(amp=0.5, duration=4.5e-6, offset=-0.2, port="q0:res")
    operations = list(pulse.operations.values())

    ramp_parts = []
    offsets = []

    assert isinstance(operations[0], LoopOperation)
    unrolled_loop = _unroll_single_loop(operations[0])
    # This is a schedule with two sub-schedules
    sub_schedules: list[TimeableSchedule] = list(unrolled_loop.operations.values())  # type: ignore
    operations = [op for sched in sub_schedules for op in sched.operations.values()] + operations[
        1:
    ]

    for op in operations:
        pulse_info = op.data["pulse_info"]
        if "offset_path_I" in pulse_info:
            offsets.append(pulse_info)
        else:
            ramp_parts.append(pulse_info)

    assert offsets[0]["offset_path_I"] == pytest.approx(-0.2)
    assert offsets[1]["offset_path_I"] == pytest.approx(-0.2 + 0.5 * 2 / 4.5)
    assert sum(pul_inf["amp"] for pul_inf in ramp_parts) == pytest.approx(0.5)
    assert sum(pul_inf["duration"] for pul_inf in ramp_parts) == pytest.approx(4.5e-6)
    assert ramp_parts[-1]["offset"] + ramp_parts[-1]["amp"] == pytest.approx(0.3)
    assert offsets[-1]["offset_path_I"] == pytest.approx(0.0)


def test_long_square_pulse():
    """Test a long square pulse."""
    port = "q0:res"
    clock = "q0.ro"
    pulse = long_square_pulse(amp=0.8, duration=1e-3, port=port, clock=clock)
    operations = list(pulse.operations.values())
    assert len(operations) == 3
    assert (
        operations[0]["pulse_info"]
        == VoltageOffset(offset_path_I=0.8, offset_path_Q=0.0, port=port, clock=clock)["pulse_info"]
    )
    assert (
        operations[1]["pulse_info"]
        == VoltageOffset(
            offset_path_I=0.0,
            offset_path_Q=0.0,
            port=port,
            clock=clock,
        )["pulse_info"]
    )
    assert (
        operations[2]["pulse_info"]
        == SquarePulse(amp=0.8, duration=4e-9, port=port, clock=clock)["pulse_info"]
    )


def test_long_square_pulse_that_is_too_short():
    """A square pulse less than `constants.MIN_TIME_BETWEEN_OPERATIONS` should error"""
    with pytest.raises(ValueError, match=f"{constants.MIN_TIME_BETWEEN_OPERATIONS}"):
        long_square_pulse(amp=0.8, duration=1e-9, port="", clock="")


def test_long_square_pulse_that_is_exactly_long_enough():
    """A square pulse less than `constants.MIN_TIME_BETWEEN_OPERATIONS` should error"""
    pulse = long_square_pulse(amp=0.8, duration=4e-9, port="", clock="")
    operations = list(pulse.operations.values())
    assert len(operations) == 1
    assert operations[0] == SquarePulse(0.8, 4e-9, port="", clock="")


def test_long_square_pulse_with_t0():
    port = "q0:res"
    clock = "q0.ro"
    pulse = long_square_pulse(amp=0.8, duration=1e-3, port=port, clock=clock, t0=100e-9)

    operations = list(pulse.operations.values())
    assert len(operations) == 3
    assert operations[0] == VoltageOffset(0.8, 0.0, port="q0:res", clock="q0.ro")
    assert operations[1] == VoltageOffset(0.0, 0.0, port="q0:res", clock="q0.ro")
    assert operations[2] == SquarePulse(0.8, 4e-9, port="q0:res", clock="q0.ro")

    schedulables = list(pulse.schedulables.values())
    assert schedulables[0]["timing_constraints"][0]["rel_time"] == 100e-9
    assert schedulables[1]["timing_constraints"][0]["rel_time"] == 1e-3 - 4e-9
    assert schedulables[2]["timing_constraints"][0]["rel_time"] == 0


def test_staircase():
    """Test a staircase pulse."""
    pulse = staircase_pulse(
        start_amp=0.1,
        final_amp=0.9,
        num_steps=20,
        duration=1e-3,
        port="q0:res",
        clock="q0.ro",
    )

    operations = list(pulse.operations.values())
    assert isinstance(operations[0], LoopOperation)
    assert operations[1] == VoltageOffset(0.9, 0.0, port="q0:res", clock="q0.ro")
    assert operations[2] == VoltageOffset(0.0, 0.0, port="q0:res", clock="q0.ro")
    assert operations[3] == SquarePulse(0.9, 4e-9, port="q0:res", clock="q0.ro")


def test_staircase_raises_not_multiple_of_grid_time():
    """Test that an error is raised if step duration is not a multiple of grid time."""
    with pytest.raises(ValueError) as err:
        _ = staircase_pulse(
            start_amp=0.1,
            final_amp=0.9,
            num_steps=20,
            duration=20 * 9e-9,
            min_operation_time_ns=4,
            port="q0:res",
            clock="q0.ro",
        )
    # Exact phrasing is not important, but should be about staircase
    assert "step" in str(err.value) and "staircase" in str(err.value)


def test_staircase_raises_step_duration_too_short():
    """Test that an error is raised if step duration is shorter than the grid time."""
    with pytest.raises(ValueError) as err:
        _ = staircase_pulse(
            start_amp=0.1,
            final_amp=0.9,
            num_steps=20,
            duration=20 * 4e-9,
            min_operation_time_ns=8,
            port="q0:res",
            clock="q0.ro",
        )
    # Exact phrasing is not important, but should be about staircase
    assert "step" in str(err.value) and "staircase" in str(err.value)


@pytest.mark.parametrize(
    "pulse",
    [
        partial(long_square_pulse, amp=0.8, duration=1e-3, port="q0:res", clock="q0.ro"),
        partial(
            staircase_pulse,
            start_amp=0.1,
            final_amp=0.9,
            num_steps=20,
            duration=1e-3,
            port="q0:res",
            clock="q0.ro",
        ),
        partial(long_ramp_pulse, amp=0.8, duration=1e-3, port="q0:res"),
    ],
)
def test_voltage_offset_operations_reference_magnitude(pulse):
    def collect_all_offsets_and_pulses(
        schedule_or_operation: TimeableSchedule | Operation,
    ) -> list[Operation]:
        if isinstance(schedule_or_operation, (SquarePulse, RampPulse, VoltageOffset)):
            return [schedule_or_operation]
        if isinstance(schedule_or_operation, LoopOperation):
            return collect_all_offsets_and_pulses(schedule_or_operation.body)
        if isinstance(schedule_or_operation, TimeableSchedule):
            return [
                pulse
                for operation in schedule_or_operation.operations.values()
                for pulse in collect_all_offsets_and_pulses(operation)
            ]
        return []

    reference_magnitude = ReferenceMagnitude(20, "dBm")

    pulse = pulse(reference_magnitude=reference_magnitude)
    operations = collect_all_offsets_and_pulses(pulse)
    assert len(operations) > 0

    for op in operations:
        assert op["pulse_info"]["reference_magnitude"] == reference_magnitude


def test_non_implemented_pulse():
    """Test that the non_implemented_pulse function raises NotImplementedError."""
    with pytest.raises(
        NotImplementedError, match="The gate or pulse you are trying to use is not implemented yet."
    ):
        non_implemented_pulse()


def test_long_chirp_pulse(assert_equal_q1asm):
    hw_config = QbloxHardwareCompilationConfig(
        config_type="QbloxHardwareCompilationConfig",
        hardware_description={
            "cluster": ClusterDescription(
                instrument_type="Cluster",
                ref="internal",
                modules={
                    2: QCMDescription(),
                },
            )
        },
        hardware_options=QbloxHardwareOptions(),
        connectivity={
            "graph": [
                ("cluster.module2.complex_output_0", "p:ort"),
            ]
        },
    )
    q_dev = QuantumDevice("qdev")
    q_dev.hardware_config = hw_config

    sched = TimeableSchedule()
    sched.add(
        long_chirp_pulse(
            amp=1.0,
            duration=6e-6,
            port="p:ort",
            clock="c.lock",
            start_freq=20e6,
            end_freq=120e6,
            part_duration_ns=2000,
        )
    )
    sched.add(IdlePulse(4e-9))
    sched.add_resource(ClockResource("c.lock", 1e6))

    compiler = SerialCompiler(name="compiler")
    compiled_schedule = compiler.compile(
        sched,
        config=q_dev.generate_compilation_config(),
    )
    assert_equal_q1asm(
        compiled_schedule.compiled_instructions["cluster"]["cluster_module2"]["sequencers"][
            "seq0"
        ].sequence["program"],
        """ set_mrk 0 # set markers to 0 (init)
 wait_sync 4
 upd_param 4
 wait 4 # latency correction of 4 + 0 ns
 move 1,R0 # iterator for loop with label start
start:
 reset_ph
 upd_param 4
 set_freq 80000000 # Update NCO frequency
 set_awg_gain 32767,-32768 # setting gain for ChirpPulse
 play 0,1,4 # play ChirpPulse (2000 ns)
 wait 1996 # auto generated wait (1996 ns)
 set_ph_delta 333333333 # increment nco phase by 120.00 deg
 set_freq 213333333 # Update NCO frequency
 set_awg_gain 32767,-32768 # setting gain for ChirpPulse
 play 0,1,4 # play ChirpPulse (2000 ns)
 wait 1996 # auto generated wait (1996 ns)
 set_ph_delta 333333333 # increment nco phase by 120.00 deg
 set_freq 346666667 # Update NCO frequency
 set_awg_gain 32767,-32768 # setting gain for ChirpPulse
 play 0,1,4 # play ChirpPulse (2000 ns)
 wait 1996 # auto generated wait (1996 ns)
 set_ph_delta 333333333 # increment nco phase by 120.00 deg
 set_freq 4000000 # Update NCO frequency
 upd_param 4
 loop R0,@start
 stop  """,
    )
    waveforms = compiled_schedule.compiled_instructions["cluster"]["cluster_module2"]["sequencers"][
        "seq0"
    ].sequence["waveforms"]
    assert len(waveforms) == 2
    for wf_dict in waveforms.values():
        assert len(wf_dict["data"]) == 2000
