# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
import numpy as np
import pytest

from qblox_scheduler import SerialCompiler, TimeableSchedule
from qblox_scheduler.backends.qblox.type_casting import (
    _cast_amplitude_to_signed_int,
    _cast_hz_to_signed_int,
)
from qblox_scheduler.enums import BinMode
from qblox_scheduler.operations import (
    IdlePulse,
    Measure,
    NumericalPulse,
    SetClockFrequency,
    ShiftClockPhase,
    SquarePulse,
)
from qblox_scheduler.operations.expressions import DType
from qblox_scheduler.operations.gate_library import X
from qblox_scheduler.operations.loop_domains import linspace
from qblox_scheduler.operations.shared_native_library import SpectroscopyOperation
from qblox_scheduler.resources import ClockResource


@pytest.mark.parametrize("start_amp", (0, -1.0, -0.5))
def test_1d_square_pulse_amp_sweep(
    mock_setup_basic_transmon_with_standard_params,
    qblox_hardware_config_transmon,
    assert_equal_q1asm,
    start_amp,
):
    sched = TimeableSchedule()
    with sched.loop(linspace(start_amp, start_amp + 1.0, 11, dtype=DType.AMPLITUDE)) as amp:
        sched.add(SquarePulse(amp=amp, duration=100e-9, port="q0:mw", clock="q0.01"))

    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    quantum_device.hardware_config = qblox_hardware_config_transmon

    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        sched,
        config=quantum_device.generate_compilation_config(),
    )

    start = _cast_amplitude_to_signed_int(start_amp)
    if start < 0:
        start = (1 << 32) + start
    step = (1 << 31) // 10
    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module2"]["sequencers"][
            "seq0"
        ].sequence["program"],
        f"""
 set_mrk 1 # set markers to 1 (init)
 wait_sync 4
 upd_param 4
 wait 4 # latency correction of 4 + 0 ns
 move 1,R0 # iterator for loop with label start
start:
 reset_ph
 upd_param 4
 move {start},R2 # Initialize sweep var
 move 11,R1 # iterator for loop with label loop8
loop8:
 asr R2,16,R3
 move 0,R4
 nop
 set_awg_offs R3,R4 # setting offset for SquarePulse
 upd_param 4
 wait 92 # auto generated wait (92 ns)
 set_awg_offs 0,0 # setting offset for SquarePulse
 asr R2,16,R4
 move 0,R3
 nop
 set_awg_gain R4,R3 # setting gain for SquarePulse
 play 0,0,4 # play SquarePulse (4 ns)
 add R2,{step},R2 # Update sweep var
 loop R1,@loop8
 loop R0,@start
 stop
""",
    )


@pytest.mark.parametrize("start_amp", (0, 1.0, 0.5))
def test_1d_square_pulse_amp_sweep_down(
    mock_setup_basic_transmon_with_standard_params,
    qblox_hardware_config_transmon,
    assert_equal_q1asm,
    start_amp,
):
    sched = TimeableSchedule()
    with sched.loop(linspace(start_amp, start_amp - 1.0, 11, dtype=DType.AMPLITUDE)) as amp:
        sched.add(SquarePulse(amp=amp, duration=100e-9, port="q0:mw", clock="q0.01"))

    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    quantum_device.hardware_config = qblox_hardware_config_transmon

    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        sched,
        config=quantum_device.generate_compilation_config(),
    )

    start = _cast_amplitude_to_signed_int(start_amp)
    step = (1 << 31) // 10
    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module2"]["sequencers"][
            "seq0"
        ].sequence["program"],
        f"""
 set_mrk 1 # set markers to 1 (init)
 wait_sync 4
 upd_param 4
 wait 4 # latency correction of 4 + 0 ns
 move 1,R0 # iterator for loop with label start
start:
 reset_ph
 upd_param 4
 move {start},R2 # Initialize sweep var
 move 11,R1 # iterator for loop with label loop8
loop8:
 asr R2,16,R3
 move 0,R4
 nop
 set_awg_offs R3,R4 # setting offset for SquarePulse
 upd_param 4
 wait 92 # auto generated wait (92 ns)
 set_awg_offs 0,0 # setting offset for SquarePulse
 asr R2,16,R4
 move 0,R3
 nop
 set_awg_gain R4,R3 # setting gain for SquarePulse
 play 0,0,4 # play SquarePulse (4 ns)
 sub R2,{step},R2 # Update sweep var
 loop R1,@loop8
 loop R0,@start
 stop
""",
    )


def test_1d_square_pulse_complex_amp_sweep(
    mock_setup_basic_transmon_with_standard_params,
    qblox_hardware_config_transmon,
    assert_equal_q1asm,
):
    sched = TimeableSchedule()
    with sched.loop(
        linspace(0, 1.0, 11, dtype=DType.AMPLITUDE), linspace(0, -1.0, 11, dtype=DType.AMPLITUDE)
    ) as amp:
        sched.add(SquarePulse(amp=amp, duration=100e-9, port="q0:mw", clock="q0.01"))

    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    quantum_device.hardware_config = qblox_hardware_config_transmon

    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        sched,
        config=quantum_device.generate_compilation_config(),
    )

    start = 0
    step = (1 << 31) // 10
    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module2"]["sequencers"][
            "seq0"
        ].sequence["program"],
        f"""
 set_mrk 1 # set markers to 1 (init)
 wait_sync 4
 upd_param 4
 wait 4 # latency correction of 4 + 0 ns
 move 1,R0 # iterator for loop with label start
start:
 reset_ph
 upd_param 4
 move {start},R2 # Initialize sweep var
 move {start},R3 # Initialize sweep var
 move 11,R1 # iterator for loop with label loop8
loop8:
 asr R2,16,R4
 asr R3,16,R5
 nop
 set_awg_offs R4,R5 # setting offset for SquarePulse
 upd_param 4
 wait 92 # auto generated wait (92 ns)
 set_awg_offs 0,0 # setting offset for SquarePulse
 asr R2,16,R5
 asr R3,16,R4
 nop
 set_awg_gain R5,R4 # setting gain for SquarePulse
 play 0,0,4 # play SquarePulse (4 ns)
 add R2,{step},R2 # Update sweep var
 sub R3,{step},R3 # Update sweep var
 loop R1,@loop8
 loop R0,@start
 stop
""",
    )


def test_1d_square_pulse_amp_sweep_zip(
    mock_setup_basic_transmon_with_standard_params,
    qblox_hardware_config_transmon,
    assert_equal_q1asm,
):
    sched = TimeableSchedule()
    with sched.loop(
        linspace(0, 1.0, 11, dtype=DType.AMPLITUDE), linspace(0.0, 1.0, 11, dtype=DType.AMPLITUDE)
    ) as (amp1, amp2):
        sched.add(SquarePulse(amp=amp1, duration=100e-9, port="q0:mw", clock="q0.01"))
        sched.add(SquarePulse(amp=(0, amp2), duration=100e-9, port="q0:mw", clock="q0.01"))

    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    quantum_device.hardware_config = qblox_hardware_config_transmon

    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        sched,
        config=quantum_device.generate_compilation_config(),
    )

    start = 0
    step = (1 << 31) // 10
    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module2"]["sequencers"][
            "seq0"
        ].sequence["program"],
        f"""
     set_mrk 1 # set markers to 1 (init)
     wait_sync 4
     upd_param 4
     wait 4 # latency correction of 4 + 0 ns
     move 1,R0 # iterator for loop with label start
    start:
     reset_ph
     upd_param 4
     move {start},R2 # Initialize sweep var
     move {start},R3 # Initialize sweep var
     move 11,R1 # iterator for loop with label loop8
    loop8:
     asr R2,16,R4
     move 0,R5
     nop
     set_awg_offs R4,R5 # setting offset for SquarePulse
     upd_param 4
     wait 92 # auto generated wait (92 ns)
     set_awg_offs 0,0 # setting offset for SquarePulse
     asr R2,16,R5
     move 0,R4
     nop
     set_awg_gain R5,R4 # setting gain for SquarePulse
     play 0,0,4 # play SquarePulse (4 ns)
     move 0,R4
     asr R3,16,R5
     nop
     set_awg_offs R4,R5 # setting offset for SquarePulse
     upd_param 4
     wait 92 # auto generated wait (92 ns)
     set_awg_offs 0,0 # setting offset for SquarePulse
     move 0,R5
     asr R3,16,R4
     nop
     set_awg_gain R5,R4 # setting gain for SquarePulse
     play 0,0,4 # play SquarePulse (4 ns)
     add R2,{step},R2 # Update sweep var
     add R3,{step},R3 # Update sweep var
     loop R1,@loop8
     loop R0,@start
     stop
    """,
    )


def test_frequency_sweeps(mock_setup_basic_nv_qblox_hardware, assert_equal_q1asm):
    device_element = "qe0"
    spec_clock = "qe0.spec"

    sched = TimeableSchedule()

    with sched.loop(linspace(1.988e9, 2.198e9, 10, dtype=DType.FREQUENCY)) as spec_freq:
        sched.add(SetClockFrequency(clock=spec_clock, clock_freq_new=spec_freq))
        sched.add(SpectroscopyOperation(device_element), label="Spectroscopy")
        sched.add(Measure(device_element, bin_mode=BinMode.APPEND))

    quantum_device = mock_setup_basic_nv_qblox_hardware["quantum_device"]
    compiler = SerialCompiler(name="compiler")

    compiled_sched = compiler.compile(
        schedule=sched,
        config=quantum_device.generate_compilation_config(),
    )

    start = _cast_hz_to_signed_int(-12e6)
    start_twos_comp = (1 << 32) + start
    stop = _cast_hz_to_signed_int(198e6)
    step = (stop - start) // 9
    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module1"]["sequencers"][
            "seq0"
        ].sequence["program"],
        f"""
 set_mrk 1 # set markers to 1 (init)
 wait_sync 4
 upd_param 4
 wait 4 # latency correction of 4 + 0 ns
 move 1,R0 # iterator for loop with label start
start:
 reset_ph
 upd_param 4
 move {start_twos_comp},R2 # Initialize sweep var
 move 10,R1 # iterator for loop with label loop8
loop8:
 set_freq R2 # Update NCO frequency
 set_awg_offs 33,0 # setting offset for Spectroscopy operation qe0
 upd_param 4
 wait 7992 # auto generated wait (7992 ns)
 set_awg_offs 0,0 # setting offset for Spectroscopy operation qe0
 set_awg_gain 33,0 # setting gain for Spectroscopy operation qe0
 play 0,0,4 # play Spectroscopy operation qe0 (4 ns)
 wait 50000 # auto generated wait (50000 ns)
 add R2,{step},R2 # Update sweep var
 loop R1,@loop8
 loop R0,@start
 stop
""",
    )


def test_frequency_sweeps_gate_level(
    compile_config_basic_transmon_qblox_hardware, assert_equal_q1asm
):
    device_element = "q0"

    sched = TimeableSchedule()

    with sched.loop(linspace(8.2e9, 7.4e9, 10, dtype=DType.FREQUENCY)) as spec_freq:
        sched.add(Measure(device_element, bin_mode=BinMode.APPEND, freq=spec_freq))
        sched.add(IdlePulse(4e-9))

    compiler = SerialCompiler(name="compiler")

    compiled_sched = compiler.compile(
        schedule=sched,
        config=compile_config_basic_transmon_qblox_hardware,
    )

    start = _cast_hz_to_signed_int(400e6)
    stop = _cast_hz_to_signed_int(-400e6)
    step = (start - stop) // 9
    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module4"]["sequencers"][
            "seq0"
        ].sequence["program"],
        f"""
 set_mrk 2 # set markers to 2 (init)
 wait_sync 4
 upd_param 4
 move 0,R0 # Initialize acquisition bin_idx for ch0
 wait 4 # latency correction of 4 + 0 ns
 move 1,R1 # iterator for loop with label start
start:
 reset_ph
 upd_param 4
 move {start},R3 # Initialize sweep var
 move 10,R2 # iterator for loop with label loop9
loop9:
 set_freq R3 # Update NCO frequency
 reset_ph
 set_awg_gain 8192,0 # setting gain for SquarePulse
 play 0,0,4 # play SquarePulse (50 ns)
 wait 96 # auto generated wait (96 ns)

 acquire 0,R0,4
 add R0,1,R0 # Increment bin_idx for ch0

 wait 996 # auto generated wait (996 ns)
 set_freq 800000000 # Update NCO frequency
 upd_param 4
 sub R3,{step},R3 # Update sweep var
 loop R2,@loop9
 loop R1,@start
 stop
""",
    )


def test_phase_sweeps(mock_setup_basic_nv_qblox_hardware, assert_equal_q1asm):
    device_element = "qe0"
    spec_clock = "qe0.spec"

    sched = TimeableSchedule()

    with sched.loop(linspace(45, 270, 9, dtype=DType.PHASE)) as spec_phase:
        sched.add(ShiftClockPhase(clock=spec_clock, phase_shift=spec_phase))
        sched.add(SpectroscopyOperation(device_element), label="Spectroscopy")
        sched.add(Measure(device_element, bin_mode=BinMode.APPEND))

    quantum_device = mock_setup_basic_nv_qblox_hardware["quantum_device"]
    compiler = SerialCompiler(name="compiler")

    compiled_sched = compiler.compile(
        schedule=sched,
        config=quantum_device.generate_compilation_config(),
    )

    start = round(45 * 1e9 / 360)
    stop = round(270 * 1e9 / 360)
    step = (stop - start) // 8
    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module1"]["sequencers"][
            "seq0"
        ].sequence["program"],
        f"""
 set_mrk 1 # set markers to 1 (init)
 wait_sync 4
 upd_param 4
 wait 4 # latency correction of 4 + 0 ns
 move 1,R0 # iterator for loop with label start
start:
 reset_ph
 upd_param 4
 move {start},R2 # Initialize sweep var
 move 9,R1 # iterator for loop with label loop8
loop8:
 set_ph_delta R2 # increment nco phase
 set_awg_offs 33,0 # setting offset for VoltageOffset
 upd_param 4
 wait 7992 # auto generated wait (7992 ns)
 set_awg_offs 0,0 # setting offset for VoltageOffset
 set_awg_gain 33,0 # setting gain for SquarePulse
 play 0,0,4 # play SquarePulse (4 ns)
 wait 50000 # auto generated wait (50000 ns)
 add R2,{step},R2
 loop R1,@loop8
 loop R0,@start
 stop
""",
    )


def test_unrolled_1d_pulse_and_gate_rel_time_sweep(
    mock_setup_basic_transmon_with_standard_params,
    qblox_hardware_config_transmon,
    assert_equal_q1asm,
):
    start = 20
    step = 20
    num = 3
    stop = start + step * (num - 1)
    xdur = 20
    domain = linspace(start / 1e9, stop / 1e9, num, dtype=DType.TIME)

    sched = TimeableSchedule(repetitions=3)
    sched.add_resource(ClockResource(name="q0.ro", freq=8000000000.0))

    with sched.loop(domain) as tau:
        sched.add(SquarePulse(amp=1.0, duration=40e-9, port="q0:mw", clock="q0.01"), rel_time=tau)
        sched.add(X("q0"))

    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    quantum_device.hardware_config = qblox_hardware_config_transmon

    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        sched,
        config=quantum_device.generate_compilation_config(),
    )

    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module2"]["sequencers"][
            "seq0"
        ].sequence["program"],
        f"""
 set_mrk 1 # set markers to 1 (init)
 wait_sync 4
 upd_param 4
 wait 4 # latency correction of 4 + 0 ns
 move 3,R0 # iterator for loop with label start
start:
 reset_ph
 upd_param 4
 wait {start + 0 * step} # auto generated wait ({start + 0 * step} ns)
 set_awg_gain 32767,0 # setting gain for SquarePulse
 play 0,0,4 # play SquarePulse (40 ns)
 wait 36 # auto generated wait (36 ns)
 set_awg_gain 3765,221 # setting gain for X q0
 play 1,2,4 # play X q0 (20 ns)
 wait {start + 1 * step + (xdur - 4)} # auto generated wait ({start + 1 * step + (xdur - 4)} ns)
 set_awg_gain 32767,0 # setting gain for SquarePulse
 play 0,0,4 # play SquarePulse (40 ns)
 wait 36 # auto generated wait (36 ns)
 set_awg_gain 3765,221 # setting gain for X q0
 play 1,2,4 # play X q0 (20 ns)
 wait {start + 2 * step + (xdur - 4)} # auto generated wait ({start + 2 * step + (xdur - 4)} ns)
 set_awg_gain 32767,0 # setting gain for SquarePulse
 play 0,0,4 # play SquarePulse (40 ns)
 wait 36 # auto generated wait (36 ns)
 set_awg_gain 3765,221 # setting gain for X q0
 play 1,2,4 # play X q0 (20 ns)
 wait 16 # auto generated wait (16 ns)
 loop R0,@start
 stop
""",
    )


@pytest.mark.parametrize("start_amp, stop_amp", ((-1.1, 0.5), (-0.5, 1.1)))
def test_invalid_sweep_range_amplitude(
    mock_setup_basic_transmon_with_standard_params,
    qblox_hardware_config_transmon,
    start_amp,
    stop_amp,
):
    schedule = TimeableSchedule()
    with schedule.loop(linspace(start_amp, stop_amp, 11, dtype=DType.AMPLITUDE)) as amp:
        schedule.add(SquarePulse(amp=amp, duration=100e-9, port="q0:mw", clock="q0.01"))

    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    quantum_device.hardware_config = qblox_hardware_config_transmon

    compiler = SerialCompiler(name="compiler")

    with pytest.raises(ValueError, match=r"Amplitude must be in the range \[-1\.0, 1\.0\]\."):
        compiler.compile(
            schedule,
            config=quantum_device.generate_compilation_config(),
        )


@pytest.mark.parametrize("start_phase, stop_phase", ((-0.1, 90), (90, 360.1)))
def test_invalid_sweep_range_phase(
    mock_setup_basic_transmon_with_standard_params,
    qblox_hardware_config_transmon,
    start_phase,
    stop_phase,
):
    schedule = TimeableSchedule()
    with schedule.loop(linspace(start_phase, stop_phase, 11, dtype=DType.PHASE)) as spec_phase:
        schedule.add(ShiftClockPhase(clock="q0.01", phase_shift=spec_phase))
        schedule.add(SquarePulse(amp=0.1, duration=100e-9, port="q0:mw", clock="q0.01"))

    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    quantum_device.hardware_config = qblox_hardware_config_transmon

    compiler = SerialCompiler(name="compiler")

    with pytest.raises(ValueError, match=r"Phase must be in the range \[0\.0, 360\.0\]\."):
        compiler.compile(
            schedule,
            config=quantum_device.generate_compilation_config(),
        )


def test_numerical_pulse_amplitude_sweep(
    mock_setup_basic_transmon_with_standard_params,
    qblox_hardware_config_transmon,
    assert_equal_q1asm,
):
    start_gain = -0.5
    t_samples = np.linspace(0, 200e-9, 200)
    signal = t_samples / 200e-9
    sched = TimeableSchedule()
    with sched.loop(linspace(start_gain, start_gain + 1.0, 11, dtype=DType.AMPLITUDE)) as gain:
        sched.add(
            NumericalPulse(
                gain=gain, samples=signal, t_samples=t_samples, port="q0:mw", clock="q0.01"
            )
        )

    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    quantum_device.hardware_config = qblox_hardware_config_transmon

    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        sched,
        config=quantum_device.generate_compilation_config(),
    )

    start = _cast_amplitude_to_signed_int(start_gain)
    if start < 0:
        start = (1 << 32) + start
    step = (1 << 31) // 10
    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module2"]["sequencers"][
            "seq0"
        ].sequence["program"],
        f"""
 set_mrk 1 # set markers to 1 (init)
 wait_sync 4
 upd_param 4
 wait 4 # latency correction of 4 + 0 ns
 move 1,R0 # iterator for loop with label start
start:
 reset_ph
 upd_param 4
 move {start},R2 # Initialize sweep var
 move 11,R1 # iterator for loop with label loop8
loop8:
 asr R2,16,R3
 move 0,R4
 nop
 set_awg_gain R3,R4 # setting gain for NumericalPulse
 play 0,0,4 # play NumericalPulse (200 ns)
 wait 196 # auto generated wait (196 ns)
 add R2,{step},R2
 loop R1,@loop8
 loop R0,@start
 stop
""",
    )

    waveforms = compiled_sched.compiled_instructions["cluster0"]["cluster0_module2"]["sequencers"][
        "seq0"
    ].sequence["waveforms"]
    wf_dict = next(iter(waveforms.values()))
    waveform = wf_dict["data"]
    # NumericalPulse is implemented in a bit of a weird way: the number of samples stays the same,
    # but the waveform is "resampled" at the start of each nanosecond.
    assert np.allclose(waveform, signal * 199 / 200)
