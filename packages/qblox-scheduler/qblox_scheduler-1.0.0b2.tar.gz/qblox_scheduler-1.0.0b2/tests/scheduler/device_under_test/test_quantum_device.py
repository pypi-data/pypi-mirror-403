# type: ignore[reportCallIssue] # TODO: Remove after refactoring SchedulerBaseModel.__init__

import datetime
import os
from unittest.mock import mock_open, patch

import numpy as np
import pytest

from qblox_scheduler import BasicElectronicNVElement, BasicSpinElement, SpinEdge
from qblox_scheduler.analysis.data_handling import OutputDirectoryManager
from qblox_scheduler.backends.qblox.exceptions import (
    InvalidQuantumDeviceConfigurationError,
)
from qblox_scheduler.device_under_test.device_element import DeviceElement
from qblox_scheduler.device_under_test.quantum_device import QuantumDevice


def test_generate_device_config(mock_setup_basic_transmon: dict) -> None:
    quantum_device = mock_setup_basic_transmon["quantum_device"]

    # N.B. the validation of the generated config is happening inside the
    # device object itself using the pydantic dataclass. Invoking the function
    # tests this directly.
    dev_cfg = quantum_device.generate_device_config()

    assert {"q0", "q1", "q2", "q3"} <= set(dev_cfg.elements.keys())
    # Ensure that we also check that the edges are being configured
    assert "q2_q3" in dev_cfg.edges


def test_generate_hardware_config(
    mock_setup_basic_transmon: dict,
) -> None:
    quantum_device = mock_setup_basic_transmon["quantum_device"]

    mock_hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "ref": "external",
                "modules": {
                    "1": {"instrument_type": "QCM"},
                    "2": {"instrument_type": "QRM"},
                },
            },
            "iq_mixer_ic_lo_mw0": {"instrument_type": "IQMixer"},
            "iq_mixer_ic_lo_ro": {"instrument_type": "IQMixer"},
            "ic_lo_ro": {"instrument_type": "LocalOscillator", "power": 1},
            "ic_lo_mw0": {"instrument_type": "LocalOscillator", "power": 1},
        },
        "hardware_options": {
            "modulation_frequencies": {
                "q0:mw-q0.01": {"lo_freq": None, "interm_freq": -100000000.0},
                "q0:res-q0.ro": {"lo_freq": None, "interm_freq": 50000000.0},
            }
        },
        "connectivity": {
            "graph": [
                ["cluster0.module1.complex_output_0", "iq_mixer_ic_lo_mw0.if"],
                ["ic_lo_mw0.output", "iq_mixer_ic_lo_mw0.lo"],
                ["iq_mixer_ic_lo_mw0.rf", "q0:mw"],
                ["cluster0.module2.complex_output_0", "iq_mixer_ic_lo_ro.if"],
                ["ic_lo_ro.output", "iq_mixer_ic_lo_ro.lo"],
                ["iq_mixer_ic_lo_ro.rf", "q0:res"],
            ]
        },
    }

    quantum_device.hardware_config = mock_hardware_cfg

    _ = quantum_device.generate_hardware_config()

    # cannot validate as there is no schema exists see qblox-scheduler #181
    # validate_config(dev_cfg, scheme_fn="qblox_cfg.json")


@pytest.fixture
def dev():
    dev = QuantumDevice("dev")
    yield dev


@pytest.fixture
def meas_ctrl():
    test_mc = QuantumDevice("test_mc")
    yield test_mc


def test_adding_non_element_raises(dev, meas_ctrl):
    with pytest.raises(TypeError):
        dev.add_element(meas_ctrl)


def test_invalid_device_element_name():
    class DummyDeviceElement(DeviceElement):
        def generate_device_config(self):  # type: ignore
            pass

    invalid_name = "q_0"
    with pytest.raises(ValueError):
        DummyDeviceElement(invalid_name)


def test_wrong_scheduling_strategy(mock_setup_basic_transmon_with_standard_params):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]
    # Assert that a validation error is raised for scheduling strategy other_strategy
    with pytest.raises(ValueError):
        quantum_device.scheduling_strategy = "other_strategy"


@pytest.mark.parametrize(
    "to_file, add_utc_timestamp",
    [(True, True), (True, False), (False, True), (False, False)],
)
def test_quantum_device_json_serialization(
    mock_setup_basic_transmon_with_standard_params, to_file, add_utc_timestamp
):
    # Prepare to be serialized quantum device
    amp180_test = 1e-9
    q2_phase_correction_test = 44
    cfg_sched_repetitions_test = 512

    mock_setup = mock_setup_basic_transmon_with_standard_params
    quantum_device = mock_setup["quantum_device"]

    q2 = mock_setup["q2"]
    q2.rxy.amp180 = amp180_test

    edge_q2_q3 = mock_setup["q2_q3"]
    edge_q2_q3.cz.parent_phase_correction = q2_phase_correction_test

    quantum_device.cfg_sched_repetitions = cfg_sched_repetitions_test

    # Serialize, deserialize
    if to_file:
        path_serialized_quantum_device = quantum_device.to_json_file(
            path=None, add_timestamp=add_utc_timestamp
        )

        # Assert that UTC timestamp is indeed appended to file name
        if add_utc_timestamp:
            basename_of_saved_file = os.path.basename(path_serialized_quantum_device)
            assert datetime.datetime.strptime(
                basename_of_saved_file.split(".json", 1)[0].split(quantum_device.name + "_", 1)[1],
                "%Y-%m-%d_%H-%M-%S_%Z",
            )
        else:
            assert path_serialized_quantum_device == os.path.join(
                OutputDirectoryManager.get_datadir(), quantum_device.name + ".json"
            )

        assert path_serialized_quantum_device.__class__ is str

        deserialized_quantum_device = QuantumDevice.from_json_file(path_serialized_quantum_device)

    else:
        serialized_quantum_device = quantum_device.to_json()

        assert serialized_quantum_device.__class__ is str

        # Ensure QuantumDevice can be deserialized again
        _ = QuantumDevice.from_json(serialized_quantum_device)
        deserialized_quantum_device = QuantumDevice.from_json(serialized_quantum_device)

    assert deserialized_quantum_device.__class__ is QuantumDevice

    assert deserialized_quantum_device.get_element("q2").rxy.amp180 == amp180_test
    assert (
        deserialized_quantum_device.get_edge("q2_q3").cz.parent_phase_correction
        == q2_phase_correction_test
    )
    assert deserialized_quantum_device.cfg_sched_repetitions == cfg_sched_repetitions_test

    # NOTE: The following assertions won't pass because of NaN, so we only check the names
    # assert deserialized_quantum_device.elements == elements_list
    # assert deserialized_quantum_device.edges == edges_list

    # Convert the keys to a list to verify insertion order
    assert list(deserialized_quantum_device.elements.keys()) == list(quantum_device.elements.keys())
    assert list(deserialized_quantum_device.edges.keys()) == list(quantum_device.edges.keys())


def test_quantum_device_yaml_serialization(
    mock_setup_basic_transmon_with_standard_params,
    tmp_path,
):
    """Verify that a quantum device can be correctly (de)serialized from/to YAML."""
    original_qd = mock_setup_basic_transmon_with_standard_params["quantum_device"]
    tmp_file = original_qd.to_yaml_file(tmp_path)
    original_qd_dict = original_qd.to_dict()

    reconstructed_qd = QuantumDevice.from_yaml_file(tmp_file)
    reconstructed_qd_dict = reconstructed_qd.to_dict()

    # Ensure that QCoDeS instruments are not deserialized
    assert reconstructed_qd.instr_instrument_coordinator is None

    np.testing.assert_equal(original_qd_dict, reconstructed_qd_dict, strict=True)


def test_quantum_device_fixed_yaml_deserialization(  # noqa: PLR0915
    qdevice_with_basic_nv_element_yaml,
    tmp_path,
):
    """
    Verify that a quantum device can be correctly deserialized from a specific YAML dump.

    Performs a deep check of every parameter involved to highlight potential regressions.
    """
    qd = QuantumDevice.from_yaml(qdevice_with_basic_nv_element_yaml)
    assert isinstance(qd, QuantumDevice)
    assert qd.name == "quantum_device"
    assert list(qd.elements.keys()) == ["qe0", "qe1"]
    assert list(qd.edges.keys()) == []
    assert qd.cfg_sched_repetitions == 1024

    # QCoDeS instruments should be kept to None
    assert qd.instr_instrument_coordinator is None

    # Test differing parameters
    qe0 = qd.get_element("qe0")
    assert isinstance(qe0, BasicElectronicNVElement)
    assert qe0.name == "qe0"
    assert qe0.clock_freqs.f01 == 3592000000.0
    assert qe0.clock_freqs.spec == 2200000000.0
    assert qe0.clock_freqs.ionization == 564000000000000.0
    assert qe0.measure.acq_channel == 0

    qe1 = qd.get_element("qe1")
    assert isinstance(qe1, BasicElectronicNVElement)
    assert qe1.name == "qe1"
    assert qe1.clock_freqs.f01 == 4874000000.0
    assert qe1.clock_freqs.spec == 1400000000.0
    assert qe1.clock_freqs.ionization == 420000000000000.0
    assert qe1.measure.acq_channel == 1

    # Test common parameters
    for el in (qe0, qe1):
        assert el.spectroscopy_operation.amplitude == 0.001
        assert el.spectroscopy_operation.duration == 8e-06
        assert el.spectroscopy_operation.pulse_shape == "SquarePulse"

        assert el.ports.microwave == f"{el.name}:mw"
        assert el.ports.optical_control == f"{el.name}:optical_control"
        assert el.ports.optical_readout == f"{el.name}:optical_readout"

        # assert el.clock_freqs.f01 == ...
        # assert el.clock_freqs.spec == ...
        assert el.clock_freqs.ge0 == 470400000000000.0
        assert el.clock_freqs.ge1 == 470395000000000.0
        # assert el.clock_freqs.ionization == ...

        assert el.reset.amplitude == 0.001
        assert el.reset.duration == 5e-05

        assert el.charge_reset.amplitude == 0.001
        assert el.charge_reset.duration == 2e-05

        assert el.measure.pulse_amplitude == 0.001
        assert el.measure.pulse_duration == 2e-05
        assert el.measure.acq_duration == 5e-05
        assert el.measure.acq_delay == 0
        # assert el.measure.acq_channel == ...
        assert el.measure.time_source == "first"
        assert el.measure.time_ref == "start"

        assert el.pulse_compensation.max_compensation_amp == 0.1
        assert el.pulse_compensation.time_grid == 4e-09
        assert el.pulse_compensation.sampling_rate == 1000000000.0

        assert el.cr_count.readout_pulse_amplitude == 0.001
        assert el.cr_count.spinpump_pulse_amplitude == 0.001
        assert el.cr_count.readout_pulse_duration == 2e-05
        assert el.cr_count.spinpump_pulse_duration == 2e-05
        assert el.cr_count.acq_duration == 5e-05
        assert el.cr_count.acq_delay == 0
        assert el.cr_count.acq_channel == 0

        assert el.rxy.amp180 == 0.5
        assert el.rxy.skewness == 0
        assert el.rxy.duration == 2e-08
        assert el.rxy.pulse_shape == "SkewedHermitePulse"


def test_quantum_device_edge_yaml_serialization():
    """Ensure that edges can be deserialized correctly from YAML."""
    spin_qd_yaml = """
        !QuantumDevice
        name: spins
        elements:
          q0: !BasicSpinElement
            name: q0
            reset:
              duration: 0.0001
          q1: !BasicSpinElement
            name: q1
            reset:
              duration: 0.0002
        edges:
          q0_q1: !SpinEdge
            parent_element_name: q0
            child_element_name: q1
        cfg_sched_repetitions: 1024
    """
    qd = QuantumDevice.from_yaml(spin_qd_yaml)

    assert isinstance(qd.elements["q0"], BasicSpinElement)
    assert isinstance(qd.elements["q1"], BasicSpinElement)
    assert isinstance(qd.edges["q0_q1"], SpinEdge)


def test_from_json_file_with_old_quantify_json_raises_invalid_config_error() -> None:
    json_content = """
    {
        "deserialization_type": "quantify_scheduler.device_under_test.quantum_device.QuantumDevice",
        "data": {
        }
    }
    """

    with (
        patch.object(
            QuantumDevice,
            "from_json",
            side_effect=TypeError("missing 1 required positional argument"),
        ),
        patch("builtins.open", mock_open(read_data=json_content)),
        pytest.raises(InvalidQuantumDeviceConfigurationError),
    ):
        QuantumDevice.from_json_file("dummy.json")
