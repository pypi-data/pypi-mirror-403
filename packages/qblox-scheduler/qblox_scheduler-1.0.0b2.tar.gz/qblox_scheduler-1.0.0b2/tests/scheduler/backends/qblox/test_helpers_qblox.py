# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
"""Tests for the helpers module."""

from __future__ import annotations

import math
from contextlib import nullcontext
from unittest.mock import Mock

import pytest

from qblox_scheduler.backends.qblox import constants, helpers
from qblox_scheduler.enums import BinMode
from qblox_scheduler.operations.acquisition_library import SSBIntegrationComplex
from qblox_scheduler.operations.hardware_operations.inline_q1asm import InlineQ1ASM
from qblox_scheduler.operations.pulse_library import SquarePulse
from qblox_scheduler.schemas.examples import utils

QBLOX_HARDWARE_CONFIG_TRANSMON = utils.load_json_example_scheme(
    "qblox_hardware_config_transmon.json"
)
QBLOX_HARDWARE_CONFIG_NV_CENTER = utils.load_json_example_scheme(
    "qblox_hardware_config_nv_center.json"
)


@pytest.mark.parametrize(
    "phase, expected_steps",
    [
        (0.0, 0),
        (360.0, 0),
        (10.0, 27777778),
        (11.11, 30861111),
        (123.123, 342008333),
        (90.0, 250000000),
        (-90.0, 750000000),
        (480.2, 333888889),
    ],
)
def test_get_nco_phase_arguments(phase, expected_steps):
    assert helpers.get_nco_phase_arguments(phase) == expected_steps


@pytest.mark.parametrize(
    "frequency, expected_steps",
    [
        (-500e6, -2000000000),
        (-200e3, -800000),
        (0.0, 0),
        (200e3, 800000),
        (500e6, 2000000000),
    ],
)
def test_get_nco_set_frequency_arguments(frequency: float, expected_steps: int):
    assert helpers.get_nco_set_frequency_arguments(frequency) == expected_steps


@pytest.mark.parametrize("frequency", [-500e6 - 1, 500e6 + 1])
def test_invalid_get_nco_set_frequency_arguments(frequency: float):
    with pytest.raises(ValueError):
        helpers.get_nco_set_frequency_arguments(frequency)


def __get_frequencies(
    clock_freq, lo_freq, interm_freq, downconverter_freq, mix_lo
) -> helpers.ValidatedFrequencies | str:
    if downconverter_freq is None or downconverter_freq == 0:
        freqs = helpers.Frequencies(clock=clock_freq)
    else:
        freqs = helpers.Frequencies(clock=downconverter_freq - clock_freq)

    if mix_lo is False:
        freqs.LO = freqs.clock
        if interm_freq is None:
            return "underconstrained"
        freqs.IF = interm_freq
    elif lo_freq is None and interm_freq is None:
        return "underconstrained"
    elif lo_freq is None and interm_freq is not None:
        freqs.IF = interm_freq
        freqs.LO = freqs.clock - interm_freq
    elif lo_freq is not None and interm_freq is None:
        freqs.IF = freqs.clock - lo_freq
        freqs.LO = lo_freq
    elif lo_freq is not None and interm_freq is not None:
        if math.isclose(freqs.clock, lo_freq + interm_freq):
            freqs.IF = interm_freq
            freqs.LO = lo_freq
        else:
            return "overconstrained"
    return helpers.ValidatedFrequencies(clock=freqs.clock, IF=freqs.IF, LO=freqs.LO)


@pytest.mark.filterwarnings(r"ignore:Overriding freqs.LO.*")
@pytest.mark.filterwarnings(r"ignore:Downconverter frequency 0 supplied*")
@pytest.mark.parametrize(
    "clock_freq, lo_freq, interm_freq, downconverter_freq, mix_lo, expected_freqs",
    [  # General test cases with positive frequencies
        (
            clock_freq := 100,
            lo_freq,
            interm_freq,
            downconverter_freq,
            mix_lo,
            __get_frequencies(clock_freq, lo_freq, interm_freq, downconverter_freq, mix_lo),
        )
        for lo_freq in [None, 20]
        for interm_freq in [None, 3]
        for downconverter_freq in [None, 0, 400]
        for mix_lo in [False, True]
    ]
    + [  # Test cases with negative frequencies
        (
            clock_freq,
            lo_freq := -200,
            interm_freq := -30,
            downconverter_freq := 400,
            mix_lo,
            __get_frequencies(clock_freq, lo_freq, interm_freq, downconverter_freq, mix_lo),
        )
        for clock_freq in [-100, 100]
        for mix_lo in [False, True]
    ]
    + [  # Test cases for downconverter_freq
        (
            clock_freq := 100,
            lo_freq := None,
            interm_freq := None,
            downconverter_freq,
            mix_lo := True,
            __get_frequencies(clock_freq, lo_freq, interm_freq, downconverter_freq, mix_lo),
        )
        for downconverter_freq in [0, clock_freq - 1, -400]
    ]
    + [  # Test cases for float("nan")
        (
            clock_freq := 100,
            lo_freq := float("nan"),
            interm_freq := 5,
            downconverter_freq := None,
            mix_lo := True,
            helpers.ValidatedFrequencies(clock=100, LO=95, IF=5),
        )
    ],
)
def test_determine_clock_lo_interm_freqs(
    clock_freq: float,
    lo_freq: float | None,
    interm_freq: float | None,
    downconverter_freq: float | None,
    mix_lo: bool,
    expected_freqs: helpers.Frequencies | str,
):
    freqs = helpers.Frequencies(clock=clock_freq, LO=lo_freq, IF=interm_freq)
    context_mngr = nullcontext()
    if (
        downconverter_freq is not None
        and (downconverter_freq < 0 or downconverter_freq < clock_freq)
    ) or expected_freqs in ("overconstrained", "underconstrained"):
        context_mngr = pytest.raises(ValueError)

    with context_mngr as error:
        assert (
            helpers.determine_clock_lo_interm_freqs(
                freqs=freqs,
                downconverter_freq=downconverter_freq,
                mix_lo=mix_lo,
            )
            == expected_freqs
        )
    if error is not None:
        possible_errors = []
        if expected_freqs == "underconstrained":
            if mix_lo:
                possible_errors.append(
                    f"Frequency settings underconstrained for {freqs.clock=}."
                    f" Neither LO nor IF supplied ({freqs.LO=}, {freqs.IF=})."
                )
            else:
                possible_errors.append(
                    f"Frequency settings underconstrained for {freqs.clock=}. "
                    "If mix_lo=False is specified, the IF must also be supplied "
                    f"({freqs.IF=})."
                )
        elif expected_freqs == "overconstrained":
            possible_errors.append(
                f"Frequency settings overconstrained."
                f" {freqs.clock=} must be equal to {freqs.LO=}+{freqs.IF=} when both are supplied."
            )
        if downconverter_freq is not None:
            if downconverter_freq < 0:
                possible_errors.append(
                    f"Downconverter frequency must be positive ({downconverter_freq=:e})"
                )
            elif downconverter_freq < clock_freq:
                possible_errors.append(
                    "Downconverter frequency must be greater than clock frequency "
                    f"({downconverter_freq=:e}, {clock_freq=:e})"
                )
        assert str(error.value) in possible_errors


def test_frequencies():
    freq = helpers.Frequencies(clock=100, LO=float("nan"), IF=float("nan"))
    assert freq.LO is None
    assert freq.IF is None

    with pytest.raises(ValueError):
        helpers.Frequencies(clock=None, LO=None, IF=None)


def test__assign_asm_info_to_devices_raises_portclock_err():
    block_wf = [1.0 for _ in range(123)]
    port, clock = "elephant", "pterodactyl"
    inline_q1asm_operation = InlineQ1ASM(
        program=f"play 22, 22, {len(block_wf)}",
        port=port,
        clock=clock,
        duration=200 / constants.SAMPLING_RATE,
        waveforms={
            "block": {
                "data": block_wf,
                "index": 22,
            },
        },
    )

    with pytest.raises(
        KeyError,
        match=(
            "Could not assign Q1ASM program to the device. The combination "
            f"of port {port} and clock {clock} could not be found "
        ),
    ):
        helpers._assign_asm_info_to_devices({}, {}, inline_q1asm_operation, 0)


def test__assign_pulse_info_to_devices_raises_portclock_err():
    port, clock = "apple", "pear"
    pulse = SquarePulse(amp=1, duration=2e-6, port=port, clock=clock)

    with pytest.raises(
        KeyError,
        match=(
            f"Could not assign pulse data to device. The combination "
            f"of port {port} and clock {clock} could not be found "
        ),
    ):
        helpers._assign_pulse_info_to_devices({}, {}, pulse.name, pulse["pulse_info"], 0)


def test__assign_acq_info_to_devices_raises_portclock_err():
    port, clock = "flute", "guitar"
    acq = SSBIntegrationComplex(
        port=port,
        clock=clock,
        duration=constants.MAX_SAMPLE_SIZE_SCOPE_ACQUISITIONS,
        acq_channel=0,
        coords={"index": 0},
        bin_mode=BinMode.APPEND,
    )
    with pytest.raises(
        KeyError,
        match=(
            f"Could not assign acquisition data to device. The combination "
            f"of port {port} and clock {clock} could not be found "
        ),
    ):
        helpers._assign_acq_info_to_devices(
            {}, {}, acq.name, acq["acquisition_info"], 0, Mock(), Mock()
        )
