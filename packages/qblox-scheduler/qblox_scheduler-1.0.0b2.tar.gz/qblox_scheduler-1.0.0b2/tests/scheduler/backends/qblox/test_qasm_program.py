# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
"""Tests for the QASM program"""

import pytest

from qblox_scheduler.backends.qblox import constants, q1asm_instructions
from qblox_scheduler.backends.qblox.qasm_program import (
    QASMProgram,
    expand_awg_from_normalised_range,
)
from qblox_scheduler.backends.types.qblox import OpInfo
from qblox_scheduler.operations.expressions import DType
from qblox_scheduler.operations.loop_domains import LinearDomain
from qblox_scheduler.operations.variables import Variable


def test_emit(empty_qasm_program_qcm):
    qasm = empty_qasm_program_qcm
    qasm.emit(q1asm_instructions.PLAY, 0, 1, 120)
    qasm.emit(q1asm_instructions.STOP, comment="This is a comment that is added")

    assert len(qasm.instructions) == 2


def test_auto_wait(empty_qasm_program_qcm):
    qasm = empty_qasm_program_qcm
    qasm.auto_wait(120)
    assert len(qasm.instructions) == 1
    qasm.auto_wait(70000)
    assert len(qasm.instructions) == 3  # since it should split the waits
    assert qasm.elapsed_time == 70120
    qasm.auto_wait(700000)
    assert qasm.elapsed_time == 770120
    assert len(qasm.instructions) == 8  # now loops are used
    with pytest.raises(ValueError):
        qasm.auto_wait(-120)
    with pytest.raises(ValueError):
        qasm.auto_wait(constants.MIN_TIME_BETWEEN_OPERATIONS - 1)
        print(qasm.instructions)


def test_auto_wait_zero(empty_qasm_program_qcm):
    empty_qasm_program_qcm.auto_wait(0)
    assert len(empty_qasm_program_qcm.instructions) == 0
    assert empty_qasm_program_qcm.elapsed_time == 0


def test_auto_wait_max_imm(empty_qasm_program_qcm):
    empty_qasm_program_qcm.auto_wait(constants.IMMEDIATE_MAX_WAIT_TIME)
    assert len(empty_qasm_program_qcm.instructions) == 1
    assert empty_qasm_program_qcm.instructions[0][2] == str(constants.IMMEDIATE_MAX_WAIT_TIME)


def test_auto_wait_max_imm_plus_one(empty_qasm_program_qcm):
    empty_qasm_program_qcm.auto_wait(constants.IMMEDIATE_MAX_WAIT_TIME + 1)
    assert len(empty_qasm_program_qcm.instructions) == 2
    assert empty_qasm_program_qcm.instructions[0][2] == str(constants.IMMEDIATE_MAX_WAIT_TIME - 3)
    assert empty_qasm_program_qcm.instructions[1][2] == "4"


def test_auto_wait_loop(empty_qasm_program_qcm):
    empty_qasm_program_qcm.auto_wait(5 * constants.IMMEDIATE_MAX_WAIT_TIME + 1)
    assert len(empty_qasm_program_qcm.instructions) == 5
    assert empty_qasm_program_qcm.instructions[2][2] == str(constants.IMMEDIATE_MAX_WAIT_TIME - 1)
    assert empty_qasm_program_qcm.instructions[4][2] == "6"


@pytest.mark.parametrize(
    "val, expected_expanded_val",
    [
        (-1, -constants.IMMEDIATE_SZ_GAIN // 2),
        (-0.5, -constants.IMMEDIATE_SZ_GAIN // 4),
        (0.0, 0),
        (0.5, constants.IMMEDIATE_SZ_GAIN // 4),
        (1.0, constants.IMMEDIATE_SZ_GAIN // 2 - 1),
    ],
)
def test_expand_awg_gain_from_normalised_range(val, expected_expanded_val):
    minimal_pulse_data = {"duration": 20e-9}
    acq = OpInfo(name="test_acq", data=minimal_pulse_data, timing=4e-9)

    expanded_val = expand_awg_from_normalised_range(
        val=val,
        immediate_size=constants.IMMEDIATE_SZ_GAIN,
        param="test_param",
        operation=acq,
    )
    assert expanded_val == expected_expanded_val


def test_out_of_range_expand_awg_gain_from_normalised_range():
    minimal_pulse_data = {"duration": 20e-9}
    acq = OpInfo(name="test_acq", data=minimal_pulse_data, timing=4e-9)
    with pytest.raises(ValueError):
        expand_awg_from_normalised_range(
            val=10,
            immediate_size=constants.IMMEDIATE_SZ_GAIN,
            param="test_param",
            operation=acq,
        )


def test_loop(empty_qasm_program_qcm):
    num_rep = 10

    qasm = empty_qasm_program_qcm
    qasm.emit(q1asm_instructions.WAIT_SYNC, 4)
    with qasm.loop("this_loop", repetitions=num_rep):
        qasm.emit(q1asm_instructions.WAIT, 20)
    assert len(qasm.instructions) == 5
    assert qasm.instructions[1][1] == q1asm_instructions.MOVE
    num_rep_used, _reg_used = qasm.instructions[1][2].split(",")
    assert int(num_rep_used) == num_rep


@pytest.mark.parametrize("amount", [1, 2, 3, 40])
def test_temp_register(amount, empty_qasm_program_qcm):
    qasm = empty_qasm_program_qcm
    with qasm.temp_registers(amount) as registers:
        for reg in registers:
            assert reg not in qasm.register_manager.available_registers
    for reg in registers:
        assert reg in qasm.register_manager.available_registers


class TestParseProgramLine:
    def test_docstring_example(self):
        # test the docstring example
        assert QASMProgram.parse_program_line(
            "example_label: move 10, R1  # Initialize R1",
        ) == ("move", ["10", "R1"], "example_label", "Initialize R1")

    @pytest.mark.parametrize(
        "label",
        [
            ("", None),
            (" \t ", None),
            ("_label:", "_label"),
            ("  \t  l__a0bel: \t\t  ", "l__a0bel"),
        ],
    )
    @pytest.mark.parametrize(
        "instruction", [("", ""), ("instr", "instr"), (" \t  inst_u  \t", "inst_u")]
    )
    @pytest.mark.parametrize(
        "arguments",
        [
            ("", []),
            (" R0", ["R0"]),
            ("\t @label \t", ["@label"]),
            (" R0, @label,1,\tR2000", ["R0", "@label", "1", "R2000"]),
        ],
    )
    @pytest.mark.parametrize("comment", [("", ""), (" \t# com\t@m:e #nt ", "com\t@m:e #nt")])
    def test_all_line_combos(self, label, instruction, arguments, comment):
        if not instruction[0]:
            arguments = ("", [])
        parsed_line = instruction[1], arguments[1], label[1], comment[1]
        input_line = f"{label[0]}{instruction[0]}{arguments[0]}{comment[0]}"
        assert QASMProgram.parse_program_line(input_line) == parsed_line

    @pytest.mark.parametrize("line", ["label :", "0label:", "instruction0", "label: arg1,arg2"])
    def test_incorrect_format(self, line):
        with pytest.raises(ValueError):
            QASMProgram.parse_program_line(line)


def test_initialize_sweep_registers_max_negative_int(empty_qasm_program_qcm):
    empty_qasm_program_qcm._initialize_sweep_registers(
        domain={
            Variable(DType.AMPLITUDE): LinearDomain(
                dtype=DType.AMPLITUDE, start=-1, stop=1, num=100
            )
        }
    )
    move_instr = empty_qasm_program_qcm.instructions[0]
    arg = move_instr[2]
    assert int(arg.split(",")[0]) == 1 << (constants.REGISTER_SIZE_BITS - 1)


def test_initialize_sweep_registers_max_positive_int(empty_qasm_program_qcm):
    empty_qasm_program_qcm._initialize_sweep_registers(
        domain={
            Variable(DType.AMPLITUDE): LinearDomain(
                dtype=DType.AMPLITUDE, start=1, stop=-1, num=100
            )
        }
    )
    move_instr = empty_qasm_program_qcm.instructions[0]
    arg = move_instr[2]
    assert int(arg.split(",")[0]) == (1 << (constants.REGISTER_SIZE_BITS - 1)) - 1


def test_fix_missing_nops(empty_qasm_program_qcm):
    empty_qasm_program_qcm.instructions = [
        ["", q1asm_instructions.MOVE, "0,R0", ""],
        ["", q1asm_instructions.ADD, "R0,10,R0", ""],
        ["label", "", "", "comment"],
        ["label", "", "", "comment"],
        ["", q1asm_instructions.SUB, "R0,10,R0", ""],
        ["", q1asm_instructions.ADD, "R1,10,R1", ""],
        ["", q1asm_instructions.NOP, "", ""],
        ["", q1asm_instructions.ADD, "R1,1,R0", ""],
    ]
    empty_qasm_program_qcm.fix_missing_nops()
    assert empty_qasm_program_qcm.instructions == [
        ["", q1asm_instructions.MOVE, "0,R0", ""],
        ["", q1asm_instructions.NOP, "", ""],
        ["", q1asm_instructions.ADD, "R0,10,R0", ""],
        ["", q1asm_instructions.NOP, "", ""],
        ["label", "", "", "comment"],
        ["label", "", "", "comment"],
        ["", q1asm_instructions.SUB, "R0,10,R0", ""],
        ["", q1asm_instructions.ADD, "R1,10,R1", ""],
        ["", q1asm_instructions.NOP, "", ""],
        ["", q1asm_instructions.ADD, "R1,1,R0", ""],
    ]
