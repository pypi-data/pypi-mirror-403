# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Python dataclasses for compilation to Qblox hardware."""

from __future__ import annotations

from dataclasses import dataclass

from dataclasses_json import DataClassJsonMixin

from qblox_scheduler.backends.qblox.q1asm_instructions import UPDATE_PARAMETERS
from qblox_scheduler.operations.expressions import (
    Expression,
    substitute_value_in_arbitrary_container,
)


@dataclass(frozen=True)
class OpInfo(DataClassJsonMixin):
    """
    Data structure describing a pulse or acquisition and containing all the information
    required to play it.
    """

    name: str
    """Name of the operation that this pulse/acquisition is part of."""
    data: dict
    """The pulse/acquisition info taken from the ``data`` property of the
    pulse/acquisition in the schedule."""
    timing: float
    """The start time of this pulse/acquisition.
    Note that this is a combination of the start time "t_abs" of the schedule
    operation, and the t0 of the pulse/acquisition which specifies a time relative
    to "t_abs"."""

    @property
    def duration(self) -> float:
        """The duration of the pulse/acquisition."""
        return self.data["duration"]

    @property
    def is_acquisition(self) -> bool:
        """Returns ``True`` if this is an acquisition, ``False`` otherwise."""
        return "acq_channel" in self.data or "bin_mode" in self.data

    @property
    def is_real_time_io_operation(self) -> bool:
        """
        Returns ``True`` if the operation is a non-idle pulse (i.e., it has a
        waveform), ``False`` otherwise.
        """
        return (
            self.is_acquisition or self.is_parameter_update or self.data.get("wf_func") is not None
        )

    @property
    def is_offset_instruction(self) -> bool:
        """
        Returns ``True`` if the operation describes a DC offset operation,
        corresponding to the Q1ASM instruction ``set_awg_offset``.
        """
        return "offset_path_I" in self.data or "offset_path_Q" in self.data

    @property
    def is_parameter_instruction(self) -> bool:
        """
        Return ``True`` if the instruction is a parameter, like a voltage offset.

        From the Qblox documentation: "parameter operation instructions" are latched and
        only updated when the upd_param, play, acquire, acquire_weighed or acquire_ttl
        instructions are executed.

        Please refer to
        https://docs.qblox.com/en/main/cluster/q1_sequence_processor.html#q1-instructions
        for the full list of these instructions.
        """
        return (
            self.is_offset_instruction
            or "phase_shift" in self.data
            or "reset_clock_phase" in self.data
            or "clock_freq_new" in self.data
            or "marker_pulse" in self.data
            or "timestamp" in self.data
        )

    @property
    def is_parameter_update(self) -> bool:
        """
        Return ``True`` if the operation is a parameter update, corresponding to the
        Q1ASM instruction ``upd_param``.
        """
        return self.data.get("instruction", "") == UPDATE_PARAMETERS

    @property
    def is_loop(self) -> bool:
        """
        Return ``True`` if the operation is a loop, corresponding to the Q1ASM
        instruction ``loop``.
        """
        return self.data.get("repetitions", None) is not None

    @property
    def is_control_flow_end(self) -> bool:
        """Return ``True`` if the operation is a control flow end."""
        return self.data.get("control_flow_end", None) is True

    def substitute(
        self, substitutions: dict[Expression, Expression | int | float | complex]
    ) -> OpInfo:
        """Substitute matching expressions in operand, possibly evaluating a result."""
        data, changed = substitute_value_in_arbitrary_container(self.data, substitutions)

        if changed:
            return OpInfo(name=self.name, data=data, timing=self.timing)  # type: ignore
        else:
            return self

    def __str__(self) -> str:
        type_label: str = "Acquisition" if self.is_acquisition else "Pulse"
        return f'{type_label} "{self.name}" (t0={self.timing}, duration={self.duration})'

    def __repr__(self) -> str:
        repr_string = (
            f"{'Acquisition' if self.is_acquisition else 'Pulse'} "
            f"{self.name!s} (t={self.timing} to "
            f"{self.timing + self.duration})\ndata={self.data}"
        )
        return repr_string


__all__ = ["OpInfo"]
