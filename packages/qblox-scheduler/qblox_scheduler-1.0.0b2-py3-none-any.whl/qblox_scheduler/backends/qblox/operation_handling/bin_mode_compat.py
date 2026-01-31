# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Functionality to determine if the bin mode is compatible with the acquisition protocol."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qblox_scheduler.enums import BinMode

if TYPE_CHECKING:
    from qblox_scheduler.backends.types.qblox import OpInfo

QRM_COMPATIBLE_BIN_MODES = {
    "SSBIntegrationComplex": {BinMode.APPEND, BinMode.AVERAGE, BinMode.AVERAGE_APPEND},
    "Trace": {BinMode.AVERAGE},
    "ThresholdedAcquisition": {BinMode.APPEND, BinMode.AVERAGE, BinMode.AVERAGE_APPEND},
    "WeightedThresholdedAcquisition": {BinMode.APPEND, BinMode.AVERAGE, BinMode.AVERAGE_APPEND},
    "TriggerCount": {BinMode.APPEND, BinMode.SUM, BinMode.DISTRIBUTION, BinMode.AVERAGE_APPEND},
    "ThresholdedTriggerCount": {BinMode.APPEND, BinMode.AVERAGE_APPEND},
    "WeightedIntegratedSeparated": {BinMode.APPEND, BinMode.AVERAGE, BinMode.AVERAGE_APPEND},
    "NumericalSeparatedWeightedIntegration": {
        BinMode.APPEND,
        BinMode.AVERAGE,
        BinMode.AVERAGE_APPEND,
    },
    "NumericalWeightedIntegration": {BinMode.APPEND, BinMode.AVERAGE, BinMode.AVERAGE_APPEND},
}

QTM_COMPATIBLE_BIN_MODES = {
    "TriggerCount": {BinMode.APPEND, BinMode.SUM, BinMode.AVERAGE_APPEND},
    "ThresholdedTriggerCount": {BinMode.APPEND, BinMode.AVERAGE_APPEND},
    "DualThresholdedTriggerCount": {BinMode.APPEND, BinMode.AVERAGE_APPEND},
    "Timetag": {BinMode.APPEND, BinMode.AVERAGE, BinMode.AVERAGE_APPEND},
    "Trace": {BinMode.FIRST},
    "TimetagTrace": {BinMode.APPEND},
}


class IncompatibleBinModeError(Exception):
    """
    Compiler exception to be raised when a bin mode is incompatible with the acquisition protocol
    for the module type.
    """

    def __init__(
        self,
        module_type: str,
        protocol: str,
        bin_mode: BinMode,
        operation_info: OpInfo | None = None,
    ) -> None:
        err_msg = (
            f"{protocol} acquisition on the {module_type} does not support bin mode {bin_mode}."
        )
        if operation_info:
            err_msg += f"\n\n{operation_info!r} caused this exception to occur."
        super().__init__(err_msg)
