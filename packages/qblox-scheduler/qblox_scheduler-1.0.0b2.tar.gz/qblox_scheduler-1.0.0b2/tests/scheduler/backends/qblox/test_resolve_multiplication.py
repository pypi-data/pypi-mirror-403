from qblox_scheduler import SerialCompiler, TimeableSchedule
from qblox_scheduler.operations import X90, DRAGPulse, X
from qblox_scheduler.operations.expressions import DType
from qblox_scheduler.operations.loop_domains import linspace


def test_resolve_multiplication_rxy_gate(
    mock_setup_basic_transmon_with_standard_params,
    qblox_hardware_config_transmon,
    assert_equal_q1asm,
):
    sched = TimeableSchedule()

    with sched.loop(linspace(0, 1, 101, DType.AMPLITUDE)) as amp:
        sched.add(X("q0", amp180=amp))

    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]
    quantum_device.hardware_config = qblox_hardware_config_transmon
    compiled_sched = SerialCompiler().compile(
        sched, config=quantum_device.generate_compilation_config()
    )

    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module2"]["sequencers"][
            "seq0"
        ].sequence["program"],
        """ set_mrk 1 # set markers to 1 (init)
 wait_sync 4
 upd_param 4
 wait 4 # latency correction of 4 + 0 ns
 move 1,R0 # iterator for loop with label start
start:
 reset_ph
 upd_param 4
 move 0,R2 # Initialize sweep var
 move 101,R1 # iterator for loop with label loop8
loop8:
 asr R2,16,R3
 nop
 set_awg_gain R3,R3 # setting gain for X q0
 play 0,1,4 # play X q0 (20 ns)
 wait 16 # auto generated wait (16 ns)
 add R2,21474836,R2 # Update sweep var
 loop R1,@loop8
 loop R0,@start
 stop
""",
    )


def test_resolve_multiplication_pulse_level(
    mock_setup_basic_transmon_with_standard_params,
    qblox_hardware_config_transmon,
    assert_equal_q1asm,
):
    sched = TimeableSchedule()

    with sched.loop(linspace(0, 1, 101, DType.AMPLITUDE)) as amp:
        sched.add(
            DRAGPulse(
                amplitude=0.5 * amp * 360 / 180,
                beta=1e-9,
                phase=0,
                duration=20e-9,
                port="q0:mw",
                clock="q0.01",
            )
        )

    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]
    quantum_device.hardware_config = qblox_hardware_config_transmon
    compiled_sched = SerialCompiler().compile(
        sched, config=quantum_device.generate_compilation_config()
    )

    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module2"]["sequencers"][
            "seq0"
        ].sequence["program"],
        """ set_mrk 1 # set markers to 1 (init)
 wait_sync 4
 upd_param 4
 wait 4 # latency correction of 4 + 0 ns
 move 1,R0 # iterator for loop with label start
start:
 reset_ph
 upd_param 4
 move 0,R2 # Initialize sweep var
 move 101,R1 # iterator for loop with label loop8
loop8:
 asr R2,16,R3
 nop
 set_awg_gain R3,R3 # setting gain for X q0
 play 0,1,4 # play X q0 (20 ns)
 wait 16 # auto generated wait (16 ns)
 add R2,21474836,R2 # Update sweep var
 loop R1,@loop8
 loop R0,@start
 stop
""",
    )


def test_resolve_multiplication_nested(
    mock_setup_basic_transmon_with_standard_params,
    qblox_hardware_config_transmon,
    assert_equal_q1asm,
):
    sched = TimeableSchedule()

    with (
        sched.loop(linspace(0, 1, 101, DType.AMPLITUDE)) as amp1,
        sched.loop(linspace(1, 0, 101, DType.AMPLITUDE)) as amp2,
    ):
        sched.add(X("q0", amp180=amp1))
        sched.add(X90("q0", amp180=amp2))

    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]
    quantum_device.hardware_config = qblox_hardware_config_transmon
    compiled_sched = SerialCompiler().compile(
        sched, config=quantum_device.generate_compilation_config()
    )

    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module2"]["sequencers"][
            "seq0"
        ].sequence["program"],
        """ set_mrk 1 # set markers to 1 (init)
 wait_sync 4
 upd_param 4
 wait 4 # latency correction of 4 + 0 ns
 move 1,R0 # iterator for loop with label start
start:
 reset_ph
 upd_param 4
 move 0,R2 # Initialize sweep var
 move 101,R1 # iterator for loop with label loop8
loop8:
 move 2147483647,R4 # Initialize sweep var
 move 101,R3 # iterator for loop with label loop11
loop11:
 asr R2,16,R5
 nop
 set_awg_gain R5,R5 # setting gain for X q0
 play 0,1,4 # play X q0 (20 ns)
 wait 16 # auto generated wait (16 ns)
 asr R4,16,R5
 nop
 set_awg_gain R5,R5 # setting gain for X_90 q0
 play 2,3,4 # play X_90 q0 (20 ns)
 wait 16 # auto generated wait (16 ns)
 sub R4,21474836,R4 # Update sweep var
 loop R3,@loop11
 add R2,21474836,R2 # Update sweep var
 loop R1,@loop8
 loop R0,@start
 stop
""",
    )


def test_resolve_multiple_scaling(
    mock_setup_basic_transmon_with_standard_params,
    qblox_hardware_config_transmon,
    assert_equal_q1asm,
):
    sched = TimeableSchedule()

    with sched.loop(linspace(0, 1, 101, DType.AMPLITUDE)) as amp:
        sched.add(X("q0", amp180=amp))
        sched.add(X90("q0", amp180=amp))

    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]
    quantum_device.hardware_config = qblox_hardware_config_transmon
    compiled_sched = SerialCompiler().compile(
        sched, config=quantum_device.generate_compilation_config()
    )

    waveforms = compiled_sched.compiled_instructions["cluster0"]["cluster0_module2"]["sequencers"][
        "seq0"
    ].sequence["waveforms"]
    wf_by_idx = {wf["index"]: wf["data"] for wf in waveforms.values()}
    assert max(wf_by_idx[0]) == 2 * max(wf_by_idx[2])
    assert max(wf_by_idx[1]) == 2 * max(wf_by_idx[3])

    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module2"]["sequencers"][
            "seq0"
        ].sequence["program"],
        """ set_mrk 1 # set markers to 1 (init)
 wait_sync 4
 upd_param 4
 wait 4 # latency correction of 4 + 0 ns
 move 1,R0 # iterator for loop with label start
start:
 reset_ph
 upd_param 4
 move 0,R2 # Initialize sweep var
 move 101,R1 # iterator for loop with label loop8
loop8:
 asr R2,16,R3
 nop
 set_awg_gain R3,R3 # setting gain for X q0
 play 0,1,4 # play X q0 (20 ns)
 wait 16 # auto generated wait (16 ns)
 asr R2,16,R3
 nop
 set_awg_gain R3,R3 # setting gain for X_90 q0
 play 2,3,4 # play X_90 q0 (20 ns)
 wait 16 # auto generated wait (16 ns)
 add R2,21474836,R2 # Update sweep var
 loop R1,@loop8
 loop R0,@start
 stop
""",
    )
