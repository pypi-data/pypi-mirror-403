# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Contains the control flow operations for the Qblox backend."""

from __future__ import annotations

from qblox_scheduler.operations.control_flow_library import (
    ConditionalOperation as _ConditionalOperation,
)
from quantify_core.utilities import deprecated


@deprecated(
    drop_version="v2",
    message_or_alias="The hardware specific ConditionalOperation has been moved "
    "to qblox_scheduler.operations.conditional_operation",
)
class ConditionalOperation(_ConditionalOperation):  # noqa: D101
    pass
