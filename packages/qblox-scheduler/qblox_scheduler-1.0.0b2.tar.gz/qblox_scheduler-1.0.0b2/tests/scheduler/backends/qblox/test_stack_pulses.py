# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
"""Tests for Qblox backend pulse stacking."""

import numpy as np
import pytest

from qblox_scheduler import TimeableSchedule
from qblox_scheduler.backends import SerialCompiler
from qblox_scheduler.backends.qblox import constants, helpers
from qblox_scheduler.operations.pulse_library import GaussPulse, SquarePulse


class TestPulseStacking:
    def test_pulse_stacking_same_start_time(self, compile_config_basic_transmon_qblox_hardware):
        sched = TimeableSchedule("Pulse stacking")
        self.add = sched.add(SquarePulse(amp=0.5, duration=20e-9, port="q0:mw", clock="q0.01"))
        ref = self.add
        sched.add(
            SquarePulse(amp=0.3, duration=20e-9, port="q0:mw", clock="q0.01"),
            ref_op=ref,
            ref_pt="start",
        )
        compiler = SerialCompiler(name="compiler")
        compiled = compiler.compile(sched, compile_config_basic_transmon_qblox_hardware)
        assert len(compiled.schedulables) == 1
        operations = list(compiled.operations.values())
        assert operations[2].data["pulse_info"]["amp"] == 0.8

    def test_pulse_stacking_amp_exception(self, compile_config_basic_transmon_qblox_hardware):
        sched = TimeableSchedule("Pulse stacking")
        ref = sched.add(SquarePulse(amp=0.5, duration=20e-9, port="q0:mw", clock="q0.01"))
        sched.add(
            SquarePulse(amp=0.6, duration=20e-9, port="q0:mw", clock="q0.01"),
            ref_op=ref,
            ref_pt="start",
        )
        compiler = SerialCompiler(name="compiler")
        with pytest.raises(
            ValueError,
            match="Waveform amplitude exceeds maximum of 1",
        ):
            compiler.compile(sched, compile_config_basic_transmon_qblox_hardware)

    def test_pulse_stacking_different_start_time(
        self, compile_config_basic_transmon_qblox_hardware
    ):
        sched = TimeableSchedule("Pulse stacking")
        ref = sched.add(SquarePulse(amp=0.5, duration=20e-9, port="q0:mw", clock="q0.01"))
        sched.add(
            SquarePulse(amp=0.3, duration=20e-9, port="q0:mw", clock="q0.01", t0=12e-9),
            ref_op=ref,
            ref_pt="start",
        )
        compiler = SerialCompiler(name="compiler")
        compiled = compiler.compile(sched, compile_config_basic_transmon_qblox_hardware)
        assert len(compiled.schedulables) == 3
        schedulables = list(compiled.schedulables.values())
        operations = [compiled.operations[schedulables[i].data["operation_id"]] for i in range(3)]
        pulse0 = operations[0].data["pulse_info"]
        pulse1 = operations[1].data["pulse_info"]
        pulse2 = operations[2].data["pulse_info"]

        assert pulse0["amp"] == 0.5 and pulse0["duration"] == 12e-9
        assert (
            pulse1["amp"] == 0.8
            and pulse1["duration"] == 8e-9
            and schedulables[1].data["abs_time"] == 12e-9
        )
        assert (
            pulse2["amp"] == 0.3
            and pulse2["duration"] == 12e-9
            and schedulables[2].data["abs_time"] == 20e-9
        )

    def test_pulse_stacking_nested(self, compile_config_basic_transmon_qblox_hardware):
        sched = TimeableSchedule("Pulse stacking")
        ref = sched.add(SquarePulse(amp=0.5, duration=40e-9, port="q0:mw", clock="q0.01"))
        sched.add(
            SquarePulse(amp=0.3, duration=24e-9, port="q0:mw", clock="q0.01", t0=12e-9),
            ref_op=ref,
            ref_pt="start",
        )
        sched.add(
            SquarePulse(amp=0.1, duration=10e-9, port="q0:mw", clock="q0.01", t0=22e-9),
            ref_op=ref,
            ref_pt="start",
        )
        compiler = SerialCompiler(name="compiler")
        compiled = compiler.compile(sched, compile_config_basic_transmon_qblox_hardware)
        assert len(compiled.schedulables) == 5
        schedulables = list(compiled.schedulables.values())
        expected_amplitudes = [0.5, 0.8, 0.9, 0.8, 0.5]
        for i, expected_amp in enumerate(expected_amplitudes):
            operation = compiled.operations[schedulables[i].data["operation_id"]]
            assert round(operation.data["pulse_info"]["amp"], 3) == expected_amp

    def test_pulse_stacking_gauss(self, compile_config_basic_transmon_qblox_hardware):
        sched = TimeableSchedule("Pulse stacking")
        gauss = GaussPulse(
            amplitude=0.5,
            phase=0,
            port="q0:fl",
            duration=40e-9,
            clock="q0.01",
            t0=4e-9,
        )
        square = SquarePulse(amp=0.2, duration=10e-9, port="q0:fl", clock="q0.01", t0=19e-9)
        ref = sched.add(gauss)
        sched.add(
            square,
            ref_op=ref,
            ref_pt="start",
        )
        gauss_waveform = helpers.generate_waveform_data(
            gauss.data["pulse_info"], sampling_rate=constants.SAMPLING_RATE
        )
        square_waveform = helpers.generate_waveform_data(
            square.data["pulse_info"], sampling_rate=constants.SAMPLING_RATE
        )
        gauss_waveform[15:25] += square_waveform
        compiler = SerialCompiler(name="compiler")
        compiled = compiler.compile(sched, compile_config_basic_transmon_qblox_hardware)

        assert len(compiled.schedulables) == 3
        schedulables = list(compiled.schedulables.values())
        operations = [compiled.operations[schedulables[i].data["operation_id"]] for i in range(3)]
        total_waveform = np.array([])
        for operation in operations:
            waveform = helpers.generate_waveform_data(
                operation.data["pulse_info"], sampling_rate=constants.SAMPLING_RATE
            )
            total_waveform = np.append(total_waveform, waveform)
        assert np.allclose(total_waveform, gauss_waveform)
