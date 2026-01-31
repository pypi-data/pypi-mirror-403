# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""
Module containing factory functions for pulses on the quantum-device layer.

These factories take a parametrized representation of an operation and create an
instance of the operation itself. The created operations make use of Qblox-specific
hardware features.
"""

from __future__ import annotations

from qblox_scheduler.operations.hardware_operations.pulse_factories import (
    long_ramp_pulse as long_ramp_pulse_,
)
from qblox_scheduler.operations.hardware_operations.pulse_factories import (
    long_square_pulse as long_square_pulse_,
)
from qblox_scheduler.operations.hardware_operations.pulse_factories import (
    staircase_pulse as staircase_pulse_,
)
from quantify_core.utilities import deprecated


@deprecated(
    drop_version="v2",
    message_or_alias="long_square_pulse has been moved "
    "to qblox_scheduler.operations.hardware_operations",
)
def long_square_pulse(*args, **kwargs):  # noqa: ANN201, D103
    return long_square_pulse_(*args, **kwargs)


@deprecated(
    drop_version="v2",
    message_or_alias="long_ramp_pulse has been moved "
    "to qblox_scheduler.operations.hardware_operations",
)
def long_ramp_pulse(*args, **kwargs):  # noqa: ANN201, D103
    return long_ramp_pulse_(*args, **kwargs)


@deprecated(
    drop_version="v2",
    message_or_alias="long_ramp_pulse has been moved "
    "to qblox_scheduler.operations.hardware_operations",
)
def staircase_pulse(*args, **kwargs):  # noqa: ANN201, D103
    return staircase_pulse_(*args, **kwargs)
