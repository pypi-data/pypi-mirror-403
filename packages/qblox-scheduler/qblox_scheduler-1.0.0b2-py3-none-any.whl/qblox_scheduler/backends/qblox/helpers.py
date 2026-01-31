# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Helper functions for Qblox backend."""

from __future__ import annotations

import math
import warnings
from copy import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from qblox_scheduler.backends.qblox import constants
from qblox_scheduler.backends.types.qblox import (
    BoundedParameter,
    OpInfo,
)
from qblox_scheduler.helpers.waveforms import exec_waveform_function
from qblox_scheduler.operations.control_flow_library import (
    ConditionalOperation,
    ControlFlowOperation,
    LoopOperation,
)
from qblox_scheduler.operations.hardware_operations.inline_q1asm import (
    InlineQ1ASM,
    Q1ASMOpInfo,
)
from qblox_scheduler.operations.operation import Operation
from qblox_scheduler.operations.pulse_library import WindowOperation
from qblox_scheduler.schedules.schedule import TimeableSchedule, TimeableScheduleBase

if TYPE_CHECKING:
    from qblox_scheduler.backends.qblox.instrument_compilers import ClusterCompiler
    from qblox_scheduler.helpers.generate_acq_channels_data import (
        FullSchedulableLabel,
        SchedulableLabelToAcquisitionIndex,
    )
    from qblox_scheduler.operations.loop_domains import LinearDomain
    from qblox_scheduler.operations.variables import Variable


def generate_waveform_data(
    data_dict: dict, sampling_rate: float, duration: float | None = None
) -> np.ndarray:
    """
    Generates an array using the parameters specified in ``data_dict``.

    Parameters
    ----------
    data_dict : dict
        The dictionary that contains the values needed to parameterize the
        waveform. ``data_dict['wf_func']`` is then called to calculate the values.
    sampling_rate : float
        The sampling rate used to generate the time axis values.
    duration : float or None, Optional
        The duration of the waveform in seconds. This parameter can be used if
        ``data_dict`` does not contain a ``'duration'`` key. By default None.

    Returns
    -------
    wf_data : np.ndarray
        The (possibly complex) values of the generated waveform. The number of values is
        determined by rounding to the nearest integer.

    Raises
    ------
    TypeError
        If ``data_dict`` does not contain a ``'duration'`` entry and ``duration is
        None``.

    """
    try:
        duration_validated = duration or data_dict["duration"]
    except KeyError as exc:
        raise TypeError(
            "Parameter 'duration' has value None. If 'data_dict' does not contain "
            "'duration', the function parameter can be used instead."
        ) from exc

    num_samples = round(duration_validated * sampling_rate)
    t = np.arange(start=0, stop=num_samples, step=1) / sampling_rate

    wf_data = exec_waveform_function(wf_func=data_dict["wf_func"], t=t, pulse_info=data_dict)

    return wf_data


def generate_waveform_names_from_uuid(uuid: object) -> tuple[str, str]:
    """
    Generates names for the I and Q parts of the complex waveform based on a unique
    identifier for the pulse/acquisition.

    Parameters
    ----------
    uuid
        A unique identifier for a pulse/acquisition.

    Returns
    -------
    uuid_I:
        Name for the I waveform.
    uuid_Q:
        Name for the Q waveform.

    """
    return f"{uuid!s}_I", f"{uuid!s}_Q"


def generate_uuid_from_wf_data(wf_data: np.ndarray, decimals: int = 12) -> str:
    """
    Creates a unique identifier from the waveform data, using a hash. Identical arrays
    yield identical strings within the same process.

    Parameters
    ----------
    wf_data:
        The data to generate the unique id for.
    decimals:
        The number of decimal places to consider.

    Returns
    -------
    :
        A unique identifier.

    """
    waveform_hash = hash(wf_data.round(decimals=decimals).tobytes())
    return str(waveform_hash)


def add_to_wf_dict_if_unique(wf_dict: dict[str, Any], waveform: np.ndarray) -> int:
    """
    Adds a waveform to the waveform dictionary if it is not yet in there and returns the
    uuid and index. If it is already present it simply returns the uuid and index.

    Parameters
    ----------
    wf_dict:
        The waveform dict in the format expected by the sequencer.
    waveform:
        The waveform to add.

    Returns
    -------
    dict[str, Any]
        The (updated) wf_dict.
    str
        The uuid of the waveform.
    int
        The index.

    """

    def generate_entry(name: str, data: np.ndarray, idx: int) -> dict[str, Any]:
        return {name: {"data": data.tolist(), "index": idx}}

    def find_first_free_wf_index() -> int:
        index = 0
        reserved_indices = [wf_dict[uuid]["index"] for uuid in wf_dict]
        while index in reserved_indices:
            index += 1
        return index

    if not np.isrealobj(waveform):
        raise RuntimeError("This function only accepts real arrays.")

    uuid = generate_uuid_from_wf_data(waveform)
    if uuid in wf_dict:
        index: int = wf_dict[uuid]["index"]
    else:
        index: int = find_first_free_wf_index()
        wf_dict.update(generate_entry(uuid, waveform, index))
    return index


def generate_waveform_dict(waveforms_complex: dict[str, np.ndarray]) -> dict[str, dict]:
    """
    Takes a dictionary with complex waveforms and generates a new dictionary with
    real valued waveforms with a unique index, as required by the hardware.

    Parameters
    ----------
    waveforms_complex
        Dictionary containing the complex waveforms. Keys correspond to a unique
        identifier, value is the complex waveform.

    Returns
    -------
    dict[str, dict]
        A dictionary with as key the unique name for that waveform, as value another
        dictionary containing the real-valued data (list) as well as a unique index.
        Note that the index of the Q waveform is always the index of the I waveform
        +1.


    .. admonition:: Examples

        .. jupyter-execute::

            import numpy as np
            from qblox_scheduler.backends.qblox.helpers import generate_waveform_dict

            complex_waveforms = {12345: np.array([1, 2])}
            generate_waveform_dict(complex_waveforms)

            # {'12345_I': {'data': [1, 2], 'index': 0},
            # '12345_Q': {'data': [0, 0], 'index': 1}}

    """
    wf_dict = {}
    for idx, (uuid, complex_data) in enumerate(waveforms_complex.items()):
        name_i, name_q = generate_waveform_names_from_uuid(uuid)
        to_add = {
            name_i: {"data": complex_data.real.tolist(), "index": 2 * idx},
            name_q: {"data": complex_data.imag.tolist(), "index": 2 * idx + 1},
        }
        wf_dict.update(to_add)
    return wf_dict


def to_grid_time(time: float, grid_time_ns: int = constants.GRID_TIME) -> int:
    """
    Convert time value in s to time in ns, and verify that it is aligned with grid time.

    Takes a float value representing a time in seconds as used by the schedule, and
    returns the integer valued time in nanoseconds that the sequencer uses.

    The time value needs to be aligned with grid time, i.e., needs to be a multiple
    of :data:`~.constants.GRID_TIME`, within a tolerance of 1 picosecond.

    Parameters
    ----------
    time
        A time value in seconds.
    grid_time_ns
        The grid time to use in nanoseconds.

    Returns
    -------
    :
        The integer valued nanosecond time.

    Raises
    ------
    ValueError
        If ``time`` is not a multiple of :data:`~.constants.GRID_TIME` within the tolerance.

    """
    time_ns_float = time * 1e9
    time_ns = round(time_ns_float)

    tolerance = constants.GRID_TIME_TOLERANCE_TIME
    if (
        not math.isclose(
            time_ns_float, time_ns, abs_tol=tolerance, rel_tol=0
        )  # rel_tol=0 results in: abs(a-b) <= max(0, abs_tol)
        or time_ns % grid_time_ns != 0
    ):
        raise ValueError(
            f"Attempting to use a time value of {time_ns_float} ns."
            f" Please ensure that the durations of operations and wait times between"
            f" operations are multiples of {grid_time_ns} ns"
            f" (tolerance: {tolerance:.0e} ns). If you think this is a mistake, try "
            "increasing the tolerance by setting e.g.:"
            f" `qblox_scheduler.backends.qblox.constants.GRID_TIME_TOLERANCE_TIME = 0.1e-3` "
            "at the top of your script."
        )

    return time_ns


def is_multiple_of_grid_time(time: float, grid_time_ns: int = constants.GRID_TIME) -> bool:
    """
    Determine whether a time value in seconds is a multiple of the grid time.

    Within a tolerance as defined by
    :meth:`~qblox_scheduler.backends.qblox.helpers.to_grid_time`.

    Parameters
    ----------
    time
        A time value in seconds.
    grid_time_ns
        The grid time to use in nanoseconds.

    Returns
    -------
    :
        ``True`` if ``time`` is a multiple of the grid time, ``False`` otherwise.

    """
    try:
        _ = to_grid_time(time=time, grid_time_ns=grid_time_ns)
    except ValueError:
        return False

    return True


def get_nco_phase_arguments(phase_deg: float) -> int:
    """
    Converts a phase in degrees to the int arguments the NCO phase instructions expect.
    We take ``phase_deg`` modulo 360 to account for negative phase and phase larger than
    360.

    Parameters
    ----------
    phase_deg
        The phase in degrees

    Returns
    -------
    :
        The int corresponding to the phase argument.

    """
    phase_deg %= 360
    return round(phase_deg * constants.NCO_PHASE_STEPS_PER_DEG)


def get_nco_set_frequency_arguments(frequency_hz: float) -> int:
    """
    Converts a frequency in Hz to the int argument the NCO set_freq instruction expects.

    Parameters
    ----------
    frequency_hz
        The frequency in Hz.

    Returns
    -------
    :
        The frequency expressed in steps for the NCO set_freq instruction.

    Raises
    ------
    ValueError
        If the frequency_hz is out of range.

    """
    frequency_steps = round(frequency_hz * constants.NCO_FREQ_STEPS_PER_HZ)

    if (
        frequency_steps < -constants.NCO_FREQ_LIMIT_STEPS
        or frequency_steps > constants.NCO_FREQ_LIMIT_STEPS
    ):
        min_max_frequency_in_hz = constants.NCO_FREQ_LIMIT_STEPS / constants.NCO_FREQ_STEPS_PER_HZ
        raise ValueError(
            f"Attempting to set NCO frequency. "
            f"The frequency must be between and including "
            f"-{min_max_frequency_in_hz:e} Hz and {min_max_frequency_in_hz:e} Hz. "
            f"Got {frequency_hz:e} Hz."
        )

    return frequency_steps


@dataclass
class Frequencies:
    """Holds and validates frequencies."""

    clock: float
    LO: float | None = None
    IF: float | None = None

    def __post_init__(self) -> None:
        if self.clock is None or math.isnan(self.clock):
            raise ValueError(f"Clock frequency must be specified ({self.clock=}).")
        if self.LO is not None and math.isnan(self.LO):
            self.LO = None
        if self.IF is not None and math.isnan(self.IF):
            self.IF = None


@dataclass(frozen=True)
class ValidatedFrequencies:
    """Simple dataclass that holds immutable frequencies after validation."""

    clock: float
    LO: float
    IF: float


def determine_clock_lo_interm_freqs(
    freqs: Frequencies,
    downconverter_freq: float | None = None,
    mix_lo: bool | None = True,
) -> ValidatedFrequencies:
    r"""
    From known frequency for the local oscillator or known intermodulation frequency,
    determine any missing frequency, after optionally applying ``downconverter_freq`` to
    the clock frequency.

    If ``mix_lo`` is ``True``, the following relation is obeyed:
    :math:`f_{RF} = f_{LO} + f_{IF}`.

    If ``mix_lo`` is ``False``, :math:`f_{RF} = f_{LO}` is upheld.

    .. warning::
        Using ``downconverter_freq`` requires custom Qblox hardware, do not use otherwise.

    Parameters
    ----------
    freqs : Frequencies
        Frequencies object containing clock, local oscillator (LO) and
        Intermodulation frequency (IF), the frequency of the numerically controlled
        oscillator (NCO).
    downconverter_freq : Optional[float]
        Frequency for downconverting the clock frequency, using:
        :math:`f_\mathrm{out} = f_\mathrm{downconverter} - f_\mathrm{in}`.
    mix_lo : bool
        Flag indicating whether IQ mixing is enabled with the LO.

    Returns
    -------
    :
        :class:`.ValidatedFrequencies` object containing the determined LO and IF
        frequencies and the optionally downconverted clock frequency.

    Warns
    -----
    RuntimeWarning
        In case ``downconverter_freq`` is set equal to 0, warns to unset via
        ``null``/``None`` instead.
    RuntimeWarning
        In case LO is overridden to clock due to ``mix_lo`` being `False`

    Raises
    ------
    ValueError
        In case ``downconverter_freq`` is less than 0.
    ValueError
        In case ``downconverter_freq`` is less than ``clock_freq``.
    ValueError
        In case ``mix_lo`` is ``True`` and neither LO frequency nor IF has been supplied.
    ValueError
        In case ``mix_lo`` is ``True`` and both LO frequency
        and IF have been supplied and do not adhere to
        :math:`f_{RF} = f_{LO} + f_{IF}`.

    """

    def _downconvert_clock(downconverter_freq: float, clock_freq: float) -> float:
        if downconverter_freq == 0:
            warnings.warn(
                "Downconverter frequency 0 supplied. To unset 'downconverter_freq', "
                "set to `null` (json) / `None` instead in hardware configuration.",
                RuntimeWarning,
            )

        if downconverter_freq < 0:
            raise ValueError(f"Downconverter frequency must be positive ({downconverter_freq=:e})")

        if downconverter_freq < clock_freq:
            raise ValueError(
                f"Downconverter frequency must be greater than clock frequency "
                f"({downconverter_freq=:e}, {clock_freq=:e})"
            )

        return downconverter_freq - clock_freq

    if downconverter_freq is not None:
        freqs.clock = _downconvert_clock(
            downconverter_freq=downconverter_freq,
            clock_freq=freqs.clock,
        )
    if not mix_lo:
        if freqs.LO is not None and not math.isclose(freqs.LO, freqs.clock):
            warnings.warn(f"Overriding {freqs.LO=} to {freqs.clock=} due to mix_lo=False.")
        freqs.LO = freqs.clock
        if freqs.IF is None:
            raise ValueError(
                f"Frequency settings underconstrained for {freqs.clock=}. "
                "If mix_lo=False is specified, the IF must also be supplied "
                f"({freqs.IF=})."
            )
    elif freqs.LO is None and freqs.IF is None:
        raise ValueError(
            f"Frequency settings underconstrained for {freqs.clock=}."
            f" Neither LO nor IF supplied ({freqs.LO=}, {freqs.IF=})."
        )
    elif freqs.LO is not None and freqs.IF is not None:
        if not math.isclose(freqs.LO + freqs.IF, freqs.clock):
            raise ValueError(
                f"Frequency settings overconstrained."
                f" {freqs.clock=} must be equal to "
                f"{freqs.LO=}+{freqs.IF=} when both are supplied."
            )
    elif freqs.LO is None and freqs.IF is not None:
        freqs.LO = freqs.clock - freqs.IF
    elif freqs.LO is not None and freqs.IF is None:
        freqs.IF = freqs.clock - freqs.LO

    return ValidatedFrequencies(clock=freqs.clock, LO=freqs.LO, IF=freqs.IF)  # type: ignore


def generate_port_clock_to_device_map(
    device_compilers: dict[str, Any],
) -> dict[str, str]:
    """
    Generates a mapping that specifies which port-clock combinations belong to which
    device.

    Here, device means a top-level entry in the hardware config, e.g. a Cluster,
    not which module within the Cluster.

    Each port-clock combination may only occur once.

    Parameters
    ----------
    device_compilers:
        Dictionary containing compiler configs.


    Returns
    -------
    :
        A dictionary with as key a tuple representing a port-clock combination, and
        as value the name of the device. Note that multiple port-clocks may point to
        the same device.

    Raises
    ------
    ValueError
        If a port-clock combination occurs multiple times in the hardware configuration.

    """
    portclock_map = {}
    for device_name, device_compiler in device_compilers.items():
        if hasattr(device_compiler, "portclock_to_path"):
            for portclock in device_compiler.portclock_to_path:
                portclock_map[portclock] = device_name

    return portclock_map


class LoopBegin(Operation):
    """
    Operation to indicate the beginning of a loop.

    Parameters
    ----------
    repetitions : int
        number of repetitions
    t0 : float, Optional
        time offset, by default 0

    """

    def __init__(
        self, repetitions: int, t0: float = 0, domain: dict[Variable, LinearDomain] | None = None
    ) -> None:
        super().__init__(name="Loop")
        self.data.update(
            {
                "name": "Loop",
                "control_flow_info": {
                    "t0": t0,
                    "repetitions": repetitions,
                    "domain": domain,
                },
            }
        )

    def __str__(self) -> str:
        """
        Represent the Operation as string.

        Returns
        -------
        str
            description

        """
        return self._get_signature(self.data["control_flow_info"])


class ConditionalBegin(Operation):
    """
    Operation to indicate the beginning of a conditional.

    Parameters
    ----------
    qubit_name
        The name of the device element to condition on.
    feedback_trigger_address
        Feedback trigger address
    t0
        Time offset, by default 0


    """

    def __init__(
        self,
        qubit_name: str,
        feedback_trigger_address: int,
        feedback_trigger_invert: bool,
        feedback_trigger_count: int,
        t0: float,
    ) -> None:
        class_name = self.__class__.__name__
        super().__init__(name=class_name)
        self.data.update(
            {
                "name": class_name,
                "control_flow_info": {
                    "qubit_name": qubit_name,
                    "t0": t0,
                    "feedback_trigger_address": feedback_trigger_address,
                    "feedback_trigger_invert": feedback_trigger_invert,
                    "feedback_trigger_count": feedback_trigger_count,
                },
            }
        )

    def __str__(self) -> str:
        """
        Represent the Operation as string.

        Returns
        -------
        str
            The string representation of this operation.

        """
        return self._get_signature(self.data["control_flow_info"])


def _get_control_flow_begins(
    control_flow_operation: ControlFlowOperation,
) -> list[Operation]:
    assert isinstance(control_flow_operation, (LoopOperation, ConditionalOperation))

    port_clocks = control_flow_operation.get_used_port_clocks()
    if isinstance(control_flow_operation, LoopOperation):
        begin_operation: Operation = LoopBegin(
            control_flow_operation.repetitions,
            control_flow_operation.data["control_flow_info"]["t0"],
            control_flow_operation.domain,
        )
    else:
        begin_operation = ConditionalBegin(
            qubit_name=control_flow_operation.data["control_flow_info"]["qubit_name"],
            feedback_trigger_address=control_flow_operation.data["control_flow_info"][
                "feedback_trigger_address"
            ],
            feedback_trigger_invert=control_flow_operation.data["control_flow_info"][
                "feedback_trigger_invert"
            ],
            feedback_trigger_count=control_flow_operation.data["control_flow_info"][
                "feedback_trigger_count"
            ],
            t0=control_flow_operation.data["control_flow_info"]["t0"],
        )

    operations = []
    for port, clock in port_clocks:
        op = copy(begin_operation)
        op["pulse_info"] = {
            "wf_func": None,
            "clock": clock,
            "port": port,
            "duration": 0,
            "control_flow_begin": True,
            **begin_operation["control_flow_info"],
        }
        operations.append(op)
    return operations


class _ControlFlowReturn(Operation):
    """
    An operation that signals the end of the current control flow statement.

    Cannot be added to TimeableSchedule manually.

    Parameters
    ----------
    t0 : float, Optional
        time offset, by default 0

    """

    def __init__(self, t0: float = 0) -> None:
        super().__init__(name="ControlFlowReturn")
        self.data.update(
            {
                "name": "ControlFlowReturn",
                "control_flow_info": {
                    "t0": t0,
                    "duration": 0.0,
                    "return_stack": True,
                },
            }
        )

    def __str__(self) -> str:
        return self._get_signature(self.data["control_flow_info"])


def _get_control_flow_ends(
    control_flow_operation: ControlFlowOperation,
) -> list[Operation]:
    assert isinstance(control_flow_operation, (LoopOperation, ConditionalOperation))

    port_clocks = control_flow_operation.get_used_port_clocks()
    end_operation: Operation = _ControlFlowReturn()
    operations = []
    for port, clock in port_clocks:
        op = copy(end_operation)
        op["pulse_info"] = {
            "wf_func": None,
            "clock": clock,
            "port": port,
            "duration": 0,
            "control_flow_end": True,
            **end_operation["control_flow_info"],
        }
        operations.append(op)
    return operations


def _get_list_of_operations_for_op_info_creation(
    operation: Operation | TimeableSchedule,
    time_offset: float,
    accumulator: list[tuple[float, Operation, FullSchedulableLabel]],
    full_schedulable_label: FullSchedulableLabel,
) -> None:
    if isinstance(operation, TimeableScheduleBase):
        for schedulable in operation.schedulables.values():
            abs_time = schedulable["abs_time"]
            inner_operation = operation.operations[schedulable["operation_id"]]
            schedulable_label = schedulable["name"]
            new_full_schedulable_label = full_schedulable_label + (schedulable_label,)
            _get_list_of_operations_for_op_info_creation(
                inner_operation,
                time_offset + abs_time,
                accumulator,
                new_full_schedulable_label,
            )
    elif isinstance(operation, ControlFlowOperation):
        accumulator.extend(
            [
                (
                    to_grid_time(time_offset) * 1e-9,
                    op,
                    full_schedulable_label + (None,),
                )
                for op in _get_control_flow_begins(operation)
            ]
        )
        new_full_schedulable_label = full_schedulable_label + (None,)
        _get_list_of_operations_for_op_info_creation(
            operation.body,
            time_offset,
            accumulator,
            new_full_schedulable_label,
        )
        assert operation.body.duration is not None
        accumulator.extend(
            [
                (
                    to_grid_time(time_offset + operation.body.duration) * 1e-9,
                    op,
                    full_schedulable_label + (None,),
                )
                for op in _get_control_flow_ends(operation)
            ]
        )
    else:
        accumulator.append(
            (
                to_grid_time(time_offset) * 1e-9,
                operation,
                full_schedulable_label,
            )
        )


def _assign_pulse_info_to_devices(
    device_compilers: dict[str, ClusterCompiler],
    portclock_mapping: dict[str, str],
    name: str,
    pulse_info: dict[str, Any],
    operation_start_time: float,
) -> None:
    if "t0" in pulse_info:
        pulse_start_time = operation_start_time + pulse_info["t0"]
    else:
        pulse_start_time = operation_start_time
    # Check whether start time aligns with grid time
    try:
        _ = to_grid_time(pulse_start_time)
    except ValueError as exc:
        raise ValueError(
            f"An operation start time of {pulse_start_time * 1e9} ns does not "
            f"align with a grid time of {constants.GRID_TIME} ns. Please make "
            f"sure the start time of all operations is a multiple of "
            f"{constants.GRID_TIME} ns."
        ) from exc

    if pulse_info.get("reference_magnitude") is not None:
        warnings.warn(
            "reference_magnitude parameter not implemented. This parameter will be ignored.",
            RuntimeWarning,
        )

    port = pulse_info["port"]
    clock = pulse_info["clock"]
    portclock = f"{port}-{clock}"

    combined_data = OpInfo(
        name=name,
        data=pulse_info,
        timing=pulse_start_time,
    )

    if port is None:
        # Distribute clock operations to all sequencers utilizing that clock
        for map_portclock, device_name in portclock_mapping.items():
            map_port, map_clock = map_portclock.split("-")
            if (combined_data.name == "LatchReset") or map_clock == clock:
                device_compilers[device_name].add_op_info(
                    port=map_port, clock=map_clock, op_info=combined_data
                )
    else:
        if portclock not in portclock_mapping:
            raise KeyError(
                f"Could not assign pulse data to device. The combination "
                f"of port {port} and clock {clock} could not be found "
                f"in hardware configuration.\n\nAre both the port and clock "
                f"specified in the hardware configuration?\n\n"
                f"Relevant operation:\n{combined_data}."
            )
        device_name = portclock_mapping[portclock]
        device_compilers[device_name].add_op_info(port=port, clock=clock, op_info=combined_data)


def _assign_acq_info_to_devices(
    device_compilers: dict[str, ClusterCompiler],
    portclock_mapping: dict[str, str],
    name: str,
    acquisition_info: dict[str, Any],
    operation_start_time: float,
    schedulable_label_to_acq_index: SchedulableLabelToAcquisitionIndex,
    optional_full_schedulable_label: FullSchedulableLabel,
) -> None:
    if "t0" in acquisition_info:
        acq_start_time = operation_start_time + acquisition_info["t0"]
    else:
        acq_start_time = operation_start_time

    port = acquisition_info["port"]
    clock = acquisition_info["clock"]
    portclock = f"{port}-{clock}"

    if port is None:
        return

    # Each operation with the same acq_data reference
    # can have different acq_index, so we need to copy it,
    # and override the acq_index. No need to deepcopy, only changing top level value.
    new_acq_data = copy(acquisition_info)
    new_acq_data["acq_index"] = schedulable_label_to_acq_index.get(optional_full_schedulable_label)
    combined_data = OpInfo(
        name=name,
        data=new_acq_data,
        timing=acq_start_time,
    )

    if portclock not in portclock_mapping:
        raise KeyError(
            f"Could not assign acquisition data to device. The combination "
            f"of port {port} and clock {clock} could not be found "
            f"in hardware configuration.\n\nAre both the port and clock "
            f"specified in the hardware configuration?\n\n"
            f"Relevant operation:\n{combined_data}."
        )
    device_name = portclock_mapping[portclock]
    device_compilers[device_name].add_op_info(port=port, clock=clock, op_info=combined_data)


def _assign_asm_info_to_devices(
    device_compilers: dict[str, ClusterCompiler],
    portclock_mapping: dict[str, str],
    operation: InlineQ1ASM,
    op_start_time: float,
) -> None:
    portclock = f"{operation.port}-{operation.clock}"

    operation_info = Q1ASMOpInfo(operation, op_start_time)

    if portclock not in portclock_mapping:
        raise KeyError(
            f"Could not assign Q1ASM program to the device. "
            f"The combination of port {operation.port} and clock {operation.clock} "
            f"could not be found "
            f"in hardware configuration."
            f"\n\nAre both the port and clock specified in the hardware configuration?\n\n"
            f"Relevant operation:\n{operation}."
        )

    device_name = portclock_mapping[portclock]
    device_compilers[device_name].add_op_info(
        port=operation.port, clock=operation.clock, op_info=operation_info
    )


def assign_pulse_and_acq_info_to_devices(
    schedule: TimeableSchedule,
    device_compilers: dict[str, ClusterCompiler],
    schedulable_label_to_acq_index: SchedulableLabelToAcquisitionIndex,
) -> None:
    """
    Traverses the schedule and generates `OpInfo` objects for every pulse and
    acquisition, and assigns it to the correct `ClusterCompiler`.

    Parameters
    ----------
    schedule
        The schedule to extract the pulse and acquisition info from.
    device_compilers
        Dictionary containing InstrumentCompilers as values and their names as keys.
    schedulable_label_to_acq_index
        Schedulable label to acquisition indices dictionary for binned acquisitions.

    Raises
    ------
    RuntimeError
        This exception is raised then the function encountered an operation that has no
        pulse or acquisition info assigned to it.
    KeyError
        This exception is raised when attempting to assign a pulse with a port-clock
        combination that is not defined in the hardware configuration.
    KeyError
        This exception is raised when attempting to assign an acquisition with a
        port-clock combination that is not defined in the hardware configuration.

    """
    portclock_mapping = generate_port_clock_to_device_map(device_compilers)

    list_of_operations: list[tuple[float, Operation, FullSchedulableLabel]] = []
    _get_list_of_operations_for_op_info_creation(schedule, 0, list_of_operations, ())
    list_of_operations.sort(key=lambda abs_time_and_op: abs_time_and_op[0])

    for operation_start_time, operation, optional_full_schedulable_label in list_of_operations:
        assert isinstance(operation, Operation)

        if isinstance(operation, WindowOperation):
            continue

        if (
            not operation.valid_pulse
            and not operation.valid_acquisition
            and not isinstance(operation, InlineQ1ASM)
        ):
            raise RuntimeError(
                f"Operation is not a valid pulse, acquisition or Q1ASM. "
                f"Please check whether the device compilation has been performed successfully. "
                f"Operation data: {operation!r}"
            )

        if isinstance(operation, InlineQ1ASM):
            _assign_asm_info_to_devices(
                device_compilers=device_compilers,
                portclock_mapping=portclock_mapping,
                operation=operation,
                op_start_time=operation_start_time,
            )
        try:
            if operation.data["pulse_info"]:
                _assign_pulse_info_to_devices(
                    device_compilers=device_compilers,
                    portclock_mapping=portclock_mapping,
                    name=operation.name,
                    pulse_info=operation.data["pulse_info"],
                    operation_start_time=operation_start_time,
                )
            if operation.data["acquisition_info"]:
                _assign_acq_info_to_devices(
                    device_compilers=device_compilers,
                    portclock_mapping=portclock_mapping,
                    name=operation.name,
                    acquisition_info=operation.data["acquisition_info"],
                    operation_start_time=operation_start_time,
                    schedulable_label_to_acq_index=schedulable_label_to_acq_index,
                    optional_full_schedulable_label=optional_full_schedulable_label,
                )
        except Exception as exc:
            raise ValueError(f"Error in {operation!r}") from exc


def calc_from_units_volt(
    voltage_range: BoundedParameter, name: str, param_name: str, offset: float | None
) -> float | None:
    """
    Helper method to calculate the offset from mV or V.
    Then compares to given voltage range, and throws a ValueError if out of bounds.

    Parameters
    ----------
    voltage_range
        The range of the voltage levels of the device used.
    name
        The name of the device used.
    param_name
        The name of the offset parameter this method is using.
    offset
        The value of the offset parameter this method is using.


    Returns
    -------
    :
        The normalized offsets.

    Raises
    ------
    RuntimeError
        When a unit range is given that is not supported, or a value is given that falls
        outside the allowed range.

    """
    offset_in_arg = offset  # Always in volts
    if offset_in_arg is None:
        return None

    conversion_factor = 1
    if voltage_range.units == "mV":
        conversion_factor = 1e3
    elif voltage_range.units != "V":
        raise RuntimeError(
            f"Parameter {param_name} of {name} specifies "
            f"the units {voltage_range.units}, but the Qblox "
            f"backend only supports mV and V."
        )

    calculated_offset = offset_in_arg * conversion_factor
    if calculated_offset < voltage_range.min_val or calculated_offset > voltage_range.max_val:
        raise ValueError(
            f"Attempting to set {param_name} of {name} to "
            f"{offset_in_arg} V. {param_name} has to be between "
            f"{voltage_range.min_val / conversion_factor} and "
            f"{voltage_range.max_val / conversion_factor} V!"
        )

    return calculated_offset


def single_scope_mode_acquisition_raise(
    sequencer_0: int, sequencer_1: int, module_name: str
) -> None:
    """
    Raises an error stating that only one scope mode acquisition can be used per module.

    Parameters
    ----------
    sequencer_0
        First sequencer which attempts to use the scope mode acquisition.
    sequencer_1
        Second sequencer which attempts to use the scope mode acquisition.
    module_name
        Name of the module.

    Raises
    ------
    ValueError
        Always raises the error message.

    """
    raise ValueError(
        f"Both sequencer '{sequencer_0}' and '{sequencer_1}' "
        f"of '{module_name}' attempts to perform scope mode acquisitions. "
        f"Only one sequencer per device can "
        f"trigger raw trace capture.\n\nPlease ensure that "
        f"only one port-clock combination performs "
        f"raw trace acquisition per instrument."
    )


def is_pulse(operation: Operation) -> bool:
    """
    Check if the operation is a pulse.

    Parameters
    ----------
    operation:
        The operation to check.

    Returns
    -------
    :
        True if the operation is a pulse, False otherwise.

    """
    return operation.data["pulse_info"].get("wf_func") is not None


def is_square_pulse(operation: Operation | TimeableSchedule) -> bool:
    """
    Check if the operation is a square pulse.

    Parameters
    ----------
    operation:
        The operation to check.

    Returns
    -------
    :
        True if the operation is a square pulse, False otherwise.

    """
    pulse_info = operation.data["pulse_info"]
    return pulse_info["wf_func"] == "qblox_scheduler.waveforms.square"


def convert_qtm_fine_delay_to_int(fine_delay: float) -> int:
    """Convert a fine delay value in seconds to an integer value for Q1ASM."""
    fine_delay_int = round(fine_delay * 128e9)
    if (
        not 0
        <= fine_delay_int
        <= constants.MAX_QTM_FINE_DELAY_NS * constants.QTM_FINE_DELAY_INT_TO_NS_RATIO
    ):
        raise ValueError(
            f"Fine delay value {fine_delay} s is outside of the hardware supported "
            f"range of (0, {constants.MAX_QTM_FINE_DELAY_NS}) ns."
        )
    return fine_delay_int
