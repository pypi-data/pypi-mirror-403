# type: ignore[reportCallIssue] # TODO: Remove after refactoring SchedulerBaseModel.__init__
# Repository: https://gitlab.com/quantify-os/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
from __future__ import annotations

import json
from unittest.mock import patch

import pytest
import xarray
import xarray as xr
from qblox_instruments.ieee488_2.cluster_dummy_transport import ClusterDummyTransport

from qblox_scheduler import (
    BasicTransmonElement,
    InstrumentCoordinator,
    QuantumDevice,
    TimeableSchedule,
)
from qblox_scheduler.analysis.data_handling import OutputDirectoryManager, _get_default_datadir
from qblox_scheduler.backends.qblox_backend import (
    QbloxHardwareCompilationConfig,
    QbloxModuleNotFoundError,
)
from qblox_scheduler.backends.types.common import (
    Connectivity,
    HardwareDescription,
    IQMixerDescription,
)
from qblox_scheduler.backends.types.qblox import (
    ClusterDescription,
    QbloxHardwareOptions,
    QCMDescription,
    QCMRFDescription,
    QRMDescription,
    QRMRFDescription,
    QTMDescription,
)
from qblox_scheduler.device_under_test.device_element import DeviceElement
from qblox_scheduler.experiments import (
    SetHardwareOption,
    SetParameter,
)
from qblox_scheduler.instrument_coordinator.components import generic
from qblox_scheduler.instrument_coordinator.components.qblox import _QTMComponent
from qblox_scheduler.operations import Measure
from qblox_scheduler.operations.expressions import DType
from qblox_scheduler.operations.gate_library import Measure
from qblox_scheduler.operations.loop_domains import linspace
from qblox_scheduler.qblox.hardware_agent import HardwareAgent
from qblox_scheduler.schedule import Schedule, TimeableSchedule
from qblox_scheduler.structure.model import Numbers, Parameter, SchedulerSubmodule
from qblox_scheduler.structure.types import Graph


@pytest.fixture
def mock_cluster(request):
    class MockModule:
        unique_index = 0  # Because module names need to be unique. Thank you qcodes

        def __init__(self, index: int, module_type: str):
            self.slot_idx = index
            self.name = f"module{MockModule.unique_index}_with_index{index}"
            MockModule.unique_index += 1
            module_type = module_type.lower()
            self.is_qtm_type = module_type == "qtm"
            self.is_qcm_type = "qcm" in module_type
            self.is_qrm_type = "qrm" in module_type
            self.is_rf_type = "rf" in module_type

    class MockCluster:
        def __init__(self, name, identifier, debug):
            self.name = name
            self.identifier = identifier
            self.debug = debug
            self.modules = []
            if hasattr(request, "param"):
                for i, instr_type in request.param.items():
                    self.modules.append(MockModule(i, instr_type))

    return patch("qblox_scheduler.qblox.hardware_agent.Cluster", MockCluster)


@pytest.mark.parametrize("as_file", [True, False])
def test_init_empty_hw_config(as_file, tmpdir):
    config = {}
    if as_file:
        path = tmpdir.join("config.json")
        path.write("{}")
        config = path.strpath
    backend = HardwareAgent(config)
    assert isinstance(backend._quantum_device, QuantumDevice)
    assert backend._quantum_device is backend.quantum_device
    assert isinstance(backend._instrument_coordinator, InstrumentCoordinator)
    assert backend._instrument_coordinator is backend.instrument_coordinator
    assert backend._quantum_device.instr_instrument_coordinator is backend._instrument_coordinator
    assert backend._hardware_configuration == {}
    assert backend._quantum_device.hardware_config is None
    with pytest.raises(TypeError, match="Hardware not initialized yet"):
        _ = backend.hardware_configuration

    # Since no dir is provided it is set to default
    assert OutputDirectoryManager.get_datadir() == _get_default_datadir(False)


def test_init_two_instances():
    backend1 = HardwareAgent(
        {
            "hardware_description": {
                "cluster_name": {"ip": "localhost", "instrument_type": "Cluster", "ref": "internal"}
            },
            "hardware_options": {},
            "connectivity": {"graph": []},
        }
    )
    backend2 = HardwareAgent(
        {
            "hardware_description": {
                "cluster_name": {"ip": "localhost", "instrument_type": "Cluster", "ref": "internal"}
            },
            "hardware_options": {},
            "connectivity": {"graph": []},
        }
    )
    assert backend1 is not backend2


def test_init_incorrect_hw_config():
    backend = HardwareAgent({"no": "checks"})
    assert backend._hardware_configuration == {"no": "checks"}


def test_connect_clusters_empty_hw_config():
    backend = HardwareAgent({})
    with pytest.raises(ValueError, match="Hardware configuration misses the hardware description"):
        backend.connect_clusters()


@pytest.mark.parametrize("as_file", [True, False])
def test_connect_clusters_empty_hw_description(as_file, tmpdir):
    config = {"hardware_description": {}, "hardware_options": {}, "connectivity": {"graph": []}}
    if as_file:
        path = tmpdir.join("config.json")
        path.write(json.dumps(config))
        config = path.strpath
    backend = HardwareAgent(config)
    backend.connect_clusters()
    created_hw_config = backend.hardware_configuration
    assert created_hw_config is backend._quantum_device.hardware_config
    assert isinstance(created_hw_config, QbloxHardwareCompilationConfig)
    assert created_hw_config.hardware_description == {}
    assert isinstance(created_hw_config.connectivity, Connectivity)
    assert len(created_hw_config.connectivity.graph.nodes) == 0


def test_connect_clusters_ip_only(mock_cluster):
    backend = HardwareAgent(
        {
            "hardware_description": {
                "cluster_name": {"ip": "localhost", "instrument_type": "Cluster", "ref": "internal"}
            },
            "hardware_options": {},
            "connectivity": {"graph": []},
        }
    )
    with mock_cluster:
        backend.connect_clusters()
    created_hw_config = backend.hardware_configuration
    assert isinstance(created_hw_config, QbloxHardwareCompilationConfig)
    assert len(created_hw_config.hardware_description) == 1
    cluster_description = created_hw_config.hardware_description["cluster_name"]
    assert isinstance(cluster_description, ClusterDescription)
    assert cluster_description.instrument_type == "Cluster"
    assert cluster_description.modules == {}
    assert cluster_description.ip == "localhost"


@pytest.mark.parametrize("mock_cluster", [{3: "QTM"}], indirect=True)
def test_connect_clusters_one_module(mock_cluster):
    backend = HardwareAgent(
        {
            "hardware_description": {
                "cluster_name": {"ip": "localhost", "instrument_type": "Cluster", "ref": "internal"}
            },
            "hardware_options": {},
            "connectivity": {"graph": []},
        }
    )
    with mock_cluster:
        backend.connect_clusters()
    created_hw_config = backend.hardware_configuration
    cluster_description = created_hw_config.hardware_description["cluster_name"]
    assert isinstance(cluster_description, ClusterDescription)
    assert len(cluster_description.modules) == 1
    assert 3 in cluster_description.modules
    assert cluster_description.modules[3] == QTMDescription()


@pytest.mark.parametrize(
    "mock_cluster",
    [{3: "QTM", 2: "New Module", 5: "QRM", 6: "QCM", 7: "QRM", 8: "QCM_RF", 1001: "QRM_RF"}],
    indirect=True,
)
def test_connect_clusters_all_modules(mock_cluster):
    backend = HardwareAgent(
        {
            "hardware_description": {
                "cluster_name": {"ip": "localhost", "instrument_type": "Cluster", "ref": "internal"}
            },
            "hardware_options": {},
            "connectivity": {"graph": []},
        }
    )
    with mock_cluster:
        backend.connect_clusters()
    created_hw_config = backend.hardware_configuration
    cluster_description = created_hw_config.hardware_description["cluster_name"]
    assert isinstance(cluster_description, ClusterDescription)
    assert cluster_description.modules == {
        3: QTMDescription(),
        5: QRMDescription(),
        6: QCMDescription(),
        7: QRMDescription(),
        8: QCMRFDescription(),
        1001: QRMRFDescription(),
    }


@pytest.mark.parametrize(
    "mock_cluster",
    [{3: "QTM", 2: "New Module", 5: "QRM", 6: "QCM", 7: "QRM", 8: "QCM_RF", 1001: "QRM_RF"}],
    indirect=True,
)
def test_connect_clusters_with_instance(mock_cluster):
    backend = HardwareAgent(
        QbloxHardwareCompilationConfig(
            hardware_description={
                "cluster_name": ClusterDescription(ip="something", ref="internal")
            },
            hardware_options=QbloxHardwareOptions(),
            connectivity=Connectivity(graph=Graph()),
        )
    )
    assert isinstance(backend.hardware_configuration, QbloxHardwareCompilationConfig)
    with mock_cluster:
        backend.connect_clusters()
    created_hw_config = backend.hardware_configuration
    cluster_description = created_hw_config.hardware_description["cluster_name"]
    assert isinstance(cluster_description, ClusterDescription)
    assert cluster_description.modules == {
        3: QTMDescription(),
        5: QRMDescription(),
        6: QCMDescription(),
        7: QRMDescription(),
        8: QCMRFDescription(),
        1001: QRMRFDescription(),
    }


@pytest.mark.parametrize("as_file", [True, False])
@pytest.mark.parametrize("mock_cluster", [{3: "QTM"}], indirect=True)
def test_connect_clusters_multiple_clusters(mock_cluster, as_file, tmpdir):
    config = {
        "hardware_description": {
            "local": {"ip": "localhost", "instrument_type": "Cluster", "ref": "internal"},
            "remote": {"ip": "remote", "instrument_type": "Cluster", "ref": "internal"},
            "not a cluster": {"instrument_type": "who knows"},
        },
        "hardware_options": {},
        "connectivity": {"graph": []},
    }
    if as_file:
        path = tmpdir.join("config.json")
        path.write(json.dumps(config))
        config = path.strpath
    backend = HardwareAgent(config)
    with mock_cluster:
        backend.connect_clusters()
    created_hw_config = backend.hardware_configuration
    assert len(created_hw_config.hardware_description) == 3
    cluster_description = created_hw_config.hardware_description["local"]
    assert isinstance(cluster_description, ClusterDescription)
    assert isinstance(created_hw_config.hardware_description["remote"], ClusterDescription)
    assert 3 in cluster_description.modules
    assert cluster_description.modules[3] == QTMDescription()
    assert cluster_description.modules == created_hw_config.hardware_description["remote"].modules
    assert type(created_hw_config.hardware_description["not a cluster"]) is HardwareDescription


def test_connect_clusters_no_ip_in_description():
    backend = HardwareAgent(
        {
            "hardware_description": {
                "cluster_name": {"instrument_type": "Cluster", "ref": "internal"}
            },
            "hardware_options": {},
            "connectivity": {"graph": []},
        }
    )

    with pytest.warns(
        UserWarning,
        match="cluster_name: Trying to instantiate cluster with ip 'None'."
        "Creating a dummy cluster.",
    ):
        backend.connect_clusters()


def test_connect_clusters_module_in_connectivity_but_not_in_cluster(mock_cluster):
    backend = HardwareAgent(
        {
            "hardware_description": {
                "cluster_name": {"ip": "somewhere", "instrument_type": "Cluster", "ref": "internal"}
            },
            "hardware_options": {},
            "connectivity": {"graph": [["cluster_name.module6.complex_output_0", "q0:mw"]]},
        }
    )
    with (
        pytest.raises(
            QbloxModuleNotFoundError,
            match="Module '6' of cluster 'cluster_name' not found in the hardware description. "
            "Please ensure all modules mentioned in the connectivity "
            "are present in the hardware description. "
            "\nThis can also be because no module at the given index exists in the cluster,"
            "yet it is defined in the connectivity.",
        ),
        mock_cluster,
    ):
        backend.connect_clusters()


def test_verify_hardware_config_when_not_initialized_yet():
    backend = HardwareAgent({})
    with pytest.raises(TypeError, match="Hardware config is not yet correctly initialized."):
        backend._verify_hardware_configuration()


def test_verify_hardware_config_when_not_connected_clusters_yet():
    backend = HardwareAgent(
        QbloxHardwareCompilationConfig(
            hardware_description={
                "cluster": ClusterDescription(ref="internal"),
                "mixer": IQMixerDescription(),
            },
            hardware_options=QbloxHardwareOptions(),
            connectivity=Connectivity(graph=Graph()),
        )
    )
    with pytest.raises(ValueError, match="Hardware config is not yet correctly initialized."):
        backend._verify_hardware_configuration()


@pytest.mark.parametrize("mock_cluster", [{3: "QTM"}], indirect=True)
def test_verify_hardware_config_module_not_installed_at_index(mock_cluster):
    backend = HardwareAgent(
        {
            "hardware_description": {
                "cluster_name": {
                    "ip": "localhost",
                    "instrument_type": "Cluster",
                    "ref": "internal",
                    "modules": {4: {"instrument_type": "QTM"}},
                }
            },
            "hardware_options": {},
            "connectivity": {"graph": []},
        }
    )
    with (
        mock_cluster,
        pytest.raises(ValueError, match="No module at index 4 installed in cluster_name."),
    ):
        backend.connect_clusters()


@pytest.mark.parametrize("mock_cluster", [{3: "QTM"}], indirect=True)
def test_verify_hardware_config_wrong_module_installed(mock_cluster):
    backend = HardwareAgent(
        {
            "hardware_description": {
                "cluster_name": {
                    "ip": "localhost",
                    "instrument_type": "Cluster",
                    "ref": "internal",
                    "modules": {3: {"instrument_type": "QCM"}},
                }
            },
            "hardware_options": {},
            "connectivity": {"graph": []},
        }
    )
    with (
        mock_cluster,
        pytest.raises(
            ValueError,
            match="Cluster `cluster_name` has a module QTM installed at index 3, "
            "not a QCM as defined manually in the hardware description.",
        ),
    ):
        backend.connect_clusters()


def test_get_clusters_no_clusters():
    config = {
        "hardware_description": {
            "not a cluster": {"instrument_type": "who knows"},
        },
        "hardware_options": {},
        "connectivity": {"graph": []},
    }
    backend = HardwareAgent(config)
    assert backend.get_clusters() == {}


@pytest.mark.parametrize("mock_cluster", [{3: "QTM"}], indirect=True)
def test_get_clusters_two_clusters(mock_cluster):
    config = {
        "hardware_description": {
            "local": {"ip": "1.2.3.4", "instrument_type": "Cluster", "ref": "internal"},
            "remote": {"ip": "1.1.2.3", "instrument_type": "Cluster", "ref": "internal"},
            "not a cluster": {"instrument_type": "who knows"},
        },
        "hardware_options": {},
        "connectivity": {"graph": []},
    }
    backend = HardwareAgent(config)
    with mock_cluster:
        clusters = backend.get_clusters()
        assert len(clusters) == 2
        assert clusters["local"].identifier == "1.2.3.4"
        assert clusters["remote"].identifier == "1.1.2.3"


@patch("qblox_scheduler.qblox.hardware_agent.SerialCompiler.compile", return_value=5)
def test_compile(compile_mock):
    hardware = HardwareAgent({})
    schedule = TimeableSchedule("sched")
    compiled_schedule = hardware.compile(schedule)
    assert compiled_schedule == 5
    compile_mock.assert_called_once_with(
        schedule=schedule,
        config=hardware._quantum_device.generate_compilation_config(),
    )


@pytest.mark.parametrize("mock_cluster", [{3: "QTM"}], indirect=True)
@patch("qblox_scheduler.qblox.hardware_agent.SerialCompiler.compile", return_value=5)
@patch("qblox_scheduler.qblox.hardware_agent.InstrumentCoordinator.prepare")
@patch("qblox_scheduler.qblox.hardware_agent.InstrumentCoordinator.start")
@patch("qblox_scheduler.qblox.hardware_agent.InstrumentCoordinator.wait_done")
@patch(
    "qblox_scheduler.qblox.hardware_agent.InstrumentCoordinator.retrieve_acquisition",
    return_value=xr.Dataset(),
)
def test_run(
    retrieve_acq_mock,
    wait_done_mock,
    start_mock,
    prepare_mock,
    compile_mock,
    mock_cluster,
    tmp_test_data_dir,
):
    config = {
        "hardware_description": {
            "name": {"ip": "1.2.3.4", "instrument_type": "Cluster", "ref": "internal"},
        },
        "hardware_options": {},
        "connectivity": {"graph": []},
    }
    hardware = HardwareAgent(config, output_dir=tmp_test_data_dir)
    schedule = TimeableSchedule("sched")

    with mock_cluster:
        hardware.run(schedule)

    compile_mock.assert_called_once()
    prepare_mock.assert_called_once_with(5)
    start_mock.assert_called_once_with()
    wait_done_mock.assert_called_once()
    retrieve_acq_mock.assert_called_once()


@pytest.mark.parametrize("mock_cluster", [{3: "QTM"}], indirect=True)
@patch("qblox_scheduler.qblox.hardware_agent.SerialCompiler.compile", return_value=5)
@patch("qblox_scheduler.qblox.hardware_agent.InstrumentCoordinator.prepare")
@patch("qblox_scheduler.qblox.hardware_agent.InstrumentCoordinator.start")
@patch("qblox_scheduler.qblox.hardware_agent.InstrumentCoordinator.wait_done")
@patch(
    "qblox_scheduler.qblox.hardware_agent.InstrumentCoordinator.retrieve_acquisition",
    return_value=xr.Dataset(),
)
def test_run_with_no_tuid(
    retrieve_acq_mock,
    wait_done_mock,
    start_mock,
    prepare_mock,
    compile_mock,
    mock_cluster,
    tmp_test_data_dir,
):
    config = {
        "hardware_description": {
            "name": {"ip": "1.2.3.4", "instrument_type": "Cluster", "ref": "internal"},
        },
        "hardware_options": {},
        "connectivity": {"graph": []},
    }
    hardware = HardwareAgent(config, output_dir=tmp_test_data_dir)
    schedule = TimeableSchedule("sched")
    with mock_cluster:
        dataset = hardware.run(schedule)

    assert dataset.attrs["tuid"] is not None
    compile_mock.assert_called_once()
    prepare_mock.assert_called_once_with(5)
    start_mock.assert_called_once_with()
    wait_done_mock.assert_called_once()
    retrieve_acq_mock.assert_called_once()


def test_incorrect_cluster_description():
    backend = HardwareAgent(
        {
            "hardware_description": {"cluster_name": 4},
            "hardware_options": {},
            "connectivity": {"graph": []},
        }
    )
    with pytest.raises(
        ValueError,
        match="Invalid hardware configuration. Missing `instrument_type` for instrument "
        "'cluster_name'",
    ):
        backend.connect_clusters()


def test_dummy_cluster():
    backend = HardwareAgent(
        {
            "hardware_description": {
                "cluster_name": {
                    "ip": None,
                    "instrument_type": "Cluster",
                    "ref": "internal",
                    "modules": {4: {"instrument_type": "QTM"}},
                }
            },
            "hardware_options": {},
            "connectivity": {"graph": []},
        }
    )
    backend.connect_clusters()
    assert isinstance(
        backend._clusters["cluster_name"]._cluster_modules["cluster_name_module4"], _QTMComponent
    )
    assert isinstance(backend._clusters["cluster_name"].cluster._transport, ClusterDummyTransport)


def test_dummy_cluster_compile_run():
    backend = HardwareAgent(
        {
            "hardware_description": {
                "cluster_name": {
                    "ip": None,
                    "instrument_type": "Cluster",
                    "ref": "internal",
                    "modules": {4: {"instrument_type": "QRM"}},
                }
            },
            "hardware_options": {},
            "connectivity": {
                "graph": [
                    ["cluster_name.module4.complex_output_0", "q0:res"],
                    ["cluster_name.module4.complex_output_0", "q0:mw"],
                ]
            },
        }
    )
    q0 = BasicTransmonElement("q0")
    q0.measure.acq_delay = 100e-9
    q0.clock_freqs.readout = 1
    backend.add_device_elements([q0])
    schedule = TimeableSchedule("sched")
    schedule.add(Measure("q0"))
    compiled_schedule = backend.compile(schedule)

    _ = backend.run(compiled_schedule)


def test_dummy_cluster_run(tmp_test_data_dir):
    backend = HardwareAgent(
        {
            "hardware_description": {
                "cluster_name": {
                    "ip": None,
                    "instrument_type": "Cluster",
                    "ref": "internal",
                    "modules": {4: {"instrument_type": "QRM"}},
                }
            },
            "hardware_options": {},
            "connectivity": {
                "graph": [
                    ["cluster_name.module4.complex_output_0", "q0:res"],
                    ["cluster_name.module4.complex_output_0", "q0:mw"],
                ]
            },
        },
        output_dir=tmp_test_data_dir,
    )
    q0 = BasicTransmonElement("q0")
    q0.measure.acq_delay = 100e-9
    q0.clock_freqs.readout = 1
    backend.add_device_elements([q0])
    schedule = TimeableSchedule("sched")
    schedule.add(Measure("q0"))
    compiled_schedule = backend.compile(schedule)

    _ = backend.run(compiled_schedule)


def test_dummy_cluster_run(tmp_test_data_dir):
    backend = HardwareAgent(
        {
            "hardware_description": {
                "cluster_name": {
                    "ip": None,
                    "instrument_type": "Cluster",
                    "ref": "internal",
                    "modules": {4: {"instrument_type": "QRM"}},
                }
            },
            "hardware_options": {},
            "connectivity": {
                "graph": [
                    ["cluster_name.module4.complex_output_0", "q0:res"],
                    ["cluster_name.module4.complex_output_0", "q0:mw"],
                ]
            },
        },
        output_dir=tmp_test_data_dir,
    )
    q0 = BasicTransmonElement("q0")
    q0.measure.acq_delay = 100e-9
    q0.clock_freqs.readout = 1
    backend.add_device_elements([q0])
    schedule = TimeableSchedule("sched")
    schedule.add(Measure("q0"))
    dataset = backend.run(schedule)
    assert isinstance(dataset, xarray.Dataset)
    assert "tuid" in dataset.attrs


def test_quantum_device_as_object():
    quantum_device = QuantumDevice("test_quantum_device")
    q0 = BasicTransmonElement("q0")

    quantum_device.add_element(q0)

    hardware_config = {
        "hardware_description": {"cluster_name": 4},
        "hardware_options": {},
        "connectivity": {"graph": []},
    }

    backend = HardwareAgent(
        hardware_config,
        quantum_device_configuration=quantum_device,
    )
    assert isinstance(backend.quantum_device, QuantumDevice)


def test_quantum_device_as_dict():
    quantum_device = QuantumDevice("test_quantum_device")
    q0 = BasicTransmonElement("q0")

    quantum_device.add_element(q0)
    quantum_device_dict = quantum_device.to_dict()

    hardware_config = {
        "hardware_description": {"cluster_name": 4},
        "hardware_options": {},
        "connectivity": {"graph": []},
    }

    backend = HardwareAgent(
        hardware_config,
        quantum_device_configuration=quantum_device_dict,
    )
    assert isinstance(backend.quantum_device, QuantumDevice)


def test_quantum_device_json(tmp_path):
    quantum_device = QuantumDevice("test_quantum_device")
    q0 = BasicTransmonElement("q0")

    quantum_device.add_element(q0)
    quantum_device_json = quantum_device.to_json_file(tmp_path)

    hardware_config = {
        "hardware_description": {"cluster_name": 4},
        "hardware_options": {},
        "connectivity": {"graph": []},
    }

    backend = HardwareAgent(
        hardware_config,
        quantum_device_configuration=quantum_device_json,
    )
    assert isinstance(backend.quantum_device, QuantumDevice)


def test_quantum_device_yaml(tmp_path):
    quantum_device = QuantumDevice("test_quantum_device")
    q0 = BasicTransmonElement("q0")

    quantum_device.add_element(q0)
    quantum_device_yaml = quantum_device.to_yaml_file(tmp_path)

    hardware_config = {
        "hardware_description": {"cluster_name": 4},
        "hardware_options": {},
        "connectivity": {"graph": []},
    }

    backend = HardwareAgent(
        hardware_config,
        quantum_device_configuration=quantum_device_yaml,
    )
    assert isinstance(backend.quantum_device, QuantumDevice)


def test_instantiate_hardware_agent_twice_with_different_modules_but_same_cluster_name():
    hw_config = {
        "version": "0.2",
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "ref": "internal",
                "modules": {"1": {"instrument_type": "QCM"}, "2": {"instrument_type": "QRM_RF"}},
            }
        },
        "hardware_options": {},
        "connectivity": {"graph": []},
    }
    backend1 = HardwareAgent(hw_config)
    backend1.get_clusters()
    hw_config["hardware_description"]["cluster0"]["modules"]["1"]["instrument_type"] = "QTM"
    del hw_config["hardware_description"]["cluster0"]["modules"]["2"]
    hw_config["hardware_description"]["cluster0"]["modules"]["3"] = {"instrument_type": "QRM"}

    backend2 = HardwareAgent(hw_config)
    backend2.get_clusters()
    cluster1 = backend1.hardware_configuration.hardware_description["cluster0"]
    cluster2 = backend2.hardware_configuration.hardware_description["cluster0"]
    assert isinstance(cluster1, ClusterDescription)
    assert isinstance(cluster2, ClusterDescription)
    assert len(cluster1.modules) == 2
    assert type(cluster1.modules[1]) is QCMDescription
    assert type(cluster1.modules[2]) is QRMRFDescription
    assert len(cluster2.modules) == 2
    assert type(cluster2.modules[1]) is QTMDescription
    assert type(cluster2.modules[3]) is QRMDescription


def test_serialize_custom_device_elements_to_yaml():
    class Foo(SchedulerSubmodule):
        bar: int = Parameter(initial_value=1, unit="", vals=Numbers(min_value=0, max_value=10))

    class Hello(DeviceElement):
        element_type: str = "Hello"

        foo: Foo

        def generate_device_config(self):
            return {
                "element_type": self.element_type,
                "foo": self.foo.generate_device_config(),
            }

    hello = Hello("hi")
    hello.foo.bar = 1

    agent = HardwareAgent({"config_type": "QbloxHardwareCompilationConfig"})
    agent.add_device_elements([hello])

    reconstructed_qd = QuantumDevice.from_yaml(agent.quantum_device.to_yaml())
    assert isinstance(reconstructed_qd.elements["hi"], Hello)
    assert reconstructed_qd.elements["hi"].to_dict() == {
        "name": "hi",
        "element_type": "Hello",
        "foo": {
            "name": "foo",
            "bar": 1,
        },
    }


def test_hardware_agent_loads_and_sets_qsm_parameters():
    hw_config = {
        "version": "0.2",
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "ref": "internal",
                "modules": {
                    "2": {"instrument_type": "QSM"},
                    "4": {"instrument_type": "QRM"},
                },
            },
        },
        "hardware_options": {
            "source_mode": {
                "cluster0.module2.io_channel0": "v_source",
                "cluster0.module2.io_channel1": "i_source",
            },
            "measure_mode": {
                "cluster0.module2.io_channel2": "fine_nanoampere",
                "cluster0.module2.io_channel3": "fine_picoampere",
            },
            "slew_rate": {
                "cluster0.module2.io_channel4": 40.0,
                "cluster0.module2.io_channel5": 50.0,
            },
            "integration_time": {
                "cluster0.module2.io_channel6": 6.0,
                "cluster0.module2.io_channel7": 7.0,
            },
            "safe_voltage_range": {
                "cluster0.module2": (-5.0, +5.0),
            },
        },
        "connectivity": {
            "graph": [
                ["cluster0.module4.complex_output_0", "q0:res"],
                ["cluster0.module4.complex_output_0", "q0:mw"],
            ]
        },
    }

    backend = HardwareAgent(hw_config)
    clusters = backend.get_clusters()

    q0 = BasicTransmonElement("q0")
    q0.measure.acq_delay = 100e-9
    q0.clock_freqs.readout = 1
    backend.add_device_elements([q0])
    schedule = TimeableSchedule("sched")
    schedule.add(Measure("q0"))
    compiled_schedule = backend.compile(schedule)

    backend.run(compiled_schedule)

    # Check that all QCoDeS parameters (and the safe voltage) have been set successfully.
    assert clusters["cluster0"].modules[1].io_channels[0].source_mode() == "v_source"
    assert clusters["cluster0"].modules[1].io_channels[1].source_mode() == "i_source"
    assert clusters["cluster0"].modules[1].io_channels[2].measure_mode() == "fine_nanoampere"
    assert clusters["cluster0"].modules[1].io_channels[3].measure_mode() == "fine_picoampere"
    assert clusters["cluster0"].modules[1].io_channels[4].slew_rate() == 40.0
    assert clusters["cluster0"].modules[1].io_channels[5].slew_rate() == 50.0
    assert clusters["cluster0"].modules[1].io_channels[6].integration_time() == 6.0
    assert clusters["cluster0"].modules[1].io_channels[7].integration_time() == 7.0
    assert all(
        chan._safe_voltage_range == (-5.0, +5.0)
        for chan in clusters["cluster0"].modules[1].io_channels
    )


def test_hardware_agent_runs_with_non_cluster_instruments(
    mock_quantum_device_basic_transmon_qblox_hardware,
):
    quantum_device = mock_quantum_device_basic_transmon_qblox_hardware
    q4 = quantum_device.get_element("q4")
    instr_coord = quantum_device.instr_instrument_coordinator
    instr_coord.add_component(generic.GenericInstrumentCoordinatorComponent(generic.DEFAULT_NAME))
    q4.clock_freqs.readout = 7.4e9

    schedule = Schedule("test hardware option")
    schedule.add(SetHardwareOption("latency_corrections", 12e-9, port="q4:mw-q4.01"))
    schedule.add(Measure("q4"))

    step = SetParameter(("rxy", "amp180"), 0.69, element="q4")
    with schedule.loop(linspace(0, 10, 11, DType.NUMBER)):
        schedule.add(step)
        schedule.add(Measure("q4"))

    hw_agent = HardwareAgent(quantum_device.hardware_config, quantum_device)

    hw_agent.run(schedule)


def test_latest_compiled_schedule(mocker):
    from qblox_scheduler.backends.graph_compilation import SerialCompiler

    compiler_spy = mocker.spy(SerialCompiler, "compile")
    agent_compile_spy = mocker.spy(HardwareAgent, "compile")

    agent = HardwareAgent(
        {
            "hardware_description": {
                "cluster_name": {
                    "ip": None,
                    "instrument_type": "Cluster",
                    "ref": "internal",
                    "modules": {4: {"instrument_type": "QRM"}},
                }
            },
            "hardware_options": {},
            "connectivity": {
                "graph": [
                    ["cluster_name.module4.complex_output_0", "q0:res"],
                    ["cluster_name.module4.complex_output_0", "q0:mw"],
                ]
            },
        }
    )
    q0 = BasicTransmonElement("q0")
    q0.measure.acq_delay = 100e-9
    q0.clock_freqs.readout = 1
    agent.add_device_elements([q0])
    schedule = TimeableSchedule("sched")
    schedule.add(Measure("q0"))

    _compiled_schedule = agent.compile(schedule)
    assert agent.latest_compiled_schedule is agent_compile_spy.spy_return
    _ = agent.run(schedule)
    assert agent.latest_compiled_schedule is compiler_spy.spy_return
    _compiled_schedule = agent.compile(schedule)
    assert agent.latest_compiled_schedule is agent_compile_spy.spy_return
