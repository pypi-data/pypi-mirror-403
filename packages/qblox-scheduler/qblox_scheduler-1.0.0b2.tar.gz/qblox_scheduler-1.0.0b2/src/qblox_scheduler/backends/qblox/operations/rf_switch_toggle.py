# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Module that contains the RFSwitchToggle operation."""

from qblox_scheduler.operations.hardware_operations.pulse_library import (
    RFSwitchToggle as RFSwitchToggle_,
)
from quantify_core.utilities import deprecated


@deprecated(
    drop_version="v2",
    message_or_alias="long_ramp_pulse has been moved "
    "to qblox_scheduler.operations.hardware_operations.pulse_library",
)
class RFSwitchToggle(RFSwitchToggle_):  # noqa: D101
    pass
