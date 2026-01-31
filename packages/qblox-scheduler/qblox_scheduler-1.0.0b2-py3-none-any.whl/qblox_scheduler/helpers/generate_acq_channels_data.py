# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Helper functions to generate acq_indices."""

from __future__ import annotations

import warnings
from copy import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from qblox_scheduler.enums import BinMode
from qblox_scheduler.helpers.schedule import (
    _is_acquisition_binned_append,
    _is_acquisition_binned_average,
    _is_acquisition_binned_average_append,
)
from qblox_scheduler.operations.control_flow_library import (
    ConditionalOperation,
    LoopOperation,
)
from qblox_scheduler.operations.expressions import Expression
from qblox_scheduler.schedules.schedule import (
    AcquisitionChannelData,
    AcquisitionChannelsData,
    TimeableScheduleBase,
)

if TYPE_CHECKING:
    from collections.abc import Hashable
    from typing import Any

    from qblox_scheduler.operations.loop_domains import Domain
    from qblox_scheduler.operations.operation import Operation
    from qblox_scheduler.operations.variables import Variable

SchedulableLabel = Union[str, None]
FullSchedulableLabel = tuple[SchedulableLabel, ...]


@dataclass
class AcquisitionIndices:
    """
    The AcquisitionIndices is just
    (acq_index_offset, loop_bin_modes=None, number_of_acq_indices=1)
    for acquisitions outside of loops,
    but if the acquisition is inside a nested loop,
    the `loop_bin_modes` lists whether the acquisition is averaged or looped for each loop level.
    For example, if you have a multi-dimensional with 2, 3 and 4 repetitions,
    and you average over the last nested level,
    `loop_bin_modes=[APPEND, APPEND, AVERAGE]`, and `number_of_acq_indices=2*3`.
    """

    acq_index_offset: int
    loop_bin_modes: list[BinMode] | None
    number_of_acq_indices: int

    @property
    def acq_index(self) -> list[int] | int:
        """
        Acquisition index as a number if there are no loops,
        otherwise the list of all the acquisition indices.
        """
        if self.loop_bin_modes is None:
            return self.acq_index_offset
        else:
            return list(
                range(self.acq_index_offset, self.acq_index_offset + self.number_of_acq_indices)
            )


SchedulableLabelToAcquisitionIndex = dict[FullSchedulableLabel, AcquisitionIndices]
"""
A mapping from schedulables to an acquisition index.

This mapping helps the backend to figure out which
binned acquisition corresponds to which acquisition index.
Note, it maps the full schedulable label to acquisition indices,
Only defined for binned acquisitions, and backend independent.

For control flows, the `None` in the schedulable label refers to the `body`
of the control flow. This is for future proofing, if control flows were extended
to include maybe multiple suboperations.
"""


@dataclass
class LoopData:
    """Data to contain relevant information from LoopOperation."""

    repetitions: int
    domain: dict[Variable, Domain] | None


def _evaluate_coords_recursively(
    loops: list[LoopData],
    evaluated_coords: list[dict],
) -> list[dict]:
    """
    Evaluate coords even if there are variables in it.
    The accumulator is stored in evaluated_coords, which is returned.
    """

    def evaluate_domain(
        domain: dict[Variable, Domain],
    ) -> list[dict[Expression, Expression | int | float | complex]]:
        steps = max(current_domain.num_steps for current_domain in domain.values())

        # list of dictionaries from variable to a value.
        evaluated_variables: list[dict[Expression, Expression | int | float | complex]] = [
            {} for _ in range(steps)
        ]
        for variable, current_domain in domain.items():
            for i, value in enumerate(current_domain.values()):
                assert isinstance(
                    value, Expression | int | float | complex
                )  # Currently only these are supported.
                evaluated_variables[i][variable] = value

        return evaluated_variables

    def substitute_coords_variables(
        coords: dict, evaluated_variables: dict[Expression, Expression | int | float | complex]
    ) -> dict:
        coords = copy(coords)
        for key, value in coords.items():
            if isinstance(value, Expression):
                coords[key] = value.substitute(evaluated_variables)
        return coords

    if len(loops) == 0:
        return evaluated_coords

    current_loop = loops[-1]
    if current_loop.domain is None:
        evaluated_coords = [
            copy(item) for _ in range(current_loop.repetitions) for item in evaluated_coords
        ]
    else:
        evaluated_coords = [
            substitute_coords_variables(current_coords, evaluated_variables)
            for evaluated_variables in evaluate_domain(current_loop.domain)
            for current_coords in evaluated_coords
        ]
    return _evaluate_coords_recursively(loops[:-1], evaluated_coords)


def _evaluate_coords(coords: dict, loops: list[LoopData]) -> list[dict]:
    """Evaluate coords even if there are variables in it."""
    return _evaluate_coords_recursively(loops, [coords])


def _get_loops_with_append_bin_mode_and_all_loop_bin_modes(
    coords: dict,
    loops: list[LoopData],
    append_all_loops: bool,
) -> tuple[list[LoopData], list[BinMode]]:
    def is_variable_in_expression(domain: dict[Variable, Domain] | None, coords: dict) -> bool:
        if domain is None:
            return False

        for variable in domain:
            for coords_value in coords.values():
                if isinstance(coords_value, Expression) and (
                    (variable is coords_value) or (variable in coords_value)
                ):
                    return True
        return False

    append_loops = []
    loop_bin_modes = []
    for loop in loops:
        if is_variable_in_expression(loop.domain, coords) or append_all_loops:
            append_loops.append(loop)
            loop_bin_modes.append(BinMode.APPEND)
        else:
            loop_bin_modes.append(BinMode.AVERAGE)
    return append_loops, loop_bin_modes


def _generate_acq_channels_data_binned_average(
    acq_channel_data: AcquisitionChannelData,
    schedulable_label_to_acq_index: SchedulableLabelToAcquisitionIndex,
    full_schedulable_label: FullSchedulableLabel,
    coords: dict,
    acq_channel: Hashable,
    acq_index: int | None,
) -> None:
    """
    Generates the acquisition channel data, and updates acq_channel_data,
    and updates schedulable_label_to_acq_index for average bin mode.
    """
    assert isinstance(acq_channel_data.coords, list)

    if acq_index is not None and acq_index != len(acq_channel_data.coords):
        raise ValueError(
            f"Found invalid {acq_index=} for {acq_channel=}. "
            f"Make sure that each explicitly defined acq_index "
            f"starts at 0, and increments by 1 for each new acquisition "
            f"within the same acquisition channel, ordered by time.",
        )
    if any(isinstance(value, Expression) for value in coords.values()):
        raise ValueError(
            f"Expression acquisition coords are not supported for average bin mode. "
            f"For {acq_channel=} found {coords=} a variable."
        )
    new_acq_index = len(acq_channel_data.coords)
    schedulable_label_to_acq_index[full_schedulable_label] = AcquisitionIndices(
        new_acq_index, None, 1
    )
    acq_channel_data.coords.append(coords)


def _generate_acq_channels_data_binned_append(
    acq_channel_data: AcquisitionChannelData,
    schedulable_label_to_acq_index: SchedulableLabelToAcquisitionIndex,
    full_schedulable_label: FullSchedulableLabel,
    loops: list[LoopData],
    coords: dict,
    acq_channel: Hashable,
    acq_index: int | None,
    append_all_loops: bool,
) -> None:
    """
    Generates the acquisition channel data, and updates acq_channel_data,
    and updates schedulable_label_to_acq_index for average bin mode.
    """
    # Bear in mind: contrary to the average case,
    # we do not test whether the `acq_index`
    # are defined in order (starting from 0 and incremented by one for each new acquisition),
    # because that's very complicated in case there are loops inside the schedule.
    # We just assume that they are.

    assert isinstance(acq_channel_data.coords, list)
    coords = (
        {f"acq_index_legacy_{acq_channel}": acq_index, **coords}
        if (acq_index is not None)
        else coords
    )
    evaluated_coords: list[dict] = []
    if len(loops) == 0:
        evaluated_coords = [coords]
        loop_bin_modes = []
    else:
        if acq_index is not None:
            warnings.warn(
                (
                    f"Explicitly defined acquisition index for an append mode acquisition "
                    f"within a loop will not be supported in the future. "
                    f"Ignoring {acq_index=} for {acq_channel=}."
                ),
                FutureWarning,
            )
        append_loops, loop_bin_modes = _get_loops_with_append_bin_mode_and_all_loop_bin_modes(
            coords, loops, append_all_loops
        )
        evaluated_coords = _evaluate_coords(coords, append_loops)
        # Add loop_repetitions to evaluated_coords.
        for i, current_coords in enumerate(evaluated_coords):
            current_coords[f"loop_repetition_{acq_channel}"] = i
    first_acq_index = len(acq_channel_data.coords)
    schedulable_label_to_acq_index[full_schedulable_label] = AcquisitionIndices(
        first_acq_index, loop_bin_modes, len(evaluated_coords)
    )
    acq_channel_data.coords.extend(evaluated_coords)


def _validate_trace_protocol(
    acq_channel: Hashable,
    acq_channels_data: AcquisitionChannelsData,
    loops: list[LoopData],  # noqa: ARG001
) -> None:
    if acq_channel in acq_channels_data:
        raise ValueError(
            f"Multiple acquisitions found for acq_channel '{acq_channel}' "
            f"which has a trace acquisition. "
            f"Only one trace acquisition is allowed for each acq_channel.",
        )


def _generate_acq_channels_data_for_protocol(
    acq_info: dict,
    acq_channels_data: AcquisitionChannelsData,
    schedulable_label_to_acq_index: SchedulableLabelToAcquisitionIndex,
    full_schedulable_label: FullSchedulableLabel,
    loops: list[LoopData],
    is_explicit_acq_index: bool,
) -> None:
    """
    Generates the acquisition channel data, and updates acq_channel_data,
    and updates schedulable_label_to_acq_index.
    """
    acq_channel: Hashable = acq_info["acq_channel"]
    protocol: str = acq_info["protocol"]
    bin_mode: BinMode = acq_info["bin_mode"]

    coords: dict = acq_info["coords"] or {}

    acq_index: int | None = acq_info["acq_index"]
    # If is_explicit_acq_index, then only acquisitions where acq_index
    # is explicitly defined will be taken into account;
    # otherwise only the acquisitions where it's not defined.
    if is_explicit_acq_index is (acq_index is None):
        return

    if (acq_channel_data := acq_channels_data.get(acq_channel, None)) is not None:
        if acq_channel_data.protocol != protocol:
            raise ValueError(
                f"Found different acquisition protocols "
                f"('{acq_channel_data.protocol}' and '{protocol}') "
                f"for acq_channel '{acq_channel}'. "
                f"Make sure there is only one protocol for each acq_channel.",
            )
        if acq_channel_data.bin_mode != bin_mode:
            raise ValueError(
                f"Found different bin modes "
                f"('{acq_channel_data.bin_mode}' and '{bin_mode}') "
                f"for acq_channel '{acq_channel}'. "
                f"Make sure there is only one bin mode for each acq_channel.",
            )

    if _is_acquisition_binned_average(protocol, bin_mode):
        if acq_channel not in acq_channels_data:
            acq_channels_data[acq_channel] = AcquisitionChannelData(
                acq_index_dim_name=("acq_index_" + str(acq_channel)),
                protocol=protocol,
                bin_mode=bin_mode,
                coords=[],
            )
        _generate_acq_channels_data_binned_average(
            acq_channel_data=acq_channels_data[acq_channel],
            schedulable_label_to_acq_index=schedulable_label_to_acq_index,
            full_schedulable_label=full_schedulable_label,
            coords=coords,
            acq_channel=acq_channel,
            acq_index=acq_index,
        )
    elif (
        _is_acquisition_binned_append(protocol, bin_mode)
        or _is_acquisition_binned_average_append(protocol, bin_mode)
        or (protocol == "TimetagTrace" and bin_mode == BinMode.APPEND)
    ):
        if acq_channel not in acq_channels_data:
            acq_channels_data[acq_channel] = AcquisitionChannelData(
                acq_index_dim_name=("acq_index_" + str(acq_channel)),
                protocol=protocol,
                bin_mode=bin_mode,
                coords=[],
            )
        _generate_acq_channels_data_binned_append(
            acq_channel_data=acq_channels_data[acq_channel],
            schedulable_label_to_acq_index=schedulable_label_to_acq_index,
            full_schedulable_label=full_schedulable_label,
            loops=loops,
            coords=coords,
            acq_channel=acq_channel,
            acq_index=acq_index,
            append_all_loops=(bin_mode == BinMode.APPEND),
        )
    elif protocol == "Trace" and bin_mode in (BinMode.AVERAGE, BinMode.FIRST):
        _validate_trace_protocol(
            acq_channel=acq_channel,
            acq_channels_data=acq_channels_data,
            loops=loops,
        )
        acq_channels_data[acq_channel] = AcquisitionChannelData(
            acq_index_dim_name=("acq_index_" + str(acq_channel)),
            protocol=protocol,
            bin_mode=bin_mode,
            coords=coords,
        )
    elif protocol == "TriggerCount" and bin_mode == BinMode.DISTRIBUTION:
        acq_channels_data[acq_channel] = AcquisitionChannelData(
            acq_index_dim_name=("acq_index_" + str(acq_channel)),
            protocol=protocol,
            bin_mode=bin_mode,
            coords=coords,
        )
    else:
        raise ValueError(
            f"Unsupported acquisition protocol '{protocol}' with bin mode '{bin_mode}' "
            f"on acq_channel '{acq_channel}'.",
        )


def _generate_acq_channels_data(
    operation: TimeableScheduleBase | Operation,
    acq_channels_data: AcquisitionChannelsData,
    schedulable_label_to_acq_index: SchedulableLabelToAcquisitionIndex,
    is_explicit_acq_index: bool,
    full_schedulable_label: FullSchedulableLabel,
    loops: list[LoopData],
) -> None:
    """
    Adds mappings to acq_channels_data and schedulable_label_to_acq_index;
    these are the output arguments; the others are input arguments.
    If explicit_acq_indices is True,
    then it only adds Schedulables where acq_index is not None,
    otherwise only adds Schedulables where acq_index is None.
    In this latter case, it will generate the acq_index.
    """
    if isinstance(operation, TimeableScheduleBase):
        sorted_schedulables = sorted(operation.schedulables.values(), key=lambda s: s["abs_time"])
        for schedulable in sorted_schedulables:
            schedulable_label = schedulable["name"]
            new_full_schedulable_label = full_schedulable_label + (schedulable_label,)
            inner_operation = operation.operations[schedulable["operation_id"]]
            _generate_acq_channels_data(
                operation=inner_operation,
                acq_channels_data=acq_channels_data,
                schedulable_label_to_acq_index=schedulable_label_to_acq_index,
                is_explicit_acq_index=is_explicit_acq_index,
                full_schedulable_label=new_full_schedulable_label,
                loops=loops,
            )
    elif isinstance(operation, LoopOperation):
        # For control flows, `None` signifies we refer to the `body` of the control flow.
        new_full_schedulable_label: FullSchedulableLabel = full_schedulable_label + (None,)
        repetitions: int = operation.data["control_flow_info"]["repetitions"]
        domain: dict[Variable, Domain] | None = operation.data["control_flow_info"]["domain"]
        new_loops: list[LoopData] = loops + [LoopData(repetitions, domain)]
        _generate_acq_channels_data(
            operation=operation.body,
            acq_channels_data=acq_channels_data,
            schedulable_label_to_acq_index=schedulable_label_to_acq_index,
            is_explicit_acq_index=is_explicit_acq_index,
            full_schedulable_label=new_full_schedulable_label,
            loops=new_loops,
        )
    elif isinstance(operation, ConditionalOperation):
        # For control flows, `None` signifies we refer to the `body` of the control flow.
        new_full_schedulable_label = full_schedulable_label + (None,)
        _generate_acq_channels_data(
            operation=operation.body,
            acq_channels_data=acq_channels_data,
            schedulable_label_to_acq_index=schedulable_label_to_acq_index,
            is_explicit_acq_index=is_explicit_acq_index,
            full_schedulable_label=new_full_schedulable_label,
            loops=loops,
        )
    elif operation.valid_acquisition:
        _generate_acq_channels_data_for_protocol(
            acq_info=operation.data["acquisition_info"],
            acq_channels_data=acq_channels_data,
            schedulable_label_to_acq_index=schedulable_label_to_acq_index,
            full_schedulable_label=full_schedulable_label,
            loops=loops,
            is_explicit_acq_index=is_explicit_acq_index,
        )


def _verify_shared_coords_key(acq_channels_data: AcquisitionChannelsData) -> None:
    """
    Checks if any two acquisition channels share the same coords keys.
    This is unsupported currently, see https://gitlab.com/quantify-os/quantify-scheduler/-/issues/497.
    """
    coords_keys: dict[Any, Hashable] = {}
    for acq_channel, data in acq_channels_data.items():
        keys = (
            {key for d in data.coords for key in d}
            if isinstance(data.coords, list)
            else set(data.coords.keys())
        )
        for key in keys:
            if (other_acq_channel := coords_keys.get(key)) is not None:
                warnings.warn(
                    (
                        f"The coords key `{key}` is shared between "
                        f"`{other_acq_channel}` and `{acq_channel}`. "
                        f"This is not yet fully supported, please try different keys. "
                        f"See https://gitlab.com/quantify-os/quantify-scheduler/-/issues/497."
                    ),
                )
            else:
                coords_keys[key] = acq_channel


def generate_acq_channels_data(
    schedule: TimeableScheduleBase,
) -> tuple[AcquisitionChannelsData, SchedulableLabelToAcquisitionIndex]:
    """
    Generate acq_index for every schedulable,
    and validate schedule regarding the acquisitions.

    This function generates the ``AcquisitionChannelData`` for every ``acq_channel``,
    and the ``SchedulableLabelToAcquisitionIndex``. It assumes the schedule is device-level.
    """
    acq_channels_data: AcquisitionChannelsData = {}
    schedulable_label_to_acq_index: SchedulableLabelToAcquisitionIndex = {}

    # First we generate all mappings for Schedulables
    # where acq_index is explicitly given.
    # In the next step we generate new acq_indices
    # and mapping for Schedulables where acq_index is None.
    #
    # The reason for this is that
    # *   for compatibility reasons, temporarily we'd like to allow users to explicitly specify
    #     acquisition index on the operation (the long-term intention is not to allow this,
    #     and only allow the compiler to generate an acquisition index itself), and
    # *   the acquisition mapping data stores each acquisition index in a list, and the list
    #     index is not stored explicitly (to store memory), only implicitly in the `coords` list.
    # Imagine the schedule: `Acq(acq_index=0); Acq(acq_index(acq_index=None); Acq(acq_index=1);`.
    # We choose the following convention: the acquisition indices start from 0, increment by 1, this
    # is a restriction **only** where the acquisition index is explicitly set by the user.
    # (We could have chosen a different convention, but probably for the user this is easier than
    # the other convention that the acquisition indices are incremented by one for all acquisitions,
    # even when the acquisition index is not explicitly specified by the user.)
    # Then, the only way to generate the acquisition mapping is by first iterating through the
    # acquisition operations where the acquisition index has been explicitly defined.
    _generate_acq_channels_data(
        schedule,
        acq_channels_data,
        schedulable_label_to_acq_index,
        is_explicit_acq_index=True,
        full_schedulable_label=(),
        loops=[],
    )
    _generate_acq_channels_data(
        schedule,
        acq_channels_data,
        schedulable_label_to_acq_index,
        is_explicit_acq_index=False,
        full_schedulable_label=(),
        loops=[],
    )

    _verify_shared_coords_key(acq_channels_data)

    return acq_channels_data, schedulable_label_to_acq_index
