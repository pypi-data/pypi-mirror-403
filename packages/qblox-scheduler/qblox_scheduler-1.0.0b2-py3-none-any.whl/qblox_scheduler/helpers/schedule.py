# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Schedule helper functions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qblox_scheduler.enums import BinMode
from qblox_scheduler.helpers.collections import make_hash, without
from qblox_scheduler.operations.control_flow_library import ControlFlowOperation
from qblox_scheduler.schedules.schedule import TimeableScheduleBase

if TYPE_CHECKING:
    from qblox_scheduler.operations.operation import Operation
    from qblox_scheduler.schedules.schedule import TimeableSchedule


def get_pulse_uuid(pulse_info: dict[str, Any], excludes: list[str] | None = None) -> int:
    """
    Return an unique identifier for a pulse.

    Parameters
    ----------
    pulse_info
        The pulse information dictionary.
    excludes
        A list of keys to exclude.

    Returns
    -------
    :
        The uuid hash.

    """
    if excludes is None:
        excludes = ["t0"]

    return make_hash(without(pulse_info, excludes))


def get_acq_uuid(acq_info: dict[str, Any]) -> int:
    """
    Return an unique identifier for a acquisition protocol.

    Parameters
    ----------
    acq_info
        The acquisition information dictionary.

    Returns
    -------
    :
        The uuid hash.

    """
    return make_hash(without(acq_info, ["t0", "waveforms"]))


def _generate_acq_info_by_uuid(
    operation: Operation | TimeableScheduleBase, acqid_acqinfo_dict: dict
) -> None:
    if isinstance(operation, TimeableScheduleBase):
        for schedulable in operation.schedulables.values():
            inner_operation = operation.operations[schedulable["operation_id"]]
            _generate_acq_info_by_uuid(inner_operation, acqid_acqinfo_dict)
    elif isinstance(operation, ControlFlowOperation):
        _generate_acq_info_by_uuid(operation.body, acqid_acqinfo_dict)
    elif acq_info := operation["acquisition_info"]:
        acq_id = get_acq_uuid(acq_info)
        if acq_id not in acqid_acqinfo_dict:
            # Unique acquisition info already populated in the dictionary.
            acqid_acqinfo_dict[acq_id] = acq_info


def get_acq_info_by_uuid(schedule: TimeableSchedule) -> dict[int, dict[str, Any]]:
    """
    Return a lookup dictionary of unique identifiers of acquisition information.

    Parameters
    ----------
    schedule
        The schedule.

    """
    acqid_acqinfo_dict: dict[int, dict[str, Any]] = {}
    _generate_acq_info_by_uuid(schedule, acqid_acqinfo_dict)

    return acqid_acqinfo_dict


def _is_acquisition_binned_average(protocol: str, bin_mode: BinMode) -> bool:
    return (
        protocol
        in (
            "SSBIntegrationComplex",
            "WeightedIntegratedSeparated",
            "NumericalSeparatedWeightedIntegration",
            "NumericalWeightedIntegration",
            "ThresholdedAcquisition",
            "WeightedThresholdedAcquisition",
            "Timetag",
        )
        and bin_mode == BinMode.AVERAGE
    ) or (
        protocol
        in (
            "TriggerCount",
            "ThresholdedTriggerCount",
        )
        and bin_mode == BinMode.SUM
    )


def _is_acquisition_binned_append(protocol: str, bin_mode: BinMode) -> bool:
    return (
        protocol
        in (
            "SSBIntegrationComplex",
            "WeightedIntegratedSeparated",
            "NumericalSeparatedWeightedIntegration",
            "NumericalWeightedIntegration",
            "ThresholdedAcquisition",
            "WeightedThresholdedAcquisition",
            "Timetag",
            "TriggerCount",
            "ThresholdedTriggerCount",
            "DualThresholdedTriggerCount",
        )
        and bin_mode == BinMode.APPEND
    )


def _is_acquisition_binned_average_append(protocol: str, bin_mode: BinMode) -> bool:
    return (
        protocol
        in (
            "SSBIntegrationComplex",
            "WeightedIntegratedSeparated",
            "NumericalSeparatedWeightedIntegration",
            "NumericalWeightedIntegration",
            "ThresholdedAcquisition",
            "WeightedThresholdedAcquisition",
            "Timetag",
            "TriggerCount",
            "ThresholdedTriggerCount",
            "DualThresholdedTriggerCount",
        )
        and bin_mode == BinMode.AVERAGE_APPEND
    )
