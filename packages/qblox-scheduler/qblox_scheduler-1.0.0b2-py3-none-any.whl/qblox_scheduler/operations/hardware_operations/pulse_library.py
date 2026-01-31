# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.

"""Standard pulse-level operations for use with the qblox_scheduler."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from qblox_scheduler.backends.qblox import constants
from qblox_scheduler.operations.operation import Operation
from qblox_scheduler.operations.pulse_library import (
    NumericalPulse,
    ReferenceMagnitude,
)
from qblox_scheduler.resources import BasebandClockResource

if TYPE_CHECKING:
    from collections.abc import Sequence

    from operations.expressions import Expression


class LatchReset(Operation):
    """
    Operation that resets the feedback trigger addresses from the hardware.

    Currently only implemented for Qblox backend, refer to
    :class:`~qblox_scheduler.backends.qblox.operation_handling.virtual.ResetFeedbackTriggersStrategy`
    for more details.
    """

    def __init__(
        self,
        portclock: tuple[str, str],
        t0: float = 0,
        duration: float = 4e-9,
    ) -> None:
        super().__init__(name=self.__class__.__name__)
        self.data["pulse_info"] = {
            "name": self.__class__.__name__,
            "wf_func": None,
            "t0": t0,
            "port": portclock[0],
            "clock": portclock[1],
            "duration": duration,
        }

    def __str__(self) -> str:
        pulse_info = self.data["pulse_info"]
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"t0='{pulse_info['t0']}', "
            f"port='{pulse_info['port']}'"
            f"clock='{pulse_info['clock']}'"
            f"duration='{pulse_info['duration']}'"
            f")"
        )


class SimpleNumericalPulse(NumericalPulse):
    """
    Wrapper on top of NumericalPulse to provide a simple interface for creating a pulse
    where the samples correspond 1:1 to the produced waveform, without needing to specify
    the time samples.


    Parameters
    ----------
    samples
        An array of (possibly complex) values specifying the shape of the pulse.
    port
        The port that the pulse should be played on.
    clock
        Clock used to (de)modulate the pulse.
        By default the baseband clock.
    gain
        Gain factor between -1 and 1 that multiplies with the samples, by default 1.
    reference_magnitude
        Scaling value and unit for the unitless samples. Uses settings in
        hardware config if not provided.
    t0
        Time in seconds when to start the pulses relative to the start time
        of the Operation in the TimeableSchedule.


    Example
    -------

    .. jupyter-execute::

        from qblox_scheduler.operations.hardware_operations.pulse_library import (
            SimpleNumericalPulse
        )
        from qblox_scheduler import TimeableSchedule

        waveform = [0.1,0.2,0.2,0.3,0.5,0.4]

        schedule = TimeableSchedule("")
        schedule.add(SimpleNumericalPulse(waveform, port="q0:out"))


    """

    def __init__(
        self,
        samples: np.ndarray | list,
        port: str,
        clock: str = BasebandClockResource.IDENTITY,
        gain: complex | float | Expression | Sequence[complex | float | Expression] = 1,
        reference_magnitude: ReferenceMagnitude | None = None,
        t0: float = 0,
    ) -> None:
        # Append samples with one value which will be truncated away by the interpolation.
        samples = np.append(samples, 0)

        t_samples = np.arange(len(samples)) / constants.SAMPLING_RATE

        super().__init__(
            samples=samples,
            t_samples=t_samples,
            port=port,
            clock=clock,
            gain=gain,
            reference_magnitude=reference_magnitude,
            t0=t0,
            interpolation="linear",
        )


class RFSwitchToggle(Operation):
    """
    Turn the RF complex output on for the given duration.
    The RF ports are on by default, make sure to set
    :attr:`~.qblox_scheduler.backends.types.qblox.RFDescription.rf_output_on`
    to `False` to turn them off.

    Parameters
    ----------
    duration
        Duration to turn the RF output on.
    port
        Name of the associated port.
    clock
        Name of the associated clock.
        For now the given port-clock combination must
        have a LO frequency defined in the hardware configuration.

    Examples
    --------
    Partial hardware configuration to turn the RF complex output off by default
    to be able to use this operation.

    .. code-block:: python

        hardware_compilation_config = {
            "config_type": QbloxHardwareCompilationConfig,
            "hardware_description": {
                "cluster0": {
                    "instrument_type": "Cluster",
                    "modules": {
                        "0": {"instrument_type": "QCM_RF", "rf_output_on": False},
                        "1": {"instrument_type": "QRM_RF", "rf_output_on": False},
                    },
                },
            },
        }

    """

    def __init__(
        self,
        duration: float,
        port: str,
        clock: str,
    ) -> None:
        super().__init__(name=self.__class__.__name__)
        self.data["pulse_info"] = {
            "wf_func": None,
            "marker_pulse": True,  # This distinguishes MarkerPulse from other operations
            "t0": 0,
            "clock": clock,
            "port": port,
            "duration": duration,
        }

    def __str__(self) -> str:
        pulse_info = self.data["pulse_info"]
        return self._get_signature(pulse_info)
