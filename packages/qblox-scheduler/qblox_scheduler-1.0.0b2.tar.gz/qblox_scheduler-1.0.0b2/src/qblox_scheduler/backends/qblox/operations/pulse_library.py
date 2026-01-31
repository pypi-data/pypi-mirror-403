# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Standard pulse-level operations for use with the qblox_scheduler."""

from __future__ import annotations

from qblox_scheduler.operations.hardware_operations.pulse_library import LatchReset as LatchReset_
from qblox_scheduler.operations.hardware_operations.pulse_library import (
    SimpleNumericalPulse as SimpleNumericalPulse_,
)
from quantify_core.utilities import deprecated


@deprecated(
    drop_version="v2",
    message_or_alias="LatchReset has been moved "
    "to qblox_scheduler.operations.hardware_operations.pulse_library",
)
class LatchReset(LatchReset_):  # noqa: D101
    pass


@deprecated(
    drop_version="v2",
    message_or_alias="SimpleNumericalPulse has been moved "
    "to qblox_scheduler.operations.hardware_operations.pulse_library",
)
class SimpleNumericalPulse(SimpleNumericalPulse_):  # noqa: D101
    pass
