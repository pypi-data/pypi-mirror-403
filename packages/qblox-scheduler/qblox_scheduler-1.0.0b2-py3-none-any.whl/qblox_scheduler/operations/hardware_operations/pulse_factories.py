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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qblox_scheduler.operations.variables import Variable
import math
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np

from qblox_scheduler.backends.qblox import constants, helpers
from qblox_scheduler.operations import pulse_library
from qblox_scheduler.operations.expressions import DType
from qblox_scheduler.operations.loop_domains import linspace
from qblox_scheduler.resources import BasebandClockResource
from qblox_scheduler.schedules.schedule import TimeableSchedule

if TYPE_CHECKING:
    from qblox_scheduler.operations.variables import Variable


def long_square_pulse(
    amp: complex | Variable | Sequence[float | Variable],
    duration: float,
    port: str,
    clock: str = BasebandClockResource.IDENTITY,
    t0: float = 0,
    reference_magnitude: pulse_library.ReferenceMagnitude | None = None,
) -> TimeableSchedule:
    """
    Create a long square pulse using DC voltage offsets.

    .. warning::

        This function creates a
        :class:`~qblox_scheduler.schedules.schedule.TimeableSchedule`
        object, containing a combination of voltage offsets and waveforms. Overlapping
        Schedules with VoltageOffsets in time on the same port and clock may lead to unexpected
        results.

    Parameters
    ----------
    amp : float
        Amplitude of the envelope.
    duration : float
        The pulse duration in seconds.
    port : str
        Port of the pulse, must be capable of playing a complex waveform.
    clock : str, Optional
        Clock used to modulate the pulse. By default the baseband clock.
    t0 : float, Optional
        Time in seconds when to start the pulses relative to the start time
        of the Operation in the TimeableSchedule. By default 0.
    reference_magnitude : Optional
        Scaling value and unit for the unitless amplitude. Uses settings in
        hardware config if not provided.

    Returns
    -------
    TimeableSchedule
        A Schedule object containing an offset instruction with the specified
        amplitude.

    Raises
    ------
    ValueError
        When the duration of the pulse is not a multiple of ``grid_time_ns``.

    """
    if duration * 1e9 < constants.MIN_TIME_BETWEEN_OPERATIONS:
        raise ValueError(
            f"The duration of a long_square_pulse must be at least "
            f"{constants.MIN_TIME_BETWEEN_OPERATIONS} ns."
            f" Duration of offending operation: {duration}."
            f" Start time: {t0}"
        )

    if isinstance(amp, Sequence):
        amplitude_path_I = amp[0]
        amplitude_path_Q = amp[1]
    elif isinstance(amp, complex):
        amplitude_path_I = amp.real
        amplitude_path_Q = amp.imag
    else:
        amplitude_path_I = amp
        amplitude_path_Q = 0

    sched = TimeableSchedule(long_square_pulse.__name__)
    if duration > constants.MIN_TIME_BETWEEN_OPERATIONS * 1e-9:
        sched.add(
            pulse_library.VoltageOffset(
                offset_path_I=amplitude_path_I,
                offset_path_Q=amplitude_path_Q,
                port=port,
                clock=clock,
                reference_magnitude=reference_magnitude,
            ),
            rel_time=t0,
        )
        sched.add(
            pulse_library.VoltageOffset(
                offset_path_I=0.0,
                offset_path_Q=0.0,
                port=port,
                clock=clock,
                reference_magnitude=reference_magnitude,
            ),
            rel_time=duration - constants.MIN_TIME_BETWEEN_OPERATIONS * 1e-9,
        )
    sched.add(
        pulse_library.SquarePulse(
            amp=amp,
            duration=constants.MIN_TIME_BETWEEN_OPERATIONS * 1e-9,
            port=port,
            clock=clock,
            reference_magnitude=reference_magnitude,
        )
    )

    return sched


def long_chirp_pulse(
    amp: float,
    duration: float,
    port: str,
    start_freq: float,
    end_freq: float,
    clock: str = BasebandClockResource.IDENTITY,
    t0: float = 0,
    part_duration_ns: int = constants.STITCHED_PULSE_PART_DURATION_NS,
    reference_magnitude: pulse_library.ReferenceMagnitude | None = None,
) -> TimeableSchedule:
    """
    Create a long chirp pulse using SetClockFrequency.

    Parameters
    ----------
    amp : float
        Amplitude of the envelope.
    duration : float
        The pulse duration in seconds.
    port : str
        Port of the pulse, must be capable of playing a complex waveform.
    start_freq : float
        Start frequency of the Chirp. Note that this is the frequency at which the
        waveform is calculated, this may differ from the clock frequency.
    end_freq : float
        End frequency of the Chirp.
    clock : str, Optional
        Clock used to modulate the pulse. By default the baseband clock.
    t0 : float, Optional
        Time in seconds when to start the pulses relative to the start time
        of the Operation in the TimeableSchedule. By default 0.
    part_duration_ns : int, Optional
        Chunk size in nanoseconds.
    reference_magnitude : Optional
        Scaling value and unit for the unitless amplitude. Uses settings in
        hardware config if not provided.

    Returns
    -------
    TimeableSchedule
        A TimeableSchedule object describing a chirp pulse.

    Raises
    ------
    ValueError
        When the duration of the pulse is not a multiple of ``grid_time_ns``.

    """
    dur_ns = helpers.to_grid_time(duration)
    num_whole_parts = int(dur_ns / part_duration_ns)

    dur_left = dur_ns - num_whole_parts * part_duration_ns
    chunk_duration_sec = part_duration_ns * 1e-9

    schedule = TimeableSchedule("Long_Chirp_Pulse")
    current_freq = start_freq

    if num_whole_parts > 0:
        frequency_step = (end_freq - start_freq) / num_whole_parts
        phase_shift_rad = np.pi * frequency_step * chunk_duration_sec
        phase_shift_deg = np.rad2deg(phase_shift_rad) % 360
        chirp_pulse = pulse_library.ChirpPulse(
            amp=amp,
            duration=chunk_duration_sec,
            clock=clock,
            start_freq=0.0,
            end_freq=frequency_step,
            port=port,
            reference_magnitude=reference_magnitude,
        )

        for i in range(num_whole_parts):
            schedule.add(
                pulse_library.SetClockFrequency(
                    clock_freq_new=current_freq,
                    clock=clock,
                ),
                rel_time=t0 if i == 0 else 0,
            )

            schedule.add(chirp_pulse)

            schedule.add(
                pulse_library.ShiftClockPhase(
                    phase_shift=phase_shift_deg,
                    clock=clock,
                )
            )

            current_freq += frequency_step

    if dur_left > 0:
        # Final chunk is played with waveform again
        schedule.add(
            pulse_library.SetClockFrequency(
                clock_freq_new=start_freq,
                clock=clock,
            ),
            rel_time=t0 if num_whole_parts == 0 else 0,
        )

        schedule.add(
            pulse_library.ChirpPulse(
                amp=amp,
                duration=dur_left * 1e-9,
                clock=clock,
                start_freq=current_freq - start_freq,
                end_freq=end_freq - start_freq,
                port=port,
                reference_magnitude=reference_magnitude,
            )
        )

    # Reset to the initial clock.
    schedule.add(
        pulse_library.SetClockFrequency(
            clock_freq_new=None,
            clock=clock,
        )
    )

    return schedule


def staircase_pulse(
    start_amp: float,
    final_amp: float,
    num_steps: int,
    duration: float,
    port: str,
    clock: str = BasebandClockResource.IDENTITY,
    t0: float = 0,
    min_operation_time_ns: int = constants.MIN_TIME_BETWEEN_OPERATIONS,
    reference_magnitude: pulse_library.ReferenceMagnitude | None = None,
) -> TimeableSchedule:
    """
    Create a staircase-shaped pulse using DC voltage offsets.

    This function generates a real valued staircase pulse, which reaches its final
    amplitude in discrete steps. In between it will maintain a plateau.

    .. warning::

        This function creates a
        :class:`~qblox_scheduler.schedules.schedule.TimeableSchedule`
        object, containing a combination of voltage offsets and waveforms. Overlapping
        Schedules with VoltageOffsets in time on the same port and clock may lead to unexpected
        results.

    Parameters
    ----------
    start_amp : float
        Starting amplitude of the staircase envelope function.
    final_amp : float
        Final amplitude of the staircase envelope function.
    num_steps : int
        The number of plateaus.
    duration : float
        Duration of the pulse in seconds.
    port : str
        Port of the pulse.
    clock : str, Optional
        Clock used to modulate the pulse. By default the baseband clock.
    t0 : float, Optional
        Time in seconds when to start the pulses relative to the start time
        of the Operation in the TimeableSchedule. By default 0.
    min_operation_time_ns : int, Optional
        Min operation time in ns. The duration of the long_square_pulse must be a multiple
        of this. By default equal to the min operation time time of Qblox modules.
    reference_magnitude : Optional
        Scaling value and unit for the unitless amplitude. Uses settings in
        hardware config if not provided.

    Returns
    -------
    TimeableSchedule
        A Schedule object containing incrementing or decrementing offset
        instructions.

    Raises
    ------
    ValueError
        When the duration of a step is not a multiple of ``grid_time_ns``.

    """
    sched = TimeableSchedule(staircase_pulse.__name__)

    try:
        step_duration = helpers.to_grid_time(duration / num_steps, min_operation_time_ns) * 1e-9
    except ValueError as err:
        raise ValueError(
            f"The duration of each step of the staircase must be a multiple of"
            f" {min_operation_time_ns} ns."
        ) from err

    if num_steps == 0:
        raise ValueError("Cannot create a staircase pulse with 0 steps.")
    elif num_steps == 1:
        return long_square_pulse(
            amp=final_amp,
            duration=duration,
            port=port,
            clock=clock,
            t0=t0,
            reference_magnitude=reference_magnitude,
        )

    amp_step = (final_amp - start_amp) / (num_steps - 1)

    # The final step is a special case, see below.
    with sched.loop(
        linspace(start_amp, final_amp - amp_step, num_steps - 1, dtype=DType.AMPLITUDE), rel_time=t0
    ) as amp:
        sched.add(
            pulse_library.VoltageOffset(
                offset_path_I=amp,
                offset_path_Q=0.0,
                port=port,
                clock=clock,
                reference_magnitude=reference_magnitude,
            )
        )
        sched.add(pulse_library.IdlePulse(step_duration))

    # The final step is an offset with the last part (of duration 'grid time' ns)
    # replaced by a pulse. The offset is set back to 0 before the pulse, because the
    # Qblox backend might otherwise lengthen the full operation by adding an
    # 'UpdateParameters' instruction at the end.
    sched.add(
        pulse_library.VoltageOffset(
            offset_path_I=final_amp,
            offset_path_Q=0.0,
            port=port,
            clock=clock,
            reference_magnitude=reference_magnitude,
        )
    )
    sched.add(
        pulse_library.VoltageOffset(
            offset_path_I=0.0,
            offset_path_Q=0.0,
            port=port,
            clock=clock,
            reference_magnitude=reference_magnitude,
        ),
        rel_time=step_duration - min_operation_time_ns * 1e-9,
    )
    sched.add(
        pulse_library.SquarePulse(
            amp=final_amp,
            duration=min_operation_time_ns * 1e-9,
            port=port,
            clock=clock,
            reference_magnitude=reference_magnitude,
        )
    )

    return sched


def long_ramp_pulse(
    amp: float,
    duration: float,
    port: str,
    offset: float = 0,
    clock: str = BasebandClockResource.IDENTITY,
    t0: float = 0,
    part_duration_ns: int = constants.STITCHED_PULSE_PART_DURATION_NS,
    reference_magnitude: pulse_library.ReferenceMagnitude | None = None,
) -> TimeableSchedule:
    """
    Creates a long ramp pulse by stitching together shorter ramps.

    This function creates a long ramp pulse by stitching together ramp pulses of the
    specified duration ``part_duration_ns``, with DC voltage offset instructions placed
    in between.

    .. warning::

        This function creates a
        :class:`~qblox_scheduler.schedules.schedule.TimeableSchedule`
        object, containing a combination of voltage offsets and waveforms. Overlapping
        Schedules with VoltageOffsets in time on the same port and clock may lead to unexpected
        results.

    Parameters
    ----------
    amp : float
        Amplitude of the ramp envelope function.
    duration : float
        The pulse duration in seconds.
    port : str
        Port of the pulse.
    offset : float, Optional
        Starting point of the ramp pulse. By default 0.
    clock : str, Optional
        Clock used to modulate the pulse, by default the baseband clock.
    t0 : float, Optional
        Time in seconds when to start the pulses relative to the start time of the
        Operation in the TimeableSchedule. By default 0.
    part_duration_ns : int, Optional
        Duration of each partial ramp in nanoseconds, by default
        :class:`~qblox_scheduler.backends.qblox.constants.STITCHED_PULSE_PART_DURATION_NS`.
    reference_magnitude : Optional
        Scaling value and unit for the unitless amplitude. Uses settings in
        hardware config if not provided.

    Returns
    -------
    TimeableSchedule
        A ``TimeableSchedule`` composed of shorter ramp pulses with varying DC offsets,
        forming one long ramp pulse.

    """
    dur_ns = helpers.to_grid_time(duration)
    num_whole_parts = (dur_ns - 1) // part_duration_ns
    amp_part = part_duration_ns / dur_ns * amp
    dur_left = (dur_ns - num_whole_parts * part_duration_ns) * 1e-9
    amp_left = amp - num_whole_parts * amp_part

    sched = TimeableSchedule(long_ramp_pulse.__name__)

    if num_whole_parts > 0:
        with sched.loop(
            linspace(
                offset,
                offset + (num_whole_parts - 1) * amp_part,
                num_whole_parts,
                dtype=DType.AMPLITUDE,
            ),
            rel_time=t0,
        ) as offset_part:
            sched.add(
                pulse_library.VoltageOffset(
                    offset_path_I=offset_part,
                    offset_path_Q=0.0,
                    port=port,
                    clock=clock,
                    reference_magnitude=reference_magnitude,
                )
            )
            sched.add(
                pulse_library.RampPulse(
                    amp=amp_part,
                    duration=part_duration_ns * 1e-9,
                    port=port,
                    clock=clock,
                    reference_magnitude=reference_magnitude,
                )
            )

    last_sample_voltage = offset + num_whole_parts * amp_part

    # For the final part, the voltage offset is set to 0, because the Qblox
    # backend might otherwise lengthen the full operation by adding an
    # 'UpdateParameters' instruction at the end.

    # Insert a 0 offset if offsets were inserted above and the last offset is not 0.
    if not math.isclose(last_sample_voltage, offset) and not math.isclose(
        last_sample_voltage - amp_part, 0.0
    ):
        sched.add(
            pulse_library.VoltageOffset(
                offset_path_I=0.0,
                offset_path_Q=0.0,
                port=port,
                clock=clock,
                reference_magnitude=reference_magnitude,
            )
        )
    sched.add(
        pulse_library.RampPulse(
            amp=amp_left,
            offset=last_sample_voltage,
            duration=dur_left,
            port=port,
            clock=clock,
            reference_magnitude=reference_magnitude,
        )
    )

    return sched
