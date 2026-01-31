# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Contains the gate library for the Qblox backend."""

from __future__ import annotations

from qblox_scheduler.operations.conditional_reset import ConditionalReset as ConditionalResetDepr
from quantify_core.utilities.deprecation import deprecated


@deprecated("v2", "ConditionalReset has been moved to qblox_scheduler.operations")
class ConditionalReset(ConditionalResetDepr):  # noqa: D101
    pass
