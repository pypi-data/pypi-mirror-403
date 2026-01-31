# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Qblox-specific operation which can be used to inject Q1ASM directly into a TimeableSchedule."""

from __future__ import annotations

from qblox_scheduler.operations.hardware_operations import InlineQ1ASM as InlineQ1ASM_
from quantify_core.utilities import deprecated


@deprecated(
    drop_version="v2",
    message_or_alias="InlineQ1ASM operation has been moved "
    "to qblox_scheduler.operations.hardware_operations",
)
class InlineQ1ASM(InlineQ1ASM_):  # noqa: D101
    pass
