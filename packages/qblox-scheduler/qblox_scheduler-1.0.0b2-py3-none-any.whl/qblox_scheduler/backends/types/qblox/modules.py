# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Python dataclasses for compilation to Qblox hardware."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Annotated, Literal, Optional, Union, get_args

from pydantic import Field

from qblox_scheduler.structure.model import DataStructure

from .channels import ComplexChannelDescription, DigitalChannelDescription, RealChannelDescription

if TYPE_CHECKING:
    from collections.abc import Iterable


class _ModuleDescriptionBase(abc.ABC, DataStructure):
    """Provide the functionality of retrieving valid channel names by inheriting this class."""

    @classmethod
    def get_valid_channels(cls) -> list[str]:
        """Return all the valid channel names for this hardware description."""
        channel_description_types = [
            ComplexChannelDescription.__name__,
            RealChannelDescription.__name__,
            DigitalChannelDescription.__name__,
        ]

        channel_names = []
        for description_name, description_type in cls.__annotations__.items():
            for channel_description_type in channel_description_types:
                if channel_description_type in description_type:
                    channel_names.append(description_name)
                    break

        return channel_names

    @classmethod
    def get_instrument_type(cls) -> str:
        """Return the instrument type indicated in this hardware description."""
        return get_args(cls.model_fields["instrument_type"].annotation)[0]  # type: ignore

    @classmethod
    def validate_channel_names(cls, channel_names: Iterable[str]) -> None:
        """Validate channel names specified in the Connectivity."""
        valid_names = cls.get_valid_channels()
        for name in channel_names:
            if name not in valid_names:
                raise ValueError(
                    "Invalid channel name specified for module of type "
                    f"{cls.get_instrument_type()}: {name}"
                )


class QRMDescription(_ModuleDescriptionBase):
    """
    Information needed to specify a QRM in the
    :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.
    """

    instrument_type: Literal["QRM"] = "QRM"
    """The instrument type of this module."""
    sequence_to_file: bool = False
    """Write sequencer programs to files, for this module."""
    complex_output_0: Optional[ComplexChannelDescription] = None
    """Description of the complex output channel on this QRM, corresponding to ports O1 and O2."""
    complex_input_0: Optional[ComplexChannelDescription] = None
    """Description of the complex input channel on this QRM, corresponding to ports I1 and I2."""
    real_output_0: Optional[RealChannelDescription] = None
    """Description of the real output channel on this QRM, corresponding to port O1."""
    real_output_1: Optional[RealChannelDescription] = None
    """Description of the real output channel on this QRM, corresponding to port O2."""
    real_input_0: Optional[RealChannelDescription] = None
    """Description of the real input channel on this QRM, corresponding to port I1."""
    real_input_1: Optional[RealChannelDescription] = None
    """Description of the real output channel on this QRM, corresponding to port I2."""
    digital_output_0: Optional[DigitalChannelDescription] = None
    """Description of the digital (marker) output channel on this QRM, corresponding to port M1."""
    digital_output_1: Optional[DigitalChannelDescription] = None
    """Description of the digital (marker) output channel on this QRM, corresponding to port M2."""
    digital_output_2: Optional[DigitalChannelDescription] = None
    """Description of the digital (marker) output channel on this QRM, corresponding to port M3."""
    digital_output_3: Optional[DigitalChannelDescription] = None
    """Description of the digital (marker) output channel on this QRM, corresponding to port M4."""


class QCMDescription(_ModuleDescriptionBase):
    """
    Information needed to specify a QCM in the
    :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.
    """

    instrument_type: Literal["QCM"] = "QCM"
    """The instrument type of this module."""
    sequence_to_file: bool = False
    """Write sequencer programs to files, for this module."""
    complex_output_0: Optional[ComplexChannelDescription] = None
    """Description of the complex output channel on this QCM, corresponding to ports O1 and O2."""
    complex_output_1: Optional[ComplexChannelDescription] = None
    """Description of the complex output channel on this QCM, corresponding to ports O3 and O4."""
    real_output_0: Optional[RealChannelDescription] = None
    """Description of the real output channel on this QCM, corresponding to port O1."""
    real_output_1: Optional[RealChannelDescription] = None
    """Description of the real output channel on this QCM, corresponding to port O2."""
    real_output_2: Optional[RealChannelDescription] = None
    """Description of the real output channel on this QCM, corresponding to port O3."""
    real_output_3: Optional[RealChannelDescription] = None
    """Description of the real output channel on this QCM, corresponding to port O4."""
    digital_output_0: Optional[DigitalChannelDescription] = None
    """Description of the digital (marker) output channel on this QCM, corresponding to port M1."""
    digital_output_1: Optional[DigitalChannelDescription] = None
    """Description of the digital (marker) output channel on this QCM, corresponding to port M2."""
    digital_output_2: Optional[DigitalChannelDescription] = None
    """Description of the digital (marker) output channel on this QCM, corresponding to port M3."""
    digital_output_3: Optional[DigitalChannelDescription] = None
    """Description of the digital (marker) output channel on this QCM, corresponding to port M4."""


class RFDescription(_ModuleDescriptionBase):
    """User settings for QCM-RF and QRM-RF radio frequency (RF) modules."""

    sequence_to_file: bool = False
    """Write sequencer programs to files, for this module."""
    rf_output_on: bool | Literal["auto"] = True
    """Whether the RF outputs of this module are always on by default.\n
    If set to False they can be turned on by using the
    :class:`~.qblox_scheduler.operations.hardware_operations.pulse_library.RFSwitchToggle`
    operation for QRM-RF and QCM-RF.\n
    If set to "auto", compiler will automatically infer when outputs need to be on,
    and insert operations accordingly.
    """


class QRMRFDescription(RFDescription):
    """
    Information needed to specify a QRM-RF in the
    :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.
    """

    instrument_type: Literal["QRM_RF"] = "QRM_RF"
    """The instrument type of this module."""
    complex_output_0: Optional[ComplexChannelDescription] = None
    """Description of the complex output channel on this QRM-RF, corresponding to port O1."""
    complex_input_0: Optional[ComplexChannelDescription] = None
    """Description of the complex input channel on this QRM-RF, corresponding to port I1."""
    digital_output_0: Optional[DigitalChannelDescription] = None
    """Description of the digital (marker) output channel on this QRM-RF,
    corresponding to port M1.
    """
    digital_output_1: Optional[DigitalChannelDescription] = None
    """Description of the digital (marker) output channel on this QRM-RF,
    corresponding to port M2.
    """


class QRCDescription(_ModuleDescriptionBase):
    """
    Information needed to specify a QRC in the
    :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.
    """

    instrument_type: Literal["QRC"] = "QRC"
    """The instrument type of this module."""
    sequence_to_file: bool = False
    """Write sequencer programs to files, for this module."""
    complex_output_0: Optional[ComplexChannelDescription] = None
    """Description of the complex output channel on this QRC, corresponding to port O1."""
    complex_output_1: Optional[ComplexChannelDescription] = None
    """Description of the complex output channel on this QRC, corresponding to port O2."""
    complex_output_2: Optional[ComplexChannelDescription] = None
    """Description of the complex output channel on this QRC, corresponding to port O3."""
    complex_output_3: Optional[ComplexChannelDescription] = None
    """Description of the complex output channel on this QRC, corresponding to port O4."""
    complex_output_4: Optional[ComplexChannelDescription] = None
    """Description of the complex output channel on this QRC, corresponding to port O5."""
    complex_output_5: Optional[ComplexChannelDescription] = None
    """Description of the complex output channel on this QRC, corresponding to port O6."""
    complex_input_0: Optional[ComplexChannelDescription] = None
    """Description of the complex input channel on this QRC, corresponding to port I1."""
    complex_input_1: Optional[ComplexChannelDescription] = None
    """Description of the complex input channel on this QRC, corresponding to port I2."""
    digital_output_0: Optional[DigitalChannelDescription] = None
    """Description of the digital (marker) output channel on this QRC, corresponding to port M1."""


class QCMRFDescription(RFDescription):
    """
    Information needed to specify a QCM-RF in the
    :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.
    """

    instrument_type: Literal["QCM_RF"] = "QCM_RF"
    """The instrument type of this module."""
    complex_output_0: Optional[ComplexChannelDescription] = None
    """Description of the complex output channel on this QCM-RF, corresponding to port O1."""
    complex_output_1: Optional[ComplexChannelDescription] = None
    """Description of the complex output channel on this QCM-RF, corresponding to port O2."""
    digital_output_0: Optional[DigitalChannelDescription] = None
    """Description of the digital (marker) output channel on this QCM-RF,
    corresponding to port M1.
    """
    digital_output_1: Optional[DigitalChannelDescription] = None
    """Description of the digital (marker) output channel on this QCM-RF,
    corresponding to port M2.
    """


class QTMDescription(_ModuleDescriptionBase):
    """
    Information needed to specify a QTM in the
    :class:`~.qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.
    """

    instrument_type: Literal["QTM"] = "QTM"
    """The instrument type of this module."""
    sequence_to_file: bool = False
    """Write sequencer programs to files, for this module."""
    digital_input_0: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 1, specified as input."""
    digital_input_1: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 2, specified as input."""
    digital_input_2: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 3, specified as input."""
    digital_input_3: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 4, specified as input."""
    digital_input_4: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 5, specified as input."""
    digital_input_5: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 6, specified as input."""
    digital_input_6: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 7, specified as input."""
    digital_input_7: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 8, specified as input."""
    digital_output_0: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 1, specified as output."""
    digital_output_1: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 2, specified as output."""
    digital_output_2: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 3, specified as output."""
    digital_output_3: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 4, specified as output."""
    digital_output_4: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 5, specified as output."""
    digital_output_5: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 6, specified as output."""
    digital_output_6: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 7, specified as output."""
    digital_output_7: Optional[DigitalChannelDescription] = None
    """Description of the digital channel corresponding to port 8, specified as output."""

    @classmethod
    def validate_channel_names(cls, channel_names: Iterable[str]) -> None:
        """Validate channel names specified in the Connectivity."""
        super().validate_channel_names(channel_names)

        used_inputs = {int(n.removeprefix("digital_input_")) for n in channel_names if "input" in n}
        used_outputs = {
            int(n.removeprefix("digital_output_")) for n in channel_names if "output" in n
        }

        if overlap := used_inputs & used_outputs:
            raise ValueError(
                "The configuration for the QTM module contains channel names with port "
                "numbers that are assigned as both input and output. This is not "
                "allowed. Conflicting channel names:\n"
                + "\n".join(f"digital_input_{n}\ndigital_output_{n}" for n in overlap)
            )


class QSMDescription(_ModuleDescriptionBase):
    """
    Information needed to specify a QSM in the
    :class:`~.quantify_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`.
    """

    instrument_type: Literal["QSM"] = "QSM"
    """The instrument type of this module."""
    sequence_to_file: bool = False
    """Write sequencer programs to files, for this module."""


ClusterModuleDescription = Annotated[
    Union[
        QRMDescription,
        QCMDescription,
        QRMRFDescription,
        QRCDescription,
        QCMRFDescription,
        QTMDescription,
        QSMDescription,
    ],
    Field(discriminator="instrument_type"),
]
"""
Specifies a Cluster module and its instrument-specific settings.

The supported instrument types are:
:class:`~.QRMDescription`,
:class:`~.QCMDescription`,
:class:`~.QRMRFDescription`,
:class:`~.QRCDescription`,
:class:`~.QCMRFDescription`,
:class:`~.QTMDescription`,
:class:`~.QSMDescription`,
"""


__all__ = [
    "ClusterModuleDescription",
    "QCMDescription",
    "QCMRFDescription",
    "QRCDescription",
    "QRMDescription",
    "QRMRFDescription",
    "QSMDescription",
    "QTMDescription",
    "RFDescription",
]
