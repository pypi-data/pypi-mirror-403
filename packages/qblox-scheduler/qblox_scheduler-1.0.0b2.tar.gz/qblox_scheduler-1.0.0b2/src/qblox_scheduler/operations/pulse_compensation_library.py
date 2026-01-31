# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Pulse compensation operations for use with the qblox_scheduler."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qblox_scheduler.operations.operation import Operation

if TYPE_CHECKING:
    from collections.abc import Iterable

    from qblox_scheduler.schedule import Schedule
    from qblox_scheduler.schedules.schedule import TimeableSchedule

Port = str
"""Port on the hardware; this is an alias to str."""


class PulseCompensation(Operation):
    """
    Apply pulse compensation to an operation or schedule.

    Inserts a pulse at the end of the operation or schedule set in ``body`` for each port.
    The compensation pulses are calculated so that the integral of all pulses
    (including the compensation pulses) are zero for each port.
    Moreover, the compensating pulses are square pulses, and start just after the last
    pulse on each port individually, and their maximum amplitude is the one
    specified in the ``max_compensation_amp``. Their duration is divisible by ``duration_grid``.
    The clock is assumed to be the baseband clock; any other clock is not allowed.

    Parameters
    ----------
    body
        Operation to be pulse-compensated
    qubits
        For circuit-level operations, this is a list of device element names.
    max_compensation_amp
        Dictionary for each port the maximum allowed amplitude for the compensation pulse.
    time_grid
        Grid time of the duration of the compensation pulse.
    sampling_rate
        Sampling rate for pulse integration calculation.

    """

    def __init__(
        self,
        body: Operation | TimeableSchedule | Schedule,
        qubits: str | Iterable[str] | None = None,
        max_compensation_amp: dict[Port, float] | None = None,
        time_grid: float | None = None,
        sampling_rate: float | None = None,
    ) -> None:
        # Delayed to prevent circular imports
        from qblox_scheduler.schedules.schedule import TimeableSchedule

        if not isinstance(body, (Operation, TimeableSchedule)):
            timeable_schedule = body._timeable_schedule
            if timeable_schedule is None:
                raise ValueError(
                    "PulseCompensation can not be defined over schedules "
                    "that contain non-realtime operations"
                )
            assert isinstance(timeable_schedule, TimeableSchedule)
            body = timeable_schedule

        device_elements = qubits
        super().__init__(name="PulseCompensation")
        if device_elements is not None:
            if (
                max_compensation_amp is not None
                or time_grid is not None
                or sampling_rate is not None
            ):
                raise ValueError(
                    "PulseCompensation can only be defined on gate-level or device-level, "
                    "but not both. If 'qubit' is defined, then 'max_compensation_amp', "
                    "'time_grid' and 'sampling_rate' must be 'None'."
                )

            if isinstance(device_elements, str):
                device_elements = [device_elements]

            self.data.update(
                {
                    "pulse_compensation_info": {
                        "body": body,
                        "device_elements": device_elements,
                    },
                }
            )
        else:
            self.data.update(
                {
                    "pulse_compensation_info": {
                        "body": body,
                        "max_compensation_amp": max_compensation_amp,
                        "time_grid": time_grid,
                        "sampling_rate": sampling_rate,
                    },
                }
            )

    @property
    def body(self) -> Operation | TimeableSchedule:
        """Body of a pulse compensation."""
        return self.data["pulse_compensation_info"]["body"]

    @body.setter
    def body(self, value: Operation | TimeableSchedule) -> None:
        """Body of a pulse compensation."""
        self.data["pulse_compensation_info"]["body"] = value

    @property
    def max_compensation_amp(self) -> dict[Port, float]:
        """For each port the maximum allowed amplitude for the compensation pulse."""
        return self.data["pulse_compensation_info"]["max_compensation_amp"]

    @property
    def time_grid(self) -> float:
        """Grid time of the duration of the compensation pulse."""
        return self.data["pulse_compensation_info"]["time_grid"]

    @property
    def sampling_rate(self) -> float:
        """Sampling rate for pulse integration calculation."""
        return self.data["pulse_compensation_info"]["sampling_rate"]
