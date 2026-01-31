# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Classes for handling pulses."""

from __future__ import annotations

import logging
from abc import ABC
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import numpy as np

from qblox_scheduler._check_unsupported_expression import check_unsupported_expression
from qblox_scheduler.backends.qblox import constants, helpers, q1asm_instructions
from qblox_scheduler.backends.qblox.enums import ChannelMode
from qblox_scheduler.backends.qblox.operation_handling.base import IOperationStrategy
from qblox_scheduler.backends.types.qblox import (
    ClusterModuleDescription,
    RFDescription,
    StaticAnalogModuleProperties,
)
from qblox_scheduler.helpers.waveforms import normalize_waveform_data
from qblox_scheduler.operations.expressions import BinaryExpression, Expression
from qblox_scheduler.operations.variables import Variable

if TYPE_CHECKING:
    from qblox_scheduler.backends.qblox.qasm_program import (
        QASMProgram,
    )
    from qblox_scheduler.backends.types import qblox as types

logger = logging.getLogger(__name__)


class PulseStrategyPartial(IOperationStrategy, ABC):
    """
    Contains the logic shared between all the pulses.

    Parameters
    ----------
    operation_info
        The operation info that corresponds to this pulse.
    channel_name
        Specifies the channel identifier of the hardware config (e.g. `complex_output_0`).

    """

    _amplitude_path_I: float | Variable | None
    _amplitude_path_Q: float | Variable | None

    def __init__(self, operation_info: types.OpInfo, channel_name: str) -> None:
        self._pulse_info: types.OpInfo = operation_info
        self.channel_name = channel_name

    @property
    def operation_info(self) -> types.OpInfo:
        """Property for retrieving the operation info."""
        return self._pulse_info


def _get_i_and_q_gain_from_pulse_info(
    pulse_info: dict[str, Any],
) -> tuple[float | Variable | None, float | Variable | None]:
    wf_func = pulse_info["wf_func"]
    if wf_func in (
        "qblox_scheduler.waveforms.square",
        "qblox_scheduler.waveforms.soft_square",
        "qblox_scheduler.waveforms.chirp",
        "qblox_scheduler.waveforms.interpolated_complex_waveform",
    ):
        amp_param = "gain" if "interpolated_complex_waveform" in wf_func else "amp"
        amp = pulse_info[amp_param]
        if isinstance(amp, Sequence):
            amplitude_path_I = amp[0]
            amplitude_path_Q = amp[1]
        elif isinstance(amp, complex):
            amplitude_path_I = amp.real
            amplitude_path_Q = amp.imag
        else:
            amplitude_path_I = amp
            amplitude_path_Q = 0
        return amplitude_path_I, amplitude_path_Q
    elif wf_func == "qblox_scheduler.waveforms.drag":
        return pulse_info["amplitude"], pulse_info["amplitude"]
    return None, None


def _get_var_from_supported_expression(expression: Expression) -> Variable:
    match expression:
        case Variable():
            return expression
        case BinaryExpression(
            lhs=Variable() as lhs, operator="*" | "/", rhs=(int() | float()) as rhs
        ):
            return lhs
        case BinaryExpression(lhs=(int() | float()) as lhs, operator="*", rhs=Variable() as rhs):
            return rhs
        case _:
            raise NotImplementedError(f"Unsupported expression: {expression}.")


class GenericPulseStrategy(PulseStrategyPartial):
    """
    Default class for handling pulses.

    No assumptions are made with regards to the pulse shape and no optimizations
    are done.

    Parameters
    ----------
    operation_info
        The operation info that corresponds to this pulse.
    channel_name
        Specifies the channel identifier of the hardware config (e.g. `complex_output_0`).

    """

    def __init__(self, operation_info: types.OpInfo, channel_name: str) -> None:
        super().__init__(
            operation_info=operation_info,
            channel_name=channel_name,
        )

        self._amplitude_path_I: float | Variable | None = None
        self._amplitude_path_Q: float | Variable | None = None

        self._waveform_index0: int | None = None
        self._waveform_index1: int | None = None

        self._waveform_len: int | None = None

    def generate_data(self, wf_dict: dict[str, Any]) -> None:
        r"""
        Generates the data and adds them to the ``wf_dict`` (if not already present).

        In complex mode (e.g. ``complex_output_0``), the NCO produces real-valued data
        (:math:`I_\\text{IF}`) on sequencer path_I and imaginary data (:math:`Q_\\text{IF}`)
        on sequencer path_Q.

        .. math::
            \\underbrace{\\begin{bmatrix}
            \\cos\\omega t & -\\sin\\omega t \\\\
            \\sin\\omega t & \\phantom{-}\\cos\\omega t \\end{bmatrix}}_\\text{NCO}
            \\begin{bmatrix}
            I \\\\
            Q \\end{bmatrix} =
            \\begin{bmatrix}
            I \\cdot \\cos\\omega t - Q \\cdot\\sin\\omega t \\\\
            I \\cdot \\sin\\omega t + Q \\cdot\\cos\\omega t \\end{bmatrix}
            \\begin{matrix}
            \\ \\text{(path_I)} \\\\
            \\ \\text{(path_Q)} \\end{matrix}
            =
            \\begin{bmatrix}
            I_\\text{IF} \\\\
            Q_\\text{IF} \\end{bmatrix}


        In real mode (e.g. ``real_output_0``), the NCO produces :math:`I_\\text{IF}` on
        path_I


        .. math::
            \\underbrace{\\begin{bmatrix}
            \\cos\\omega t & -\\sin\\omega t \\\\
            \\sin\\omega t & \\phantom{-}\\cos\\omega t \\end{bmatrix}}_\\text{NCO}
            \\begin{bmatrix}
            I \\\\
            Q \\end{bmatrix}  =
            \\begin{bmatrix}
            I \\cdot \\cos\\omega t - Q \\cdot\\sin\\omega t\\\\
             - \\end{bmatrix}
            \\begin{matrix}
            \\ \\text{(path_I)} \\\\
            \\ \\text{(path_Q)} \\end{matrix}
            =
            \\begin{bmatrix}
            I_\\text{IF} \\\\
            - \\end{bmatrix}


        Note that the fields marked with `-` represent waveforms that are not relevant
        for the mode.


        Parameters
        ----------
        wf_dict
            The dictionary to add the waveform to. N.B. the dictionary is modified in
            function.
        domains
            The domains used in the schedule, keyed by variable. This is added as temporarily
            to ensure we do not upload unnecessary waveforms. The domain information will be used to
            figure out whether or not a "Q" path waveform needs to be uploaded.

        Raises
        ------
        ValueError
            Data is complex (has an imaginary component), but the channel_name is not
            set as complex (e.g. ``complex_output_0``).

        """
        op_info = self.operation_info

        amplitude_path_I, amplitude_path_Q = _get_i_and_q_gain_from_pulse_info(
            self.operation_info.data
        )

        # Simplify expressions so that we can easily recognize multiplication with or division by a
        # constant.
        if isinstance(amplitude_path_I, Expression):
            amplitude_path_I = amplitude_path_I.reduce()
        if isinstance(amplitude_path_Q, Expression):
            amplitude_path_Q = amplitude_path_Q.reduce()

        # If the amplitudes are still expressions after the reduction step, check if we can handle
        # this expression (i.e., it is just a variable, or a simple variable * constant or variable
        # / constant expression).
        if isinstance(amplitude_path_I, Expression):
            var_path_I = _get_var_from_supported_expression(amplitude_path_I)
            op_info = op_info.substitute({var_path_I: 1})
        else:
            var_path_I = None
        if isinstance(amplitude_path_Q, Expression):
            var_path_Q = _get_var_from_supported_expression(amplitude_path_Q)
            op_info = op_info.substitute({var_path_Q: 1})
        else:
            var_path_Q = None

        check_unsupported_expression(*op_info.data.values(), operation_name=op_info.name)
        waveform_data = helpers.generate_waveform_data(
            op_info.data, sampling_rate=constants.SAMPLING_RATE
        )

        # If neither I nor Q a variable: normalize both
        if var_path_I is None and var_path_Q is None:
            waveform_data, amp_real, amp_imag = normalize_waveform_data(waveform_data)
        # If one of I or Q is a variable, normalize the waveform that is not scaled by a variable.
        elif var_path_I is not None and var_path_Q is None:
            amp_real = None
            waveform_data_imag, _, amp_imag = normalize_waveform_data(np.imag(waveform_data))
            if amp_imag != 0:
                waveform_data.imag = waveform_data_imag
        elif var_path_I is None and var_path_Q is not None:
            waveform_data_real, amp_real, _ = normalize_waveform_data(np.real(waveform_data))
            waveform_data.real = waveform_data_real
            amp_imag = None
        # If both I and Q are variables, or there is a scaling variable for both: no normalization.
        else:
            amp_real = None
            amp_imag = None
        self._waveform_len = len(waveform_data)

        if np.any(np.iscomplex(waveform_data)) and ChannelMode.COMPLEX not in self.channel_name:
            raise ValueError(
                f"Complex valued {op_info!s} detected but the sequencer"
                f" is not expecting complex input. This can be caused by "
                f"attempting to play complex valued waveforms on an output"
                f" marked as real.\n\nException caused by {op_info!r}."
            )
        if (
            np.any((np.abs(waveform_data.real) > 1) | (np.abs(waveform_data.imag) > 1))
            or (amp_real is not None and abs(amp_real) > 1)
            or (amp_imag is not None and abs(amp_imag) > 1)
        ):
            raise ValueError(f"Waveform amplitude exceeds maximum of 1 for pulse {op_info!s}")

        def non_null(amp: float) -> bool:
            return abs(amp) >= 2 / constants.IMMEDIATE_SZ_GAIN

        idx_real = (
            helpers.add_to_wf_dict_if_unique(wf_dict=wf_dict, waveform=waveform_data.real)
            if amp_real is None or non_null(amp_real)
            else None
        )
        idx_imag = (
            helpers.add_to_wf_dict_if_unique(wf_dict=wf_dict, waveform=waveform_data.imag)
            if amp_imag is None or non_null(amp_imag)
            else None
        )

        self._waveform_index0, self._waveform_index1 = idx_real, idx_imag
        self._amplitude_path_I = var_path_I or amp_real
        self._amplitude_path_Q = var_path_Q or amp_imag

    def insert_qasm(self, qasm_program: QASMProgram) -> None:
        """
        Add the assembly instructions for the Q1 sequence processor that corresponds to
        this pulse.

        Parameters
        ----------
        qasm_program
            The QASMProgram to add the assembly instructions to.

        """
        if qasm_program.time_last_pulse_triggered is not None and (
            qasm_program.elapsed_time - qasm_program.time_last_pulse_triggered
            < constants.MIN_TIME_BETWEEN_OPERATIONS
        ):
            raise ValueError(
                f"Attempting to start an operation at t="
                f"{qasm_program.elapsed_time} ns, while the last operation was "
                f"started at t={qasm_program.time_last_pulse_triggered} ns. "
                f"Please ensure a minimum interval of "
                f"{constants.MIN_TIME_BETWEEN_OPERATIONS} ns between "
                f"operations.\n\nError caused by operation:\n"
                f"{self.operation_info!r}."
            )
        qasm_program.time_last_pulse_triggered = qasm_program.elapsed_time

        # Only emit play command if at least one path has a signal
        # else update parameters as there might still be some lingering
        # from for example a voltage offset.
        index0 = self._waveform_index0
        index1 = self._waveform_index1
        if index0 is None and index1 is None:
            qasm_program.emit(
                q1asm_instructions.UPDATE_PARAMETERS,
                constants.MIN_TIME_BETWEEN_OPERATIONS,
                comment=f"{self.operation_info.name} has too low amplitude to be played, "
                f"updating parameters instead",
            )
        else:
            assert self._amplitude_path_I is not None
            assert self._amplitude_path_Q is not None
            qasm_program.set_gain_from_amplitude(
                self._amplitude_path_I,
                self._amplitude_path_Q,
                self.operation_info,
            )
            # If a channel doesn't have an index (index0 or index1 is None) means,
            # that for that channel we do not want to play any waveform;
            # it's also ensured in this case, that the gain is set to 0 for that channel;
            # but, the Q1ASM program needs a waveform index for both channels,
            # so we set the other waveform's index in this case as a dummy
            qasm_program.emit(
                q1asm_instructions.PLAY,
                index0 if (index0 is not None) else index1,
                index1 if (index1 is not None) else index0,
                constants.MIN_TIME_BETWEEN_OPERATIONS,  # N.B. the waveform keeps playing
                comment=f"play {self.operation_info.name} ({self._waveform_len} ns)",
            )
        qasm_program.elapsed_time += constants.MIN_TIME_BETWEEN_OPERATIONS


class DigitalOutputStrategy(PulseStrategyPartial, ABC):
    """
    Interface class for :class:`MarkerPulseStrategy` and :class:`DigitalPulseStrategy`.

    Both classes work very similarly, since they are both strategy classes for the
    `~qblox_scheduler.operations.pulse_library.MarkerPulse`. The
    ``MarkerPulseStrategy`` is for the QCM/QRM modules, and the ``DigitalPulseStrategy``
    for the QTM.
    """

    def generate_data(self, wf_dict: dict[str, Any]) -> None:
        """Returns None as no waveforms are generated in this strategy."""
        pass


class MarkerPulseStrategy(DigitalOutputStrategy):
    """If this strategy is used a digital pulse is played on the corresponding marker."""

    def __init__(
        self,
        operation_info: types.OpInfo,
        channel_name: str,
        module_options: ClusterModuleDescription,
    ) -> None:
        super().__init__(operation_info, channel_name)
        self.module_options = module_options

    def insert_qasm(self, qasm_program: QASMProgram) -> None:
        """
        Inserts the QASM instructions to play the marker pulse.
        Note that for RF modules the first two bits of set_mrk
        are used as switches for the RF outputs.

        Parameters
        ----------
        qasm_program
            The QASMProgram to add the assembly instructions to.

        """
        hw_properties = qasm_program.static_hw_properties
        if not isinstance(hw_properties, StaticAnalogModuleProperties):
            raise TypeError(
                f"Marker Operations are only supported for analog modules, "
                f"not for instrument {self.module_options.instrument_type}."
            )
        if self.channel_name not in hw_properties.channel_name_to_digital_marker:
            raise ValueError(
                f"Unable to set markers on channel '{self.channel_name}' for "
                f"instrument {hw_properties.instrument_type} "
                f"and operation {self.operation_info.name}. "
                f"Supported channels: {list(hw_properties.channel_name_to_digital_marker.keys())}"
            )
        marker = hw_properties.channel_name_to_digital_marker[self.channel_name]
        default_marker = 0
        if (
            isinstance(self.module_options, RFDescription)
            and self.module_options.rf_output_on is True
            and hw_properties.default_markers
        ):
            default_marker = hw_properties.default_markers[self.channel_name]
            if marker | default_marker == default_marker:  # Marker has no effect
                raise RuntimeError(
                    "Attempting to turn on an RF output on a module where "
                    "`rf_output_on` is set to True (the default value). \n"
                    "Turning the RF output on with an RFSwitchToggle Operation "
                    "has no effect. \n"
                    "Please set `rf_output_on` to False for this module "
                    "in the hardware configuration."
                )

        if self.operation_info.data["enable"]:
            marker |= default_marker
            qasm_program.emit(
                q1asm_instructions.SET_MARKER,
                marker,
                comment=f"set markers to {marker} (marker pulse)",
            )
        else:
            qasm_program.emit(
                q1asm_instructions.SET_MARKER,
                default_marker,
                comment=f"set markers to {default_marker} (default, marker pulse)",
            )


class DigitalPulseStrategy(DigitalOutputStrategy):
    """
    If this strategy is used a digital pulse is played
    on the corresponding digital output channel.
    """

    def insert_qasm(self, qasm_program: QASMProgram) -> None:
        """
        Inserts the QASM instructions to play the marker pulse.
        Note that for RF modules the first two bits of set_mrk
        are used as switches for the RF outputs.

        Parameters
        ----------
        qasm_program
            The QASMProgram to add the assembly instructions to.

        """
        if ChannelMode.DIGITAL not in self.channel_name:
            port = self.operation_info.data.get("port")
            clock = self.operation_info.data.get("clock")

            raise ValueError(
                f"{self.__class__.__name__} can only be used with a "
                f"digital channel. Please make sure that "
                f"'digital' keyword is included in the channel_name in the hardware configuration "
                f"for port-clock combination '{port}-{clock}' "
                f"(current channel_name is '{self.channel_name}')."
                f"Operation causing exception: {self.operation_info}"
            )

        if self.operation_info.data["enable"]:
            fine_delay = helpers.convert_qtm_fine_delay_to_int(
                self.operation_info.data.get("fine_start_delay", 0)
            )
        else:
            fine_delay = helpers.convert_qtm_fine_delay_to_int(
                self.operation_info.data.get("fine_end_delay", 0)
            )
        qasm_program.emit(
            q1asm_instructions.SET_DIGITAL,
            int(self.operation_info.data["enable"]),
            1,  # Mask. Reserved for future use, set to 1.
            fine_delay,
        )
