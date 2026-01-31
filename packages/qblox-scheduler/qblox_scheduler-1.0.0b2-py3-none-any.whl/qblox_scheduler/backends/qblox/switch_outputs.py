# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2025, Qblox B.V.
"""Module containing logic to handle automatic output (RF) switching."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qblox_scheduler.backends.qblox import constants
from qblox_scheduler.backends.qblox.helpers import is_pulse
from qblox_scheduler.compilation import _shift_timing_at, _shift_timing_from
from qblox_scheduler.operations.control_flow_library import ControlFlowOperation
from qblox_scheduler.operations.hardware_operations.pulse_library import RFSwitchToggle
from qblox_scheduler.operations.pulse_library import IdlePulse
from qblox_scheduler.schedules import Schedulable, TimeableSchedule

if TYPE_CHECKING:
    from qblox_scheduler.backends.graph_compilation import CompilationConfig
    from qblox_scheduler.operations import Operation


def switch_outputs(
    schedule: TimeableSchedule,
    config: CompilationConfig,
) -> TimeableSchedule:
    """
    Apply automatic RF output switching to the given schedule based on the operations.

    Parameters
    ----------
    schedule
        The schedule to which automatic output switching will be applied.
    config
        The configuration containing hardware options.

    Returns
    -------
    A tuple containing the schedule with RF output switching applied,
    and the amount of timing added in case of automatic operation insertion.

    """
    schedule, _delta = _switch_outputs(schedule, config)
    return schedule


def _switch_outputs(
    schedule: TimeableSchedule,
    config: CompilationConfig,
) -> tuple[TimeableSchedule, float]:
    # Save list of original schedulables as we're adding to them in _add_switch_operation
    original_schedulables = list(schedule.schedulables.values())
    # Maintain list of last switch operations
    switch_ops = {}

    # Total amount of time this schedule has been shifted forward
    delta = 0.0
    # Shift to add to every operation due to e.g. recursive schedules having been shifted
    add_delta = 0.0

    for i, schedulable in enumerate(original_schedulables):
        operation = schedule.operations[schedulable["operation_id"]]
        control_operation = None
        if isinstance(operation, ControlFlowOperation):
            control_operation = operation
            operation = control_operation.body

        if add_delta > 0:
            _shift_timing_at(schedulable, operation, add_delta)

        if isinstance(operation, TimeableSchedule):
            # Recursively apply pass to nested schedules
            new_operation, op_delta = _switch_outputs(operation, config)
            if control_operation is not None:
                control_operation.body = new_operation
            else:
                schedule.operations[schedulable["operation_id"]] = new_operation
            delta += op_delta
            add_delta += op_delta
        elif is_rf_pulse(operation):
            is_last = i == len(original_schedulables) - 1
            ops, op_delta = _add_switch_operations(
                schedule,
                config,
                operation,
                schedulable,
                switch_ops,
                is_last,
            )
            switch_ops.update(ops)
            delta += op_delta

    return schedule, delta


def is_rf_pulse(operation: Operation) -> bool:
    """
    Check if the operation is an RF pulse.

    Parameters
    ----------
    operation:
        The operation to check.

    Returns
    -------
    :
        True if the operation is an RF pulse, False otherwise.

    """
    if not is_pulse(operation):
        return False
    pulse_info = operation.data["pulse_info"]
    return not pulse_info.get("marker_pulse", False)


def _add_switch_operations(
    schedule: TimeableSchedule,
    config: CompilationConfig,
    original_operation: Operation,
    original_schedulable: Schedulable,
    switch_ops: dict[str, tuple[Operation, Schedulable]],
    is_last: bool,
) -> tuple[dict[str, tuple[Operation, Schedulable]], float]:
    auto_retime = False
    hardware_config = config.hardware_compilation_config
    if hardware_config is not None:
        auto_retime = hardware_config.compiler_options.retime_allowed

    # Get pulses and their durations
    switches = _gather_pulse_durations(original_operation, config)

    # Add operations
    delta = 0.0
    added_ops = {}
    for target_port, (target_duration, target_clock) in switches.items():
        original_start = original_schedulable["abs_time"] + original_operation["pulse_info"]["t0"]
        target_start = original_start - constants.RF_OUTPUT_RISE_TIME
        target_end = original_schedulable["abs_time"] + target_duration

        # Check starts and ends
        if target_start < 0:
            if not auto_retime:
                raise RuntimeError(
                    f"no space to insert RF switch toggle in schedule: "
                    f"{constants.RF_OUTPUT_RISE_TIME * 1e9} ns rise time required, "
                    f"but operation starts at {original_start * 1e9} ns"
                )
            shift_delay = -target_start
            _shift_timing_from(schedule, original_schedulable, shift_delay)
            delta += shift_delay
            target_start = 0
            target_end += shift_delay

        if is_last and constants.RF_OUTPUT_FALL_TIME > 0:
            if not auto_retime:
                raise RuntimeError(
                    f"no space to insert RF switch toggle in schedule: "
                    f"{constants.RF_OUTPUT_FALL_TIME * 1e9} ns required afterwards, "
                    "but schedulable is last operation. "
                    "Please add additional idle time at the end of the schedule, "
                    "by adding e.g. an `IdlePulse` to the schedule."
                )
            idle_sched = schedule.add(
                IdlePulse(duration=constants.RF_OUTPUT_FALL_TIME),
                rel_time=target_duration,
                ref_op=original_schedulable,
                ref_pt="start",
            )
            idle_sched["abs_time"] = original_start + target_duration
            delta += constants.RF_OUTPUT_FALL_TIME
            is_last = False  # we added the pulse

        # Check if we can extend an existing op
        if target_port in switch_ops:
            switch_op, switch_sched = switch_ops[target_port]
            switch_end = switch_sched["abs_time"] + switch_op.duration
            if switch_end + constants.RF_OUTPUT_GRACE_TIME >= target_start:
                # We can! Extend this op.
                to_extend = target_end - switch_end
                if to_extend > 0:
                    switch_op.data["pulse_info"]["duration"] += to_extend
                continue

        # No merging, create new op
        switch_op = RFSwitchToggle(
            duration=target_end - target_start,
            port=target_port,
            clock=target_clock,
        )
        switch_sched = schedule.add(
            switch_op,
            rel_time=-constants.RF_OUTPUT_RISE_TIME,
            ref_op=original_schedulable,
            ref_pt="start",
        )
        switch_sched["abs_time"] = target_start
        added_ops[target_port] = (switch_op, switch_sched)

    return added_ops, delta


def _gather_pulse_durations(
    operation: Operation, config: CompilationConfig
) -> dict[str, tuple[float, str]]:
    # Avoid circular import
    from qblox_scheduler.backends.qblox_backend import _get_module_cfg

    if not is_rf_pulse(operation):
        return {}

    pulse_info = operation.data["pulse_info"]
    target_port = pulse_info["port"]
    target_clock = pulse_info["clock"]
    target_duration = operation.duration

    try:
        module_cfg = _get_module_cfg(target_port, target_clock, config)
    except KeyError:
        return {}

    if getattr(module_cfg, "rf_output_on", None) != "auto":
        return {}

    return {target_port: (target_duration, target_clock)}
