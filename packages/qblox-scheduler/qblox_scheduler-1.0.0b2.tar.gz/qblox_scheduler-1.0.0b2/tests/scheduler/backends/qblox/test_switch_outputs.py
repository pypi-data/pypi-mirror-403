# Repository: https://gitlab.com/quantify-os/qblox-scheduler
# Licensed according to the LICENCE file on the main branch
#
# Copyright 2025, Qblox B.V.
"""Tests for Qblox backend RF output switching."""

import numpy as np
import pytest

from qblox_scheduler import SerialCompiler, TimeableSchedule
from qblox_scheduler.backends.qblox import constants
from qblox_scheduler.operations import IdlePulse, Reset, SquarePulse, X
from qblox_scheduler.operations.hardware_operations.pulse_library import RFSwitchToggle


class TestSwitchOutputs:
    def test_output_switch_single(self, compile_config_basic_transmon_qblox_hardware):
        # Set automatic RF switching to on
        hardware_config = compile_config_basic_transmon_qblox_hardware.hardware_compilation_config
        hardware_description = hardware_config.hardware_description["cluster0"]
        for module in hardware_description.modules.values():
            if module.instrument_type.endswith("RF"):
                module.rf_output_on = "auto"
        compiler = SerialCompiler(name="compiler")

        # Test basic case
        sched = TimeableSchedule("output switch")
        sched.add(Reset("q0"))
        sched.add(
            SquarePulse(
                amp=0.4,
                port="q0:mw",
                duration=20e-9,
                clock="q0.01",
                t0=4e-9,
            ),
            rel_time=100e-9,
        )
        sched.add(Reset("q0"))

        compiled = compiler.compile(sched, config=compile_config_basic_transmon_qblox_hardware)
        assert len(compiled.schedulables) == 4
        operations = {
            ident: compiled.operations[s.data["operation_id"]]
            for (ident, s) in compiled.schedulables.items()
        }

        # Find square pulse schedulable
        square_schedulable = next(
            compiled.schedulables[ident]
            for (ident, op) in operations.items()
            if isinstance(op, SquarePulse)
        )
        square_operation = compiled.operations[square_schedulable.data["operation_id"]]
        # Find inserted RF switch schedulable
        rf_switch_schedulable = next(
            compiled.schedulables[ident]
            for (ident, op) in operations.items()
            if isinstance(op, RFSwitchToggle)
        )
        rf_switch_operation = compiled.operations[rf_switch_schedulable.data["operation_id"]]

        # Verify properties
        np.testing.assert_allclose(
            rf_switch_schedulable["abs_time"],
            square_schedulable["abs_time"]
            + square_operation["pulse_info"]["t0"]
            - constants.RF_OUTPUT_RISE_TIME,
        )
        np.testing.assert_allclose(rf_switch_operation.data["pulse_info"]["t0"], 0.0)
        np.testing.assert_allclose(
            rf_switch_operation.data["pulse_info"]["duration"],
            square_operation.data["pulse_info"]["duration"] + constants.RF_OUTPUT_RISE_TIME,
        )

    def test_output_switch_merge(self, compile_config_basic_transmon_qblox_hardware):
        # Set automatic RF switching to on
        hardware_config = compile_config_basic_transmon_qblox_hardware.hardware_compilation_config
        hardware_description = hardware_config.hardware_description["cluster0"]
        for module in hardware_description.modules.values():
            if module.instrument_type.endswith("RF"):
                module.rf_output_on = "auto"
        compiler = SerialCompiler(name="compiler")

        # Test basic case
        sched = TimeableSchedule("output switch")
        sched.add(X("q0"), rel_time=100e-9)
        sched.add(X("q0"), rel_time=constants.RF_OUTPUT_GRACE_TIME)
        sched.add(IdlePulse(duration=100e-9))

        compiled = compiler.compile(sched, config=compile_config_basic_transmon_qblox_hardware)
        # Should be only one added operation!
        assert len(compiled.schedulables) == 4
        operations = {
            ident: compiled.operations[s.data["operation_id"]]
            for (ident, s) in compiled.schedulables.items()
        }

        # Find X schedulables
        x_schedulable = next(
            compiled.schedulables[ident] for (ident, op) in operations.items() if isinstance(op, X)
        )
        x2_schedulable = next(
            compiled.schedulables[ident]
            for (ident, op) in operations.items()
            if isinstance(op, X) and compiled.schedulables[ident] != x_schedulable
        )
        x2_operation = compiled.operations[x2_schedulable.data["operation_id"]]
        # Find inserted RF switch schedulable
        rf_switch_schedulable = next(
            compiled.schedulables[ident]
            for (ident, op) in operations.items()
            if isinstance(op, RFSwitchToggle)
        )
        rf_switch_operation = compiled.operations[rf_switch_schedulable.data["operation_id"]]

        # Verify properties
        np.testing.assert_allclose(
            rf_switch_schedulable["abs_time"],
            x_schedulable["abs_time"] - constants.RF_OUTPUT_RISE_TIME,
        )
        x2_end = x2_schedulable["abs_time"] + x2_operation.duration
        np.testing.assert_allclose(
            rf_switch_schedulable["abs_time"] + rf_switch_operation.duration, x2_end
        )

    def test_output_switch_no_merge(self, compile_config_basic_transmon_qblox_hardware):
        # Set automatic RF switching to on
        hardware_config = compile_config_basic_transmon_qblox_hardware.hardware_compilation_config
        hardware_description = hardware_config.hardware_description["cluster0"]
        for module in hardware_description.modules.values():
            if module.instrument_type.endswith("RF"):
                module.rf_output_on = "auto"
        compiler = SerialCompiler(name="compiler")

        # Test basic case
        sched = TimeableSchedule("output switch")
        sched.add(X("q0"), rel_time=100e-9)
        sched.add(X("q0"), rel_time=constants.RF_OUTPUT_GRACE_TIME + 50e-9)
        sched.add(IdlePulse(duration=100e-9))

        compiled = compiler.compile(sched, config=compile_config_basic_transmon_qblox_hardware)
        # Should be two added operations since merge failed!
        assert len(compiled.schedulables) == 5

    def test_output_switch_not_enough_front_room(
        self, compile_config_basic_transmon_qblox_hardware
    ):
        # Set automatic RF switching to on
        hardware_config = compile_config_basic_transmon_qblox_hardware.hardware_compilation_config
        hardware_description = hardware_config.hardware_description["cluster0"]
        for module in hardware_description.modules.values():
            if module.instrument_type.endswith("RF"):
                module.rf_output_on = "auto"
        compiler = SerialCompiler(name="compiler")

        # Test ValueError if there is not enough front room
        sched = TimeableSchedule("output switch")
        sched.add(
            SquarePulse(
                amp=0.4,
                port="q0:mw",
                duration=20e-9,
                clock="q0.01",
                t0=4e-9,
            ),
        )
        sched.add(Reset("q0"))
        with pytest.raises(RuntimeError):
            compiler.compile(sched, config=compile_config_basic_transmon_qblox_hardware)

    def test_output_switch_auto_insert_front(self, compile_config_basic_transmon_qblox_hardware):
        hardware_config = compile_config_basic_transmon_qblox_hardware.hardware_compilation_config
        # Set timing insertion to on
        compiler_options = hardware_config.compiler_options
        compiler_options.retime_allowed = True
        # Set automatic RF switching to on
        hardware_description = hardware_config.hardware_description["cluster0"]
        for module in hardware_description.modules.values():
            if module.instrument_type.endswith("RF"):
                module.rf_output_on = "auto"

        # Make sure something was inserted
        sched = TimeableSchedule("output switch")
        sched.add(
            SquarePulse(
                amp=0.4,
                port="q0:mw",
                duration=20e-9,
                clock="q0.01",
                t0=4e-9,
            ),
        )
        sched.add(Reset("q0"))

        compiler = SerialCompiler(name="compiler")
        compiled = compiler.compile(sched, config=compile_config_basic_transmon_qblox_hardware)

        # Should be only one added operation!
        assert len(compiled.schedulables) == 3
        operations = {
            ident: compiled.operations[s.data["operation_id"]]
            for (ident, s) in compiled.schedulables.items()
        }

        # Find SquarePulse schedulable
        sq_schedulable = next(
            compiled.schedulables[ident]
            for (ident, op) in operations.items()
            if isinstance(op, SquarePulse)
        )
        sq_operation = compiled.operations[sq_schedulable.data["operation_id"]]
        # Find reset schedulable
        reset_schedulable = next(
            compiled.schedulables[ident]
            for (ident, op) in operations.items()
            if isinstance(op, Reset)
        )
        # Find inserted RF switch schedulable
        rf_switch_schedulable = next(
            compiled.schedulables[ident]
            for (ident, op) in operations.items()
            if isinstance(op, RFSwitchToggle)
        )

        # Verify properties
        np.testing.assert_allclose(
            rf_switch_schedulable["abs_time"],
            0.0,
        )
        np.testing.assert_allclose(
            sq_schedulable["abs_time"] + sq_operation["pulse_info"]["t0"],
            rf_switch_schedulable["abs_time"] + constants.RF_OUTPUT_RISE_TIME,
        )
        np.testing.assert_allclose(
            reset_schedulable["abs_time"],
            sq_schedulable["abs_time"] + sq_operation.duration,
        )

    def test_output_switch_not_enough_back_room(self, compile_config_basic_transmon_qblox_hardware):
        # Set automatic RF switching to on
        hardware_config = compile_config_basic_transmon_qblox_hardware.hardware_compilation_config
        hardware_description = hardware_config.hardware_description["cluster0"]
        for module in hardware_description.modules.values():
            if module.instrument_type.endswith("RF"):
                module.rf_output_on = "auto"
        compiler = SerialCompiler(name="compiler")

        # Test ValueError if there is not enough back room
        sched = TimeableSchedule("output switch")
        sched.add(Reset("q0"))
        sched.add(
            SquarePulse(
                amp=0.4,
                port="q0:mw",
                duration=20e-9,
                clock="q0.01",
                t0=4e-9,
            ),
            rel_time=100e-9,
        )
        with pytest.raises(RuntimeError):
            compiler.compile(sched, config=compile_config_basic_transmon_qblox_hardware)

    def test_output_switch_auto_insert_back(self, compile_config_basic_transmon_qblox_hardware):
        hardware_config = compile_config_basic_transmon_qblox_hardware.hardware_compilation_config
        # Set timing insertion to on
        compiler_options = hardware_config.compiler_options
        compiler_options.retime_allowed = True
        # Set automatic RF switching to on
        hardware_description = hardware_config.hardware_description["cluster0"]
        for module in hardware_description.modules.values():
            if module.instrument_type.endswith("RF"):
                module.rf_output_on = "auto"

        # Make sure something was inserted
        sched = TimeableSchedule("output switch")
        sched.add(Reset("q0"))
        sched.add(
            SquarePulse(
                amp=0.4,
                port="q0:mw",
                duration=20e-9,
                clock="q0.01",
                t0=4e-9,
            ),
            rel_time=100e-9,
        )

        compiler = SerialCompiler(name="compiler")
        compiled = compiler.compile(sched, config=compile_config_basic_transmon_qblox_hardware)

        # Should be two added operations!
        assert len(compiled.schedulables) == 4
        operations = {
            ident: compiled.operations[s.data["operation_id"]]
            for (ident, s) in compiled.schedulables.items()
        }

        # Find SquarePulse schedulable
        sq_schedulable = next(
            compiled.schedulables[ident]
            for (ident, op) in operations.items()
            if isinstance(op, SquarePulse)
        )
        sq_operation = sched.operations[sq_schedulable.data["operation_id"]]
        # Find inserted idle pulse schedulable
        idle_schedulable = next(
            compiled.schedulables[ident]
            for (ident, op) in operations.items()
            if isinstance(op, IdlePulse)
        )
        # Find inserted RF switch schedulable
        rf_switch_schedulable = next(
            compiled.schedulables[ident]
            for (ident, op) in operations.items()
            if isinstance(op, RFSwitchToggle)
        )

        # Verify properties
        sq_start = sq_schedulable["abs_time"] + sq_operation["pulse_info"]["t0"]
        np.testing.assert_allclose(
            rf_switch_schedulable["abs_time"],
            sq_start - constants.RF_OUTPUT_RISE_TIME,
        )
        np.testing.assert_allclose(
            idle_schedulable["abs_time"],
            sq_start + sq_operation.duration,
        )
