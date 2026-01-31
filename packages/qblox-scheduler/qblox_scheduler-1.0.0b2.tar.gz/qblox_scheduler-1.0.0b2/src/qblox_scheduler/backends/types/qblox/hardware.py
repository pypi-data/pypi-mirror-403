# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Python dataclasses for compilation to Qblox hardware."""

# ruff: noqa: TC001

from __future__ import annotations

from dataclasses import field as dataclasses_field
from typing import Annotated, Literal, Optional, Union

from pydantic import Field

from qblox_scheduler.backends.types.common import (
    HardwareDescription,
    IQMixerDescription,
    LocalOscillatorDescription,
    OpticalModulatorDescription,
)

from .modules import ClusterModuleDescription
from .settings import ExternalTriggerSyncSettings


class QbloxBaseDescription(HardwareDescription):
    """Base class for a Qblox hardware description."""

    ref: Literal["internal", "external"]
    """The reference source for the instrument."""
    sequence_to_file: bool = False
    """Write sequencer programs to files for (all modules in this) instrument."""


class ClusterDescription(QbloxBaseDescription):
    """Information needed to specify a Cluster in the :class:`~.CompilationConfig`."""

    instrument_type: Literal["Cluster"] = "Cluster"  # type: ignore  # (valid override)
    """The instrument type, used to select this datastructure
    when parsing a :class:`~.CompilationConfig`."""
    modules: dict[int, ClusterModuleDescription] = dataclasses_field(default_factory=dict)
    """Description of the modules of this Cluster, using slot index as key."""
    ip: Optional[str] = None
    """Unique identifier (typically the ip address) used to connect to the cluster"""
    sync_on_external_trigger: Optional[ExternalTriggerSyncSettings] = None
    """Settings for synchronizing the cluster on an external trigger."""


QbloxHardwareDescription = Annotated[
    Union[
        ClusterDescription,
        LocalOscillatorDescription,
        IQMixerDescription,
        OpticalModulatorDescription,
    ],
    Field(discriminator="instrument_type"),
]
"""
Specifies a piece of Qblox hardware and its instrument-specific settings.
"""


__all__ = ["ClusterDescription", "QbloxBaseDescription", "QbloxHardwareDescription"]
