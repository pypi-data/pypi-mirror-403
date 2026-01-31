# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
"""Tests for pulse and acquisition corrections."""

import numpy as np
import pytest
from pydantic import ValidationError

from qblox_scheduler.backends import SerialCompiler
from qblox_scheduler.backends.corrections import (
    distortion_correct_pulse,
)
from qblox_scheduler.backends.qblox import constants as qblox_constants
from qblox_scheduler.backends.types.common import (
    SoftwareDistortionCorrection,
)
from qblox_scheduler.operations.gate_library import X
from qblox_scheduler.operations.pulse_library import (
    NumericalPulse,
    SquarePulse,
)
from qblox_scheduler.schedules.schedule import TimeableSchedule


# --------- Test fixtures ---------
@pytest.fixture
def hardware_options_distortion_corrections(
    filter_coefficients,
    use_numpy_array,
):
    return {
        "distortion_corrections": {
            "q2:fl-cl0.baseband": {
                "filter_func": "scipy.signal.lfilter",
                "input_var_name": "x",
                "kwargs": {
                    "b": filter_coefficients,
                    "a": np.array([1]) if use_numpy_array else [1],
                },
                "clipping_values": [-2.5, 2.5],
            },
        },
    }


@pytest.fixture
def filter_coefficients(use_numpy_array):
    coeffs = [
        1.95857073e00,
        -1.86377203e-01,
        -1.68242537e-01,
        -1.52224167e-01,
        -1.37802128e-01,
        -1.21882898e-01,
        -8.43375734e-02,
        -5.96895462e-02,
        -3.96596464e-02,
        -1.76637397e-02,
        3.30717805e-03,
        8.42734090e-03,
        6.07696990e-03,
        -5.36042501e-03,
        -1.29125589e-02,
        -4.28917964e-03,
        1.33989347e-02,
        1.62354458e-02,
        9.54868788e-03,
        1.17526984e-02,
        -1.89290954e-03,
        -9.12214872e-03,
        -1.36650277e-02,
        -1.90334368e-02,
        -1.01304462e-02,
        1.06730684e-03,
        1.09447182e-02,
        1.00001337e-02,
        3.11361952e-03,
        -1.38470050e-02,
    ]

    if use_numpy_array:
        return np.array(coeffs)

    return coeffs


# --------- Test correction functions ---------
@pytest.mark.parametrize(
    "clipping_values, duration, use_numpy_array",
    [
        (clipping, duration, use_numpy)
        for clipping in [None, [-0.2, 0.4]]
        for duration in np.arange(start=1e-9, stop=16e-9, step=1e-9)
        for use_numpy in [True, False]
    ],
)
def test_distortion_correct_pulse(filter_coefficients, clipping_values, duration, use_numpy_array):
    pulse = SquarePulse(amp=220e-3, duration=duration, port="", clock="")

    distortion_correction = SoftwareDistortionCorrection.model_validate(
        {
            "sampling_rate": qblox_constants.SAMPLING_RATE,
            "filter_func": "scipy.signal.lfilter",
            "input_var_name": "x",
            "kwargs": {
                "b": filter_coefficients,
                "a": np.array([1]) if use_numpy_array else [1],
            },
            "clipping_values": clipping_values,
        }
    )

    corrected_pulse = distortion_correct_pulse(
        pulse_data=pulse.data["pulse_info"],
        distortion_correction=distortion_correction,
    )

    corrected_pulse_samples = corrected_pulse.data["pulse_info"]["samples"]

    assert len(corrected_pulse_samples) > 1, "Correction always generates at least 2 sample points"

    if distortion_correction.clipping_values:
        assert min(corrected_pulse_samples) >= distortion_correction.clipping_values[0]
        assert max(corrected_pulse_samples) <= distortion_correction.clipping_values[1]


@pytest.mark.parametrize(
    "config_type, use_numpy_array",
    [
        (config_type, use_numpy)
        for config_type in [
            "QbloxHardwareCompilationConfig",
        ]
        for use_numpy in [True, False]
    ],
)
def test_apply_software_distortion_corrections(
    mock_setup_basic_transmon_with_standard_params,
    hardware_options_distortion_corrections,
    two_qubit_gate_schedule,
    get_subschedule_operation,
    config_type,
):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]
    if "Qblox" in config_type:
        hardware_compilation_config = {
            "config_type": config_type,
            "hardware_description": {
                "cluster0": {
                    "instrument_type": "Cluster",
                    "ref": "internal",
                    "modules": {
                        "1": {
                            "instrument_type": "QCM",
                        },
                    },
                }
            },
            "connectivity": {
                "graph": [
                    ("cluster0.module1.complex_output_0", "q2:fl"),
                    ("cluster0.module1.complex_output_0", "q3:fl"),
                ]
            },
            "hardware_options": hardware_options_distortion_corrections,
        }

    quantum_device.hardware_config = hardware_compilation_config

    operation_hash = list(two_qubit_gate_schedule.operations.keys())[1]
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=two_qubit_gate_schedule,
        config=quantum_device.generate_compilation_config(),
    )

    assert list(compiled_sched.operations.keys())[1] == operation_hash, (
        "Key of CZ operation remains identical"
    )

    corrected_pulse = get_subschedule_operation(compiled_sched, [1, 0])
    assert isinstance(corrected_pulse, NumericalPulse), "Type of CZ operation is now NumericalPulse"

    assert corrected_pulse.data["pulse_info"]["samples"] == pytest.approx(
        [
            0.979285365,
            0.8860967635,
            0.801975495,
            0.7258634115,
            0.6569623475,
            0.5960208985000001,
            0.5538521118,
            0.5240073387,
            0.5041775155,
            0.49534564565,
            0.496999234675,
            0.501212905125,
            0.5042513900750001,
            0.5015711775700001,
            0.49511489812000015,
            0.49297030829999994,
            0.4996697756499999,
            0.5077874985499999,
            0.5125618424899999,
            0.5184381916899999,
        ]
    )


def test_apply_latency_corrections_hardware_options_invalid_raises(
    mock_setup_basic_transmon,
):
    """
    This test function checks that:
    Providing an invalid latency correction specification raises an exception
    when compiling.
    """

    sched = TimeableSchedule("Latency experiment")
    sched.add(X("q4"))
    sched.add(
        SquarePulse(port="q4:res", clock="q4.ro", amp=0.25, duration=12e-9),
        ref_pt="start",
    )

    with pytest.raises(ValidationError, match="Input should be a valid number"):
        mock_setup_basic_transmon["quantum_device"].hardware_config = {
            "config_type": "QbloxHardwareCompilationConfig",
            "hardware_description": {},
            "hardware_options": {
                "latency_corrections": {"q4:mw-q4.01": 2e-8, "q4:res-q4.ro": None}
            },
            "connectivity": {},
        }
