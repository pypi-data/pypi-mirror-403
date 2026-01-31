import json
from enum import Enum

import numpy as np
import pytest

from qblox_scheduler.backends import SerialCompiler
from qblox_scheduler.backends.circuit_to_device import DeviceCompilationConfig
from qblox_scheduler.device_under_test.mock_setup import (
    set_standard_params_basic_nv,
    set_up_mock_basic_nv_setup,
)
from qblox_scheduler.device_under_test.nv_element import BasicElectronicNVElement
from qblox_scheduler.device_under_test.quantum_device import QuantumDevice
from qblox_scheduler.instrument_coordinator.instrument_coordinator import (
    InstrumentCoordinator,
)
from qblox_scheduler.operations.gate_library import X
from qblox_scheduler.schedules.schedule import TimeableSchedule


@pytest.fixture
def electronic_q0() -> BasicElectronicNVElement:
    """Fixture returning electronic qubit named qe0."""
    q0 = BasicElectronicNVElement("qe0")

    # Electronic NV element is returned
    yield q0


def test_qubit_name(electronic_q0: BasicElectronicNVElement):
    """Qubit name is stored correctly."""
    assert electronic_q0.name == "qe0"


def test_operation_configs_are_submodules(electronic_q0: BasicElectronicNVElement):
    """Operation configuration is not only a class attribute, but also a submodule"""
    assert "ports" in electronic_q0.submodules
    assert "clock_freqs" in electronic_q0.submodules
    assert "spectroscopy_operation" in electronic_q0.submodules
    assert "reset" in electronic_q0.submodules
    assert "measure" in electronic_q0.submodules


def test_generate_config_spectroscopy(electronic_q0: BasicElectronicNVElement):
    """Setting values updates the correct values in the config."""
    # Set values for spectroscopy
    electronic_q0.spectroscopy_operation.amplitude = 1.0
    electronic_q0.spectroscopy_operation.duration = 10e-6

    # Get device config
    dev_cfg = electronic_q0.generate_device_config()
    cfg_spec = dev_cfg.elements["qe0"]["spectroscopy_operation"]

    # Assert values are in right place
    assert cfg_spec.factory_kwargs["duration"] == 10e-6
    assert cfg_spec.factory_kwargs["amplitude"] == 1.0


def test_generate_config_reset(electronic_q0: BasicElectronicNVElement):
    """Setting values updates the correct values in the config."""
    # Set values for reset
    electronic_q0.reset.amplitude = 1.0
    electronic_q0.reset.duration = 10e-6

    # Get device config
    dev_cfg = electronic_q0.generate_device_config()
    cfg_reset = dev_cfg.elements["qe0"]["reset"]

    # Assert values are in right place
    assert cfg_reset.factory_kwargs["duration"] == 10e-6
    assert cfg_reset.factory_kwargs["amp"] == 1.0


def test_generate_config_measure(electronic_q0: BasicElectronicNVElement):
    """Setting values updates the correct values in the config."""
    # Set values for measure
    electronic_q0.measure.pulse_amplitude = 1.0
    electronic_q0.measure.pulse_duration = 300e-6
    electronic_q0.measure.acq_duration = 287e-6
    electronic_q0.measure.acq_delay = 13e-6
    electronic_q0.measure.acq_channel = 7
    electronic_q0.clock_freqs.ge0 = 470.4e12  # 637 nm
    electronic_q0.clock_freqs.ge1 = 470.4e12 - 5e9  # slightly detuned

    # Get device config
    dev_cfg = electronic_q0.generate_device_config()
    cfg_measure = dev_cfg.elements["qe0"]["measure"]

    # Assert values are in right place
    assert cfg_measure.factory_kwargs["pulse_amplitudes"] == [1.0]
    assert cfg_measure.factory_kwargs["pulse_durations"] == [300e-6]
    assert cfg_measure.factory_kwargs["pulse_ports"] == ["qe0:optical_control"]
    assert cfg_measure.factory_kwargs["pulse_clocks"] == ["qe0.ge0"]
    assert cfg_measure.factory_kwargs["acq_duration"] == 287e-6
    assert cfg_measure.factory_kwargs["acq_delay"] == 13e-6
    assert cfg_measure.factory_kwargs["acq_channel"] == 7
    assert cfg_measure.factory_kwargs["acq_port"] == "qe0:optical_readout"
    assert cfg_measure.factory_kwargs["acq_clock"] == "qe0.ge0"
    assert cfg_measure.factory_kwargs["pulse_type"] == "SquarePulse"

    # Changing values of the measure
    electronic_q0.measure.acq_channel = "ch_7"

    dev_cfg = electronic_q0.generate_device_config()
    cfg_measure = dev_cfg.elements["qe0"]["measure"]

    # Assert values are in right place
    assert cfg_measure.factory_kwargs["acq_channel"] == "ch_7"


def test_generate_config_charge_reset(electronic_q0: BasicElectronicNVElement):
    """Setting values updates the correct values in the config."""
    # Set values for charge_reset
    electronic_q0.charge_reset.amplitude = 1.0
    electronic_q0.charge_reset.duration = 300e-6
    electronic_q0.clock_freqs.ionization = 564e12  # 532 nm

    # Get device config
    dev_cfg = electronic_q0.generate_device_config()
    cfg_charge_reset = dev_cfg.elements["qe0"]["charge_reset"]

    # Assert values are in right place
    assert dev_cfg.clocks["qe0.ionization"] == 564e12
    assert cfg_charge_reset.factory_kwargs["amp"] == 1.0
    assert cfg_charge_reset.factory_kwargs["duration"] == 300e-6
    assert cfg_charge_reset.factory_kwargs["port"] == "qe0:optical_control"
    assert cfg_charge_reset.factory_kwargs["clock"] == "qe0.ionization"


def test_generate_config_crcount(electronic_q0: BasicElectronicNVElement):
    """Setting values updates the correct values in the config."""
    # Set values for CRCount
    electronic_q0.cr_count.readout_pulse_amplitude = 0.2
    electronic_q0.cr_count.spinpump_pulse_amplitude = 1.6
    electronic_q0.cr_count.readout_pulse_duration = 10e-9
    electronic_q0.cr_count.spinpump_pulse_duration = 40e-9
    electronic_q0.cr_count.acq_duration = 39e-9
    electronic_q0.cr_count.acq_delay = 1e-9
    electronic_q0.cr_count.acq_channel = 3

    # Get device config
    dev_cfg = electronic_q0.generate_device_config()
    cfg_crcount = dev_cfg.elements["qe0"]["cr_count"]

    # Assert values are in right place
    assert cfg_crcount.factory_kwargs["pulse_amplitudes"] == [0.2, 1.6]
    assert cfg_crcount.factory_kwargs["pulse_durations"] == [10e-9, 40e-9]
    assert cfg_crcount.factory_kwargs["pulse_ports"] == ["qe0:optical_control" for _ in range(2)]
    assert cfg_crcount.factory_kwargs["acq_duration"] == 39e-9
    assert cfg_crcount.factory_kwargs["acq_delay"] == 1e-9
    assert cfg_crcount.factory_kwargs["acq_channel"] == 3

    # Changing values of the measure
    electronic_q0.cr_count.acq_channel = "ch_3"

    dev_cfg = electronic_q0.generate_device_config()
    cfg_measure = dev_cfg.elements["qe0"]["cr_count"]

    # Assert values are in right place
    assert cfg_measure.factory_kwargs["acq_channel"] == "ch_3"


def test_generate_device_config(electronic_q0: BasicElectronicNVElement):
    """Generating device config returns DeviceCompilationConfig."""
    dev_cfg = electronic_q0.generate_device_config()
    assert isinstance(dev_cfg, DeviceCompilationConfig)


def test_mock_nv_setup():
    """Can use mock setup multiple times after closing it."""
    # test that everything works once
    mock_nv_setup = set_up_mock_basic_nv_setup()
    assert isinstance(mock_nv_setup, dict)
    set_standard_params_basic_nv(mock_nv_setup)
    for inst in mock_nv_setup.values():
        if callable(getattr(inst, "close", None)):  # Only actual instruments should be closed
            inst.close()

    # test that tear-down closes all instruments by re-executing
    mock_nv_setup = set_up_mock_basic_nv_setup()
    assert isinstance(mock_nv_setup, dict)
    set_standard_params_basic_nv(mock_nv_setup)


def test_r_xy_compiles(mock_setup_basic_nv_qblox_hardware):
    """Test Rxy operations compile using the skewed hermite pulse waveform"""

    # Create test NV center element
    qe0: BasicElectronicNVElement = mock_setup_basic_nv_qblox_hardware["qe0"]

    qe0.clock_freqs.spec = 2.2e9

    qe0.rxy.amp180 = 1
    qe0.rxy.duration = 1e-6

    rxy_sched = TimeableSchedule("Rxy_Hermite")
    rxy_sched.add(X("qe0"))

    # Assert
    abs_times = [0]
    abs_times.append(abs_times[-1] + qe0.rxy.duration)

    compiler = SerialCompiler(name="compiler")
    schedule = compiler.compile(
        schedule=rxy_sched,
        config=mock_setup_basic_nv_qblox_hardware["quantum_device"].generate_compilation_config(),
    )

    for i, schedulable in enumerate(schedule.schedulables.values()):
        assert schedulable["abs_time"] == abs_times[i]

    assert schedule.compiled_instructions != {}


@pytest.fixture
def dev() -> QuantumDevice:
    """Fixture returning quantum device with instrument coordinator."""
    device = QuantumDevice("dev")
    coordinator = InstrumentCoordinator("ic")
    device.instr_instrument_coordinator = coordinator
    yield device


def test_find_coordinator(dev: QuantumDevice):
    """Quantum device has instrument coordinator."""
    coordinator = dev.instr_instrument_coordinator
    assert coordinator.name == "ic"


def test_generate_device_config_part_of_device(
    electronic_q0: BasicElectronicNVElement, dev: QuantumDevice
):
    """Device config contains entry for a device element."""
    dev.add_element(electronic_q0)
    dev_cfg = dev.generate_device_config()
    assert "qe0" in dev_cfg.elements


def test_nv_center_serialization(electronic_q0):
    """
    Tests the serialization process of :class:`~BasicElectronicNVElement` by comparing the
    parameter values of the submodules of the original `BasicElectronicNVElement` object and
    the serialized counterpart.
    """

    # Set values to params with initial_value = nan
    electronic_q0.spectroscopy_operation.amplitude = 1.0
    electronic_q0.clock_freqs.f01 = 470.4e12
    electronic_q0.clock_freqs.ionization = 564e12
    electronic_q0.clock_freqs.spec = 2.2e9
    electronic_q0.clock_freqs.ge0 = 470.4e12
    electronic_q0.clock_freqs.ge1 = 470.4e12 - 5e9
    electronic_q0.reset.amplitude = 1.0
    electronic_q0.charge_reset.amplitude = 1.0
    electronic_q0.rxy.amp180 = 0.5
    electronic_q0.measure.pulse_amplitude = 1.0
    electronic_q0.cr_count.readout_pulse_amplitude = 0.2
    electronic_q0.cr_count.spinpump_pulse_amplitude = 1.6

    electronic_q0_as_dict = json.loads(electronic_q0.to_json())
    assert electronic_q0_as_dict.__class__ is dict
    assert electronic_q0_as_dict["element_type"] == "BasicElectronicNVElement"

    # Check that all original submodule params match their serialized counterpart
    for submodule_name, submodule in electronic_q0.submodules.items():
        for parameter_name, expected_val in submodule.parameters.items():
            val = electronic_q0_as_dict[submodule_name][parameter_name]

            if isinstance(expected_val, Enum):
                expected_val = expected_val.value  # noqa: PLW2901

            np.testing.assert_equal(val, expected_val, strict=True)

    # Check that all serialized submodule params match the original
    for submodule_name, submodule_data in electronic_q0_as_dict.items():
        if submodule_name in ("name", "element_type"):
            continue
        for parameter_name, parameter_val in submodule_data.items():
            expected_parameter_val = getattr(
                electronic_q0.submodules[submodule_name], parameter_name
            )

            if isinstance(expected_parameter_val, Enum):
                expected_parameter_val = expected_parameter_val.value

            np.testing.assert_equal(parameter_val, expected_parameter_val, strict=True)


def test_nv_center_deserialization(mock_setup_basic_nv_qblox_hardware):
    electronic_q0 = mock_setup_basic_nv_qblox_hardware["qe0"]

    electronic_q0_serialized = electronic_q0.to_json()

    assert electronic_q0_serialized.__class__ is str

    original_config = electronic_q0._generate_config()

    deserialized = type(electronic_q0).from_json(electronic_q0_serialized)

    assert deserialized._generate_config() == original_config
