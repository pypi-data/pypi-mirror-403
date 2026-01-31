# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.

"""QASM program class for Qblox backend."""

from __future__ import annotations

import re
from contextlib import contextmanager
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
)

import numpy as np
from columnar import columnar
from columnar.exceptions import TableOverflowError

from qblox_scheduler.backends.qblox import constants, helpers, q1asm_instructions
from qblox_scheduler.backends.qblox.conditional import (
    ConditionalManager,
)
from qblox_scheduler.backends.qblox.register_manager import RegisterManager
from qblox_scheduler.backends.qblox.type_casting import (
    SIGNED_INT_CASTING_FNS,
    get_safe_step_size,
)
from qblox_scheduler.enums import BinMode
from qblox_scheduler.operations.variables import Variable

if TYPE_CHECKING:
    from collections.abc import Generator, Hashable, Iterator, Sequence

    from qblox_scheduler.backends.qblox.operation_handling.base import (
        IOperationStrategy,
    )
    from qblox_scheduler.backends.qblox.operation_handling.virtual import (
        ConditionalStrategy,
    )
    from qblox_scheduler.backends.types.qblox import (
        OpInfo,
        StaticHardwareProperties,
    )
    from qblox_scheduler.operations.loop_domains import LinearDomain


@dataclass
class _AcqBinRegister:
    """
    Container for additional data for acquisition bin register
    at a specific loop depth. For each loop depth, this data is stored.
    """

    bin_mode: BinMode | None
    """Bin mode of the loop."""
    increments: int
    """
    Stores the number of increments the register already did
    for all acquisitions in total that are inside this loop depth.
    For example, if there is a loop within this block with
    3 repetitions and 2 acquisitions, and a single acquisition directly in this block,
    then the increments is 2*3+1.
    """


def expand_awg_from_normalised_range(
    val: float,
    immediate_size: int = constants.IMMEDIATE_SZ_GAIN,
    param: str | None = None,
    operation: OpInfo | None = None,
) -> int:
    """
    Takes the value of an awg gain or offset parameter
    in normalized form (abs(param) <= 1.0),
    and expands it to an integer
    in the appropriate range required by the sequencer.

    Parameters
    ----------
    val
        The value of the parameter to expand.
    immediate_size
        The size of the immediate. Used to find the max int value.
    param
        The name of the parameter, to make a possible exception message more
        descriptive.
    operation
        The operation this value is expanded for, to make a possible exception
        message more descriptive.

    Returns
    -------
    :
        The expanded value of the parameter.

    Raises
    ------
    ValueError
        Parameter is not in the normalized range.

    """
    if np.abs(val) > 1.0:
        raise ValueError(
            f"{param} is set to {val}. Parameter must be in the range "
            f"-1.0 <= {param} <= 1.0 for {operation!r}."
        )
    max_gain = immediate_size // 2
    return max(-max_gain, min(round(val * max_gain), max_gain - 1))


class QASMProgram:
    """
    Class that holds the compiled Q1ASM program that is to be executed by the sequencer.

    Apart from this the class holds some convenience functions that auto generate
    certain instructions with parameters, as well as update the elapsed time.

    Parameters
    ----------
    static_hw_properties
        Dataclass holding the properties of the hardware that this program is to be
        played on.
    register_manager
        The register manager that keeps track of the occupied/available registers.
    align_fields
        If True, make QASM program more human-readable by aligning its fields.

    """

    def __init__(
        self,
        static_hw_properties: StaticHardwareProperties,
        register_manager: RegisterManager | None = None,
        align_fields: bool = True,
    ) -> None:
        self.static_hw_properties = static_hw_properties
        """Dataclass holding the properties of the hardware that this program is to be
        played on."""
        self.register_manager = register_manager or RegisterManager()
        """The register manager that keeps track of the occupied/available registers."""
        self.align_fields = align_fields
        """If true, all labels, instructions, arguments and comments
        in the string representation of the program are printed on the same indention level.
        This worsens performance."""

        self.time_last_acquisition_triggered: int | None = None
        """Time on which the last acquisition was triggered. Is ``None`` if no previous
        acquisition was triggered."""
        self.time_last_pulse_triggered: int | None = None
        """Time on which the last operation was triggered. Is ``None`` if no previous
        operation was triggered."""
        self.instructions: list[list] = []
        """A list containing the instructions added to the program. The instructions
        added are in turn a list of the instruction string with arguments."""
        self.conditional_manager = ConditionalManager()
        """The conditional manager that keeps track of the conditionals."""
        self._lock_conditional: bool = False
        """A lock to prevent nested conditionals."""
        self._elapsed_times_in_loops: list[int] = [0]
        """The time elapsed in its current form.
        This is used  to keep track of the total and nested loop timing and necessary waits."""
        self._acq_bin_registers: dict[str, list[_AcqBinRegister]] = {}
        """
        For acquisition loop averaging and appending,
        we keep track of the acquisition bin registers, and their metadata
        to properly increment/decrement them in loops.
        The keys are the registers, and the values are a list of bin register data.
        Each element in the list corresponds to a loop depth,
        for example the 2nd element in that list is for an inner-inner loop.
        """

    @property
    def elapsed_time(self) -> int:
        """
        Current elapsed time of all the instructions in ns.
        It needs to be manually adjusted after each modifications of the QASM program.
        If the QASM program is in a loop,
        only one repetition's worth of elapsed time should be registered.
        After a loop is ended, ``QASMProgram`` will automatically adjust the correct
        elapsed time with all repetitions.
        """
        return sum(self._elapsed_times_in_loops)

    @elapsed_time.setter
    def elapsed_time(self, value: int) -> None:
        difference: int = value - self.elapsed_time
        self._elapsed_times_in_loops[-1] += difference

    @staticmethod
    def get_instruction_as_list(
        instruction: str,
        *args: int | str,
        label: str | None = None,
        comment: str | None = None,
    ) -> list[str]:
        """
        Takes an instruction with arguments, label and comment and turns it into the
        list required by the class.

        Parameters
        ----------
        instruction
            The instruction to use. This should be one specified in
            :mod:`~qblox_scheduler.backends.qblox.q1asm_instructions`
            or the assembler will raise an exception.
        args
            Arguments to be passed.
        label
            Adds a label to the line. Used for jumps and loops.
        comment
            Optionally add a comment to the instruction.

        Returns
        -------
        :
            List that contains all the passed information in the valid format for the
            program.

        Raises
        ------
        SyntaxError
            More arguments passed than the sequencer allows.

        """
        instr_args = ",".join(str(arg) for arg in args)

        label_str = f"{label}:" if label is not None else ""
        comment_str = f"# {comment}" if comment is not None else ""
        return [label_str, instruction, instr_args, comment_str]

    # TODO, use proper (keyword) arguments instead of *args and **kwargs
    def emit(self, *args, **kwargs) -> list[str]:
        """
        Wrapper around the ``get_instruction_as_list`` which adds it to this program.

        Parameters
        ----------
        args
            All arguments to pass to `get_instruction_as_list`.
        **kwargs
            All keyword arguments to pass to `get_instruction_as_list`.

        Returns
        -------
        :
            A list containing instructions.

        """
        self.instructions.append(self.get_instruction_as_list(*args, **kwargs))
        return self.instructions[-1]

    # --- QOL functions -----

    def set_latch(self, op_strategies: Sequence[IOperationStrategy]) -> None:
        """
        Set the latch that is needed for conditional playback.

        This assumes that the latch address is present inside the pulses'
        `operation_info`. If no latch address is found, nothing is emitted.

        Parameters
        ----------
        op_strategies
            The op_strategies containing the pulses to search the latch address in.

        """
        for op_strategy in op_strategies:
            op_info = op_strategy.operation_info
            if not op_info.is_acquisition and (
                op_info.data.get("feedback_trigger_address") is not None
            ):
                self.emit(q1asm_instructions.FEEDBACK_TRIGGER_EN, 1, 4)
                return

    def auto_wait(
        self,
        wait_time: int,
        count_as_elapsed_time: bool = True,
        comment: str | None = None,
    ) -> None:
        """
        Automatically emits a correct wait command. If the wait time is longer than
        allowed by the sequencer it correctly breaks it up into multiple wait
        instructions. If the number of wait instructions is too high (>4), a loop will
        be used.

        Parameters
        ----------
        wait_time
            Time to wait in ns.
        count_as_elapsed_time
            If true, this wait time is taken into account when keeping track of timing.
            Otherwise, the wait instructions are added but this wait time is ignored in
            the timing calculations in the rest of the program.
        comment
            Allows to override the default comment.

        Raises
        ------
        ValueError
            If ``wait_time <= 0``.

        """
        if wait_time == 0:
            return
        if wait_time < constants.MIN_TIME_BETWEEN_OPERATIONS:
            raise ValueError(
                f"Invalid wait time. Attempting to wait "
                f"for {wait_time} ns at t={self.elapsed_time}"
                f" ns."
            )

        def get_reps_divisor_and_remainder(t_ns: int) -> tuple[int, int, int]:
            if t_ns <= constants.IMMEDIATE_MAX_WAIT_TIME:
                return 0, constants.IMMEDIATE_MAX_WAIT_TIME, t_ns

            div = constants.IMMEDIATE_MAX_WAIT_TIME
            reps = t_ns // div
            rem = t_ns % div
            while (
                0 < rem < constants.MIN_TIME_BETWEEN_OPERATIONS
                and div >= constants.MIN_TIME_BETWEEN_OPERATIONS
            ):
                div -= 1
                reps = t_ns // div
                rem = t_ns % div
            if (
                0 < rem < constants.MIN_TIME_BETWEEN_OPERATIONS
                or div < constants.MIN_TIME_BETWEEN_OPERATIONS
            ):
                raise ValueError(f"Failed to compile wait instructions for duration of {t_ns} ns.")
            return reps, div, rem

        comment = comment if comment else f"auto generated wait ({wait_time} ns)"
        repetitions, wait_in_loop, time_left = get_reps_divisor_and_remainder(wait_time)

        if repetitions > 0:
            # number of instructions where it becomes worthwhile to use a loop.
            instr_number_using_loop = 4
            if repetitions > instr_number_using_loop:
                loop_label = f"wait{len(self.instructions)}"
                with self.loop(loop_label, repetitions):
                    self.emit(
                        q1asm_instructions.WAIT,
                        wait_in_loop,
                        comment=comment,
                    )
                    if count_as_elapsed_time:
                        self.elapsed_time += wait_in_loop
                    self.conditional_manager.num_real_time_instructions += 1
            else:
                for _ in range(repetitions):
                    self.emit(
                        q1asm_instructions.WAIT,
                        wait_in_loop,
                        comment=comment,
                    )
                    if count_as_elapsed_time:
                        self.elapsed_time += wait_in_loop
                    self.conditional_manager.num_real_time_instructions += 1

        if time_left > 0:
            self.emit(
                q1asm_instructions.WAIT,
                time_left,
                comment=comment,
            )
            if count_as_elapsed_time:
                self.elapsed_time += time_left
            self.conditional_manager.num_real_time_instructions += 1

    def wait_till_start_operation(self, operation: OpInfo) -> None:
        """
        Waits until the start of a pulse or acquisition.

        Parameters
        ----------
        operation
            The pulse or acquisition that we want to wait for.

        Raises
        ------
        ValueError
            If wait time < 0.

        """
        start_time = helpers.to_grid_time(operation.timing)
        wait_time = start_time - self.elapsed_time
        if wait_time > 0:
            self.auto_wait(wait_time)
        elif wait_time < 0 and operation.is_parameter_instruction:
            raise ValueError(
                f"Invalid timing. {operation!r} cannot be started at this order or time. "
                f"Please try to reorder your operations by adding this operation "
                "before any other operation (possibly at the same time) that happens at that time."
            )
        elif wait_time < 0 and operation.name != "IdlePulse":
            # The idle pulse is a no operation, if any other operation
            # is simultaneously running, it is allowed.
            raise ValueError(
                f"Invalid timing. Attempting to wait for {wait_time} "
                f"ns before {operation!r}. Please note that a wait time of at least"
                f" {constants.MIN_TIME_BETWEEN_OPERATIONS} ns is required between "
                f"operations.\nAre multiple operations being started at the same time?"
            )

    def _process_awg_instruction_args(
        self,
        path_I: float | Variable,
        path_Q: float | Variable,
        param_name: str,
        operation: OpInfo,
    ) -> tuple[int | str, int | str]:
        def process_variable_and_get_temp_register(var: Variable) -> str:
            # Shift a register value to a lower bit range
            main_register = self.register_manager.get_register_of_variable(var)

            smaller_register = self.register_manager.allocate_register()
            self.emit(
                q1asm_instructions.ARITHMETIC_SHIFT_RIGHT,
                main_register,
                constants.AWG_INSTRUCTION_BIT_SIZE,
                smaller_register,
            )
            return smaller_register

        def process_float_and_get_temp_register(val: float) -> str:
            val_int = expand_awg_from_normalised_range(val, param="awg_gain", operation=operation)
            register = self.register_manager.allocate_register()

            self.emit(
                q1asm_instructions.MOVE,
                val_int,
                register,
            )
            return register

        reserved_registers = []

        if isinstance(path_I, Variable) and isinstance(path_Q, Variable):
            path_I_arg = process_variable_and_get_temp_register(path_I)
            if path_I is path_Q:
                path_Q_arg = path_I_arg
                reserved_registers = [path_I_arg]
            else:
                path_Q_arg = process_variable_and_get_temp_register(path_Q)
                reserved_registers = [path_I_arg, path_Q_arg]
        elif isinstance(path_I, Variable):
            path_I_arg = process_variable_and_get_temp_register(path_I)
            path_Q_arg = process_float_and_get_temp_register(path_Q)  # type: ignore
            reserved_registers = [path_I_arg, path_Q_arg]
        elif isinstance(path_Q, Variable):
            path_I_arg = process_float_and_get_temp_register(path_I)
            path_Q_arg = process_variable_and_get_temp_register(path_Q)
            reserved_registers = [path_I_arg, path_Q_arg]
        else:
            path_I_arg = expand_awg_from_normalised_range(
                path_I, param=param_name, operation=operation
            )
            path_Q_arg = expand_awg_from_normalised_range(
                path_Q, param=param_name, operation=operation
            )

        if reserved_registers:
            self.emit(q1asm_instructions.NOP)
            for reg in reserved_registers:
                self.register_manager.free_register(reg)
        return path_I_arg, path_Q_arg

    def set_gain_from_amplitude(
        self,
        amplitude_path_I: float | Variable,
        amplitude_path_Q: float | Variable,
        operation: OpInfo,
    ) -> None:
        """
        Sets the gain such that a 1.0 in waveform memory corresponds to the full awg gain.

        Parameters
        ----------
        amplitude_path_I
            Voltage to set on path_I.
        amplitude_path_Q
            Voltage to set on path_Q.
        operation
            The operation for which this is done. Used for the exception messages.

        """
        path_I_arg, path_Q_arg = self._process_awg_instruction_args(
            amplitude_path_I, amplitude_path_Q, "awg_gain", operation
        )

        self.emit(
            q1asm_instructions.SET_AWG_GAIN,
            path_I_arg,
            path_Q_arg,
            comment=f"setting gain for {operation.name}",
        )

    def set_offset_from_float_or_variable(
        self,
        offset_path_I: float | Variable,
        offset_path_Q: float | Variable,
        operation: OpInfo,
    ) -> None:
        """
        Sets the offset such that a 1.0 float value corresponds to the maximum offset.

        Parameters
        ----------
        offset_path_I
            Voltage to set on path_I.
        offset_path_Q
            Voltage to set on path_Q.
        operation
            The operation for which this is done. Used for the exception messages.

        """
        path_I_arg, path_Q_arg = self._process_awg_instruction_args(
            offset_path_I, offset_path_Q, "awg_offset", operation
        )

        self.emit(
            q1asm_instructions.SET_AWG_OFFSET,
            path_I_arg,
            path_Q_arg,
            comment=f"setting offset for {operation.name}",
        )

    def merge_some_arithmetic_instructions(self) -> None:
        """
        Merges all add and sub instructions that happen after each other,
        and are only applied in a form "add RX,NUMBER,RX.
        This is useful especially to merge instructions
        that increment and decrement bin indices for averaging,
        because they can happen right after each other for the same register,
        which is not allowed in Q1ASM.
        """

        def parse_eligible_instruction(instruction: list[str]) -> tuple[str, int] | None:
            """
            Returns the parsed addition or subtraction operation
            in a form of register, signed integer,
            if the instruction is only incrementing or decrementing a register by a constant.
            Otherwise, returns None.
            """
            operation = instruction[1]
            if operation not in ("add", "sub"):
                return None
            arguments = instruction[2].split(",")
            if arguments[0] != arguments[2]:
                return None
            register = arguments[0]
            if arguments[1].isdigit():
                n = int(arguments[1])
                if operation == "sub":
                    n = -n
                return register, n
            return None

        def merge(
            mergeable_instructions: list[tuple[str, int]], new_instructions: list[list[str]]
        ) -> None:
            """
            Adds the merged instructions to the new instructions,
            and clears the mergeable_instructions.
            """
            register_to_n = {}
            for register, n in mergeable_instructions:
                register_to_n[register] = register_to_n.get(register, 0) + n

            for register, n in register_to_n.items():
                if n != 0:
                    new_instructions.append(
                        ["", "add" if n > 0 else "sub", f"{register},{abs(n)},{register}", ""]
                    )
            mergeable_instructions.clear()

        new_instructions: list[list[str]] = []
        mergeable_instructions: list[tuple[str, int]] = []
        for instruction in self.instructions:
            if (eligible_instruction := parse_eligible_instruction(instruction)) is not None:
                mergeable_instructions.append(eligible_instruction)
            else:
                merge(mergeable_instructions, new_instructions)
                new_instructions.append(instruction)
        merge(mergeable_instructions, new_instructions)

        self.instructions = new_instructions

    def __str__(self) -> str:
        """
        Returns a string representation of the program. The sequencer expects the program
        to be such a string.

        The conversion to str is done using `columnar`, which expects a list of lists,
        and turns it into a string with rows and columns corresponding to those lists.

        Returns
        -------
        :
            The string representation of the program.

        """
        if self.align_fields:
            try:
                instructions_str = columnar(
                    self.instructions, headers=None, no_borders=True, wrap_max=0
                )
            # running in a sphinx environment can trigger a TableOverFlowError
            except TableOverflowError:
                instructions_str = columnar(
                    self.instructions, headers=None, no_borders=True, terminal_width=120
                )
            # columnar inserts a newline before all the instruction rows
            return instructions_str.split("\n", 1)[1]
        else:
            return "\n".join(" ".join(instruction) for instruction in self.instructions) + "\n"

    @contextmanager
    def conditional(self, operation: ConditionalStrategy) -> Generator[None, None, None]:
        """
        Defines a conditional block in the QASM program.

        When this context manager is entered/exited it will insert additional
        ``set_cond`` QASM instructions in the program that specify the
        conditionality of a set of instructions.

        The following example should make it clear what is happening.

        .. code-block:: none

            set_cond set_enable=1, mask=0, operator=OR, else_duration=4
            <50 ns duration of instructions that contains 3 real time instructions>

            set_cond set_enable=1, mask=0, operator=NOR, else_duration=4
            wait 50-3*4+4 = 42 ns # adding an additional 4 ns to make math work out

            set_cond set_enable=0, mask=0, operator=OR, else_duration=4

        The `else_duration` is the wait time per real time instruction in the
        conditional block. If a trigger happened, the first block runs normally for
        50 ns, the second block runs for 4 ns. If there is no trigger, the first
        block runs for 3*4 = 12 ns, second block for 42 ns. So the duration in
        both cases is 42 ns. Note that `set_cond` itself has zero duration.

        The exact values that need to be passed to the ``set_cond``
        instructions are determined while the qasm program is generated with the
        help of
        :class:`~qblox_scheduler.backends.qblox.conditional.FeedbackTriggerCondition`
        and
        :class:`~qblox_scheduler.backends.qblox.conditional.ConditionalManager`.

        Parameters
        ----------
        operation: ConditionalStrategy
            The conditional strategy that defines the start of a conditional block.

        """
        trigger_condition = operation.trigger_condition
        if self._lock_conditional:
            raise RuntimeError(
                "Nested conditional playback inside schedules is not supported by "
                f"the Qblox backend. "
                f"This error is caused by the following operation strategy:\n{operation}."
            )
        self._lock_conditional = True

        # This instruction will be replaced when the context manager exits the
        # conditional block.
        self.emit(
            q1asm_instructions.FEEDBACK_SET_COND,
            int(trigger_condition.enable),
            trigger_condition.mask,
            trigger_condition.operator.value,
            constants.MIN_TIME_BETWEEN_OPERATIONS,
            comment="start conditional playback",
        )
        self.conditional_manager.reset()
        self.conditional_manager.start_time = self.elapsed_time

        yield
        # When the context manager exits, add an else branch to fill the correct wait time
        # and add a stop conditional playback and
        # replace the initial FEEDBACK_SET_COND instruction.
        self.conditional_manager.end_time = self.elapsed_time
        self.emit(
            q1asm_instructions.FEEDBACK_SET_COND,
            int(trigger_condition.enable),
            trigger_condition.mask,
            (~trigger_condition.operator).value,
            constants.MIN_TIME_BETWEEN_OPERATIONS,
            comment="else wait",
        )
        # autowait now adds an additional duration to elapsed time that we need to compensate.
        duration = (
            self.conditional_manager.duration
            - constants.MIN_TIME_BETWEEN_OPERATIONS
            * self.conditional_manager.num_real_time_instructions
            + constants.MIN_TIME_BETWEEN_OPERATIONS
        )
        self.auto_wait(duration, count_as_elapsed_time=False)
        self.emit(
            q1asm_instructions.FEEDBACK_SET_COND,
            0,
            0,
            0,
            0,
            comment="stop conditional playback",
        )
        self.elapsed_time += constants.MIN_TIME_BETWEEN_OPERATIONS

        self.conditional_manager.reset()
        self._lock_conditional = False

    @contextmanager
    def loop(
        self,
        label: str,
        repetitions: int,
        domain: dict[Variable, LinearDomain] | None = None,
    ) -> Generator[None, None, None]:
        """
        Defines a context manager that can be used to generate a loop in the QASM
        program.

        Parameters
        ----------
        label
            The label to use for the jump.
        repetitions
            The amount of iterations to perform.
        domain:
            A dictionary of domains to sweep over (in a zip-fashion), keyed by variable. If None, a
            simple repetition loop is generated. By default None.


        Examples
        --------
        This adds a loop to the program that loops 10 times over a wait of 100 ns.

        .. jupyter-execute::

            from qblox_scheduler.backends.qblox.qasm_program import QASMProgram
            from qblox_scheduler.backends.qblox.instrument_compilers import QCMCompiler
            from qblox_scheduler.backends.qblox import register_manager
            from qblox_scheduler.backends.types.qblox import QCMDescription

            qasm = QASMProgram(
                static_hw_properties=QCMCompiler.static_hw_properties,
                register_manager=register_manager.RegisterManager(),
                align_fields=True,
            )

            with qasm.loop(label="repeat", repetitions=10):
                qasm.auto_wait(100)

            qasm.instructions

        """
        self._elapsed_times_in_loops.append(0)

        loop_count_register = self.register_manager.allocate_register()
        comment = f"iterator for loop with label {label}"

        if domain is not None:
            self._initialize_sweep_registers(domain)

        # Do after initializing sweep registers to reduce chance of needing a nop
        self.emit(q1asm_instructions.MOVE, repetitions, loop_count_register, comment=comment)

        self.emit(q1asm_instructions.NEW_LINE, label=label)

        self._adjust_acq_bin_registers_start_loop()

        yield

        self._adjust_acq_bin_registers_end_loop()

        if domain is not None:
            self._update_sweep_registers(domain)

        self.emit(q1asm_instructions.LOOP, loop_count_register, f"@{label}")
        self.register_manager.free_register(loop_count_register)

        if domain is not None:
            self._free_sweep_registers(domain)

        self._adjust_acq_bin_registers_after_loop(repetitions)

        last_elapsed_time = self._elapsed_times_in_loops.pop()

        self._elapsed_times_in_loops[-1] += last_elapsed_time * repetitions

    def _initialize_sweep_registers(self, domain: dict[Variable, LinearDomain]) -> None:
        def twos_complement(val: int, bits: int = constants.REGISTER_SIZE_BITS) -> int:
            return (1 << bits) + val if val < 0 else val

        for var, dom in domain.items():
            reg = self.register_manager.allocate_register_for_variable(var)
            val = SIGNED_INT_CASTING_FNS[dom.dtype](np.real(dom.start))
            self.emit(
                q1asm_instructions.MOVE,
                twos_complement(val),
                reg,
                comment="Initialize sweep var",
            )

    def _update_sweep_registers(self, domain: dict[Variable, LinearDomain]) -> None:
        def emit_update(reg: str, val: int) -> None:
            if val < 0:
                self.emit(q1asm_instructions.SUB, reg, -val, reg, comment="Update sweep var")
            elif val > 0:
                self.emit(q1asm_instructions.ADD, reg, val, reg, comment="Update sweep var")
            # if exactly 0, do nothing

        for var, dom in domain.items():
            reg = self.register_manager.get_register_of_variable(var)
            val = get_safe_step_size(dom)
            emit_update(reg, val)

    def _free_sweep_registers(self, domain: dict[Variable, LinearDomain]) -> None:
        for var in domain:
            self.register_manager.free_register_of_variable(var)

    @contextmanager
    def temp_registers(self, amount: int = 1) -> Iterator[list[str]]:
        """
        Context manager for using a register temporarily. Frees up the register
        afterwards.

        Parameters
        ----------
        amount
            The amount of registers to temporarily use.

        Yields
        ------
        :
            Either a single register or a list of registers.

        """
        registers: list[str] = [self.register_manager.allocate_register() for _ in range(amount)]
        yield registers

        for reg in registers:
            self.register_manager.free_register(reg)

    @staticmethod
    def parse_program_line(
        program_line: str,
    ) -> tuple[str, list[str], str | None, str]:
        """
        Parses a single line of a Q1ASM program and extracts its components.

        This function processes a line of Q1ASM code;
        handling labels, instructions, arguments, and comments.

        Parameters
        ----------
        program_line
            A single line of Q1ASM code to be parsed.

        Returns
        -------
        instruction
            The instruction part of the Q1ASM line, empty string if no instruction present.
        arguments
            A list of arguments associated with the instruction, empty list if no arguments present.
        label
            The processed label extracted from the line, or None if no label is present.
        comment
            The comment extracted from the line; empty string if no comment is present.

        Raises
        ------
        ValueError
            If the program line is not a valid q1asm format

        Examples
        --------
        >>> QASMProgram.parse_program_line("example_label: move 10, R1  # Initialize R1")
        ('move', ['10', 'R1'], 'example_label', 'Initialize R1')

        """
        # A q1asm line has the following format:
        # [label:] instruction argument,argument,... [comment]
        # Everything is optional.
        # Arguments are only allowed if an instruction is given
        # Arguments can either be numbers, registers, or label references.
        # We set up the regex to parse it.
        alpha_num_regex = "[a-zA-Z0-9_]"
        white_space = "[ \t]+"  # Space and tabs
        # label has to start with a letter or underscore
        label_regex = f"[a-zA-Z_]{alpha_num_regex}*"
        argument_regex = f"(R?[0-9]+|(@{label_regex}))"
        argument_list_regex = f"{white_space}({argument_regex}+,({white_space})?)*{argument_regex}"
        instruction_regex = "[a-z_]+"  # All instructions are snake_case
        comment_regex = "#(?P<comment>.*)"
        line_regex = (
            f"({white_space})?"
            f"((?P<label>{label_regex}):)?"
            f"({white_space})?"
            f"((?P<instruction>{instruction_regex})(?P<arguments>{argument_list_regex})?)?"
            f"({white_space})?"
            f"({comment_regex})?"
        )
        full_match = re.fullmatch(line_regex, program_line)
        if full_match is None:
            raise ValueError(f"'{program_line}' is not valid Q1ASM.")
        match = full_match.groupdict()
        label = match["label"]
        instruction = match["instruction"] or ""
        arguments = (
            [arg.strip() for arg in match["arguments"].split(",")] if match["arguments"] else []
        )
        # extract comment when it exists
        comment = match["comment"].strip() if match["comment"] else ""

        return instruction, arguments, label, comment

    def update_and_adjust_acq_bin_register(
        self, register: str, loop_bin_modes: list[BinMode], acq_channel: Hashable
    ) -> None:
        """
        Increment the acquisition bin register,
        and store metadata regarding the bin modes of any nested
        loops the acquisition may be contained in
        to adjust the acquisition bin register when necessary.
        """
        self.emit(
            q1asm_instructions.ADD,
            register,
            1,
            register,
            comment=f"Increment bin_idx for ch{acq_channel}",
        )
        if register in self._acq_bin_registers:
            for i, bin_mode in enumerate(loop_bin_modes):
                if self._acq_bin_registers[register][i].bin_mode is None:
                    self._acq_bin_registers[register][i].bin_mode = bin_mode
                else:
                    # Sanity check whether the compiler is consistent.
                    # Each time this function is called with the same register, the loop_bin_modes
                    # must be consistent with the current bin modes in _acq_bin_registers.
                    assert bin_mode == self._acq_bin_registers[register][i].bin_mode
        else:
            self._acq_bin_registers[register] = [
                _AcqBinRegister(bin_mode, 0) for bin_mode in loop_bin_modes
            ]

        self._acq_bin_registers[register][-1].increments += 1

    def _adjust_acq_bin_registers_end_loop(self) -> None:
        for register, acq_bin_register in self._acq_bin_registers.items():
            if (
                acq_bin_register[-1].bin_mode == BinMode.AVERAGE
                and acq_bin_register[-1].increments != 0
            ):
                self.emit(
                    q1asm_instructions.SUB,
                    register,
                    acq_bin_register[-1].increments,
                    register,
                    comment="Decrement bin_idx for averaging",
                )

    def _adjust_acq_bin_registers_start_loop(self) -> None:
        for acq_bin_register in self._acq_bin_registers.values():
            acq_bin_register.append(_AcqBinRegister(None, 0))

    def _adjust_acq_bin_registers_after_loop(self, repetitions: int) -> None:
        for register, acq_bin_register in self._acq_bin_registers.items():
            last_acq_bin_register = acq_bin_register.pop()
            if last_acq_bin_register.bin_mode is not None:
                last_acq_bin_register.increments *= (
                    repetitions if last_acq_bin_register.bin_mode == BinMode.APPEND else 1
                )
                if len(acq_bin_register) != 0:
                    acq_bin_register[-1].increments += last_acq_bin_register.increments

                if (
                    last_acq_bin_register.bin_mode == BinMode.AVERAGE
                    and last_acq_bin_register.increments != 0
                ):
                    self.emit(
                        q1asm_instructions.ADD,
                        register,
                        last_acq_bin_register.increments,
                        register,
                        comment="Increment bin_idx for averaging",
                    )

    def fix_missing_nops(self) -> None:
        """Insert NOP instructions where needed."""
        writing_instructions = {
            q1asm_instructions.MOVE,
            q1asm_instructions.NOT,
            q1asm_instructions.ADD,
            q1asm_instructions.SUB,
            q1asm_instructions.AND,
            q1asm_instructions.OR,
            q1asm_instructions.XOR,
            q1asm_instructions.ARITHMETIC_SHIFT_LEFT,
            q1asm_instructions.ARITHMETIC_SHIFT_RIGHT,
        }

        def writes_to_register(instr: list[str]) -> str | None:
            if instr[1] in writing_instructions:
                return instr[2].split(",")[-1].strip()

        def next_instruction_reads_from_register(i: int, register: str) -> bool:
            for next_instr in self.instructions[i + 1 :]:
                # Skip any "instructions" that are just a label or a comment
                if len(next_instr[1]) > 0:
                    # We assume that we do not write to the same register back-to-back, so we assume
                    # the register is read if the following is True.
                    return register in next_instr[2]
            return False

        idx_to_insert = []

        for i, instr in enumerate(self.instructions):
            if (write_reg := writes_to_register(instr)) and next_instruction_reads_from_register(
                i, write_reg
            ):
                idx_to_insert.append(i + 1)

        for i in reversed(idx_to_insert):
            self.instructions.insert(i, QASMProgram.get_instruction_as_list(q1asm_instructions.NOP))
