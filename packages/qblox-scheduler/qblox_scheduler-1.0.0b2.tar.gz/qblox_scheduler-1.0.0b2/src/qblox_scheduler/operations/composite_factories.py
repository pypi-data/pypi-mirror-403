# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""A module containing factory functions for composite gates, which are replaced by schedules."""

from qblox_scheduler.operations.gate_library import CZ, Y90, H, Z
from qblox_scheduler.schedules.schedule import TimeableSchedule


def hadamard_as_y90z(
    qubit: str,
) -> TimeableSchedule:
    """
    Generate a :class:`~.schedules.schedule.TimeableSchedule` Y90 * Z
    (equivalent to a Hadamard gate).

    Parameters
    ----------
    qubit
        Device element to which the Hadamard gate is applied.

    Returns
    -------
    :
        TimeableSchedule.

    """
    device_element = qubit
    schedule = TimeableSchedule("Hadamard")
    schedule.add(Z(device_element))
    schedule.add(Y90(device_element))
    return schedule


def cnot_as_h_cz_h(
    control_qubit: str,
    target_qubit: str,
) -> TimeableSchedule:
    """
    Generate a :class:`~.schedules.schedule.TimeableSchedule` for a CNOT gate using a CZ gate
    interleaved with Hadamard gates on the target qubit.

    Parameters
    ----------
    control_qubit
        Qubit acting as the control qubit.
    target_qubit
        Qubit acting as the target qubit.

    Returns
    -------
    TimeableSchedule
        TimeableSchedule for the CNOT gate.

    """
    schedule = TimeableSchedule("CNOT")
    schedule.add(H(target_qubit))
    schedule.add(CZ(control_qubit, target_qubit))
    schedule.add(H(target_qubit))
    return schedule
