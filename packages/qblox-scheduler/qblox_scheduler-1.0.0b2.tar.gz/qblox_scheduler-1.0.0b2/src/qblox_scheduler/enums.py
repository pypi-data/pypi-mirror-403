# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Enums for qblox-scheduler."""

from enum import Enum, unique
from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class StrEnum(str, Enum):
    """Enum that can be directly serialized to string."""

    def __str__(self) -> str:
        # Needs to be implemented for compatibility with qcodes cache.
        return str(self.value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        """
        Add a 'before' validator to the core schema.

        This validator uses the enum's constructor to coerce values.
        """
        # Get the default schema that Pydantic would generate
        default_schema = handler(source_type)

        # Wrap it with a 'before' validator
        return core_schema.no_info_before_validator_function(
            cls,  # The function to call is the enum constructor itself
            default_schema,
        )


@unique
class BinMode(StrEnum):  # type: ignore
    """
    Describes how to handle `Acquisitions` that write to the same `AcquisitionIndex`.

    A BinMode is a property of an `AcquisitionChannel` that describes how to
    handle multiple
    :class:`~qblox_scheduler.operations.acquisition_library.Acquisition` s
    that write data to the same `AcquisitionIndex` on a channel.

    The most common use-case for this is when iterating over multiple
    repetitions of a :class:`~qblox_scheduler.schedules.schedule.TimeableSchedule`
    When the BinMode is set to `APPEND` new entries will be added as a list
    along the `repetitions` dimension.

    When the BinMode is set to `AVERAGE` the outcomes are averaged together
    into one value.

    Note that not all `AcquisitionProtocols` and backends support all possible
    BinModes. For more information, please see the :ref:`sec-acquisition-protocols`
    reference guide and some of the Qblox-specific :ref:`acquisition details
    <sec-qblox-acquisition-details>`.
    """

    APPEND = "append"
    AVERAGE = "average"
    AVERAGE_APPEND = "average_append"
    """Averages over the schedule's repetition, appends over loops."""
    FIRST = "first"
    DISTRIBUTION = "distribution"
    SUM = "sum"
    # N.B. in principle it is possible to specify other behaviours for
    # BinMode such as `SUM` or `OVERWRITE` but these are not
    # currently supported by any backend.


class TimeSource(StrEnum):  # type: ignore
    """
    Selects the timetag data source for timetag (trace) acquisitions.

    See :class:`~qblox_scheduler.operations.acquisition_library.Timetag` and
    :class:`~qblox_scheduler.operations.acquisition_library.TimetagTrace`.
    """

    FIRST = "first"
    SECOND = "second"
    LAST = "last"


class TimeRef(StrEnum):  # type: ignore
    """
    Selects the event that counts as a time reference (i.e. t=0) for timetags.

    See :class:`~qblox_scheduler.operations.acquisition_library.Timetag` and
    :class:`~qblox_scheduler.operations.acquisition_library.TimetagTrace`.
    """

    START = "start"
    END = "end"
    FIRST = "first"
    TIMESTAMP = "timestamp"
    PORT = "port"


class TriggerCondition(StrEnum):  # type: ignore
    """Comparison condition for the thresholded trigger count acquisition."""

    LESS_THAN = "less_than"
    GREATER_THAN_EQUAL_TO = "greater_than_equal_to"


class DualThresholdedTriggerCountLabels(StrEnum):  # type: ignore
    """
    All suffixes for the feedback trigger labels that can be used by
    DualThresholdedTriggerCount.
    """

    LOW = "low"
    MID = "mid"
    HIGH = "high"
    INVALID = "invalid"


class SchedulingStrategy(StrEnum):
    """Default scheduling strategy to use when no timing constraints are defined."""

    ASAP = "asap"
    ALAP = "alap"
