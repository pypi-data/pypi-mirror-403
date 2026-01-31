# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2025, Qblox B.V.
import pytest

from qblox_scheduler import BasicTransmonElement, QuantumDevice, Schedule, SerialCompiler
from qblox_scheduler.operations import DRAGPulse, IdlePulse, Measure, RampPulse
from qblox_scheduler.operations.expressions import DType
from qblox_scheduler.operations.loop_domains import arange, linspace


def test_freq_expression(
    mock_setup_basic_transmon_with_standard_params, qblox_hardware_config_transmon
):
    qd: QuantumDevice = mock_setup_basic_transmon_with_standard_params["quantum_device"]
    qd.hardware_config = qblox_hardware_config_transmon
    qubit: BasicTransmonElement = mock_setup_basic_transmon_with_standard_params["q0"]

    frequency_center = qubit.clock_freqs.readout
    frequency_width = 100e6

    spec_sched = Schedule("resonator_spectroscopy")
    with (
        spec_sched.loop(arange(0, 10, 1, DType.NUMBER)),
        spec_sched.loop(
            linspace(
                start=frequency_center - frequency_width / 2,
                stop=frequency_center + frequency_width / 2,
                num=101,
                dtype=DType.FREQUENCY,
            )
        ) as freq,
    ):
        spec_sched.add(
            Measure(qubit.name, freq=1 * freq, coords={"frequency": freq}, acq_channel="S_21")
        )
        spec_sched.add(IdlePulse(10e-6))

    with pytest.raises(
        RuntimeError, match="Using expressions in SetClockFrequency is not fully supported yet."
    ):
        _ = SerialCompiler().compile(spec_sched, qd.generate_compilation_config())


def test_expression_in_ramp_pulse(
    mock_setup_basic_transmon_with_standard_params, qblox_hardware_config_transmon
):
    qd: QuantumDevice = mock_setup_basic_transmon_with_standard_params["quantum_device"]
    qd.hardware_config = qblox_hardware_config_transmon

    spec_sched = Schedule("resonator_spectroscopy")
    with spec_sched.loop(
        linspace(start=0, stop=1, num=101, dtype=DType.AMPLITUDE),
    ) as amp:
        spec_sched.add(RampPulse(amp=amp, duration=100e-9, port="q0:mw", clock="q0.01"))
        spec_sched.add(IdlePulse(10e-6))

    with pytest.raises(
        RuntimeError, match="Using expressions in RampPulse is not fully supported yet."
    ):
        _ = SerialCompiler().compile(spec_sched, qd.generate_compilation_config())


def test_expression_in_drag_pulse_beta(
    mock_setup_basic_transmon_with_standard_params, qblox_hardware_config_transmon
):
    qd: QuantumDevice = mock_setup_basic_transmon_with_standard_params["quantum_device"]
    qd.hardware_config = qblox_hardware_config_transmon

    spec_sched = Schedule("resonator_spectroscopy")
    with spec_sched.loop(
        linspace(start=0, stop=1, num=101, dtype=DType.AMPLITUDE),
    ) as amp:
        spec_sched.add(
            DRAGPulse(amplitude=0.5, beta=amp, phase=0, duration=24e-9, port="q0:mw", clock="q0.01")  # type: ignore
        )
        spec_sched.add(IdlePulse(10e-6))

    with pytest.raises(
        RuntimeError, match="Using expressions in DRAGPulse is not fully supported yet."
    ):
        _ = SerialCompiler().compile(spec_sched, qd.generate_compilation_config())
