import json
import math

import numpy as np
import pytest

from qblox_scheduler import TimeableSchedule
from qblox_scheduler.backends.circuit_to_device import DeviceCompilationConfig
from qblox_scheduler.backends.graph_compilation import SerialCompiler
from qblox_scheduler.device_under_test.quantum_device import QuantumDevice
from qblox_scheduler.device_under_test.spin_element import BasicSpinElement, ChargeSensor
from qblox_scheduler.device_under_test.transmon_element import BasicTransmonElement
from qblox_scheduler.operations.gate_library import Measure
from qblox_scheduler.structure.model import SchedulerBaseModel
from qblox_scheduler.structure.types import _NDArrayPydanticAnnotation


@pytest.fixture
def dev():
    dev = QuantumDevice("dev")
    yield dev


@pytest.fixture
def transmon_element():
    return BasicTransmonElement("q0")


@pytest.fixture
def spin_element():
    return BasicSpinElement("q0")


@pytest.fixture
def charge_sensor():
    return ChargeSensor("cs0")


qubit_params = [
    (
        "transmon_element",
        {
            "clock": "f01",
        },
    ),
    (
        "spin_element",
        {
            "clock": "f_larmor",
            "qubit_specific_param": {
                "gate_pulse_amp": {"settable": 0.1, "gettable": 0.1},
                "gate_port": {"settable": None, "gettable": "q0:gt"},
            },
        },
    ),
    (
        "charge_sensor",
        {
            "clock": "ro",
        },
    ),
]


@pytest.mark.parametrize(["qubit_fixture", "expected_values"], qubit_params)
class TestQubitOperations:
    def test_qubit_name(
        self,
        qubit_fixture,
        expected_values,  # noqa: ARG002  # Mark as unused
        request,
    ):
        q0 = request.getfixturevalue(qubit_fixture)
        if isinstance(q0, ChargeSensor):
            assert q0.name == "cs0"
        else:
            assert q0.name == "q0"

    def test_generate_device_config_part_of_device(
        self, qubit_fixture, expected_values, dev: QuantumDevice, request
    ) -> None:
        q0 = request.getfixturevalue(qubit_fixture)

        q0.measure.pulse_type = "SquarePulse"
        q0.measure.pulse_duration = 400e-9

        dev.add_element(q0)
        dev_cfg = dev.generate_device_config()

        assert isinstance(dev_cfg, DeviceCompilationConfig)

        # Assert values in the right place in config
        assert dev_cfg.elements[q0.name]["measure"].factory_kwargs["pulse_type"] == "SquarePulse"
        assert dev_cfg.elements[q0.name]["measure"].factory_kwargs["pulse_duration"] == 400e-9
        # qblox-scheduler is inconsistent with clock naming and frequency naming between
        # device elements
        if isinstance(q0, (BasicTransmonElement, BasicSpinElement)):
            if isinstance(q0, BasicTransmonElement):
                expected_clock = q0.name + "." + expected_values["clock"][1:]
            else:
                expected_clock = q0.name + "." + expected_values["clock"]

            assert dev_cfg.elements[q0.name]["Rxy"].factory_kwargs["clock"] == expected_clock
            assert dev_cfg.elements[q0.name]["Rxy"].gate_info_factory_kwargs == [
                "theta",
                "phi",
            ]

    def test_generate_device_config(
        self,
        qubit_fixture,
        expected_values,  # noqa: ARG002  # Mark as unused
        request,
    ):
        q0 = request.getfixturevalue(qubit_fixture)
        _ = q0.generate_device_config()

    @pytest.mark.parametrize(
        "readout_frequency, mw_frequency, acq_delay, pulse_amp",
        [
            (8.0e9, 8.2e9, 100e-9, 0.1),
        ],
    )
    def test_device_element_serialization(
        self,
        qubit_fixture,
        expected_values,
        readout_frequency,
        mw_frequency,
        acq_delay,
        pulse_amp,
        request,
    ):
        """
        Tests the serialization process of various :class:(qubit Elements) by comparing the
        parameter values of the submodules of the original :class: object and
        the serialized counterpart.
        """
        q0 = request.getfixturevalue(qubit_fixture)

        def is_serialized_ndarray(obj):
            return isinstance(obj, dict) and obj.keys() == {"data", "shape", "dtype"}

        q0.clock_freqs.readout = readout_frequency
        q0.measure.acq_delay = acq_delay
        q0.measure.reference_magnitude.dBm = -10

        if isinstance(q0, (BasicTransmonElement, BasicSpinElement)):
            q0.rxy.amp180 = pulse_amp
            q0.rxy.reference_magnitude.dBm = -10
            clock = expected_values["clock"]
            setattr(q0.clock_freqs, clock, mw_frequency)

            if isinstance(q0, BasicTransmonElement):
                q0.clock_freqs.f12 = 0

        q0_as_dict = json.loads(q0.to_json())
        assert q0_as_dict.__class__ is dict
        assert q0_as_dict["element_type"] == q0.__class__.__name__

        # Check that all original submodule params match their serialized counterpart
        for submodule_name, submodule in q0.submodules.items():
            for parameter_name, expected_val in submodule.parameters.items():
                val = q0_as_dict[submodule_name][parameter_name]

                if is_serialized_ndarray(val):
                    expected_val = _NDArrayPydanticAnnotation.ndarray_to_dict(expected_val)  # noqa: PLW2901
                if isinstance(expected_val, SchedulerBaseModel):
                    expected_val = expected_val.to_dict()  # noqa: PLW2901

                np.testing.assert_equal(val, expected_val, strict=True)

        # Check that all serialized submodule params match the original
        for submodule_name, submodule_data in q0_as_dict.items():
            if submodule_name in ("name", "element_type"):
                continue
            for parameter_name, parameter_val in submodule_data.items():
                expected_parameter_val = getattr(q0.submodules[submodule_name], parameter_name)

                if is_serialized_ndarray(parameter_val):
                    expected_parameter_val = _NDArrayPydanticAnnotation.ndarray_to_dict(
                        expected_parameter_val
                    )
                if isinstance(expected_parameter_val, SchedulerBaseModel):
                    expected_parameter_val = expected_parameter_val.to_dict()

                np.testing.assert_equal(parameter_val, expected_parameter_val, strict=True)

    def test_device_element_deserialization(
        self,
        qubit_fixture,
        expected_values,  # noqa: ARG002
        dev: QuantumDevice,
        get_subschedule_operation,
        request,
    ):
        """
        Tests the deserialization process of various :class:(qubit Elements) by comparing the
        operations inside compiled schedules of the original and the deserialized
        class object.
        """
        q0 = request.getfixturevalue(qubit_fixture)
        q0.measure.acq_channel = 0
        q0.measure.pulse_amp = 0.05
        q0.clock_freqs.readout = 3e9
        dev.add_element(q0)

        sched = TimeableSchedule("test_device_element_deserialization")
        sched.add(Measure(q0.name))

        compiler = SerialCompiler(name="compiler")
        compiled_sched_q0 = compiler.compile(
            schedule=sched, config=dev.generate_compilation_config()
        )

        dev.remove_element(f"{q0.name}")

        q0_as_str = q0.to_json()
        assert q0_as_str.__class__ is str

        expected_class_name = f"{q0.__class__.__module__}.{q0.__class__.__name__}"

        deserialized_q0 = type(q0).from_json(q0_as_str)
        class_name = type(deserialized_q0).__module__ + "." + type(deserialized_q0).__qualname__
        assert class_name == expected_class_name

        dev.add_element(deserialized_q0)

        compiled_sched_deserialized_q0 = compiler.compile(
            schedule=sched, config=dev.generate_compilation_config()
        )
        assert len(compiled_sched_deserialized_q0.schedulables) == len(
            compiled_sched_q0.schedulables
        )
        assert (
            get_subschedule_operation(compiled_sched_deserialized_q0, [0]).operations
            == get_subschedule_operation(compiled_sched_q0, [0]).operations
        ), (
            f"Compiled operations of deserialized '{deserialized_q0.name}' "
            f"does not match the original's"
        )

    def test_reference_magnitude_overwrite_units(
        self,
        qubit_fixture,
        expected_values,  # noqa: ARG002  # Mark as unused
        request,
    ):
        """
        Tests that the amplitude reference parameters get correctly overwritten when you
        call the set method of a different unit parameter
        """

        q0 = request.getfixturevalue(qubit_fixture)

        if isinstance(q0, ChargeSensor):
            pytest.skip("This test is not relevant for ChargeSensor because no module rxy")
        # All units should initially be nan
        assert math.isnan(q0.rxy.reference_magnitude.dBm)
        assert math.isnan(q0.rxy.reference_magnitude.V)

        # Set dBm unit
        q0.rxy.reference_magnitude.dBm = -10
        assert q0.rxy.reference_magnitude.dBm == -10
        assert math.isnan(q0.rxy.reference_magnitude.V)

        # Set V unit
        q0.rxy.reference_magnitude.V = 10e-3
        assert q0.rxy.reference_magnitude.V == 10e-3
        assert math.isnan(q0.rxy.reference_magnitude.dBm)

        assert q0.rxy.reference_magnitude.get_val_unit() == (10e-3, "V")

        # Set A unit
        q0.rxy.reference_magnitude.A = 1e-3
        assert q0.rxy.reference_magnitude.A == 1e-3
        assert math.isnan(q0.rxy.reference_magnitude.V)

        assert q0.rxy.reference_magnitude.get_val_unit() == (1e-3, "A")

        # Set nan
        q0.rxy.reference_magnitude.V = float("nan")

        assert math.isnan(q0.rxy.reference_magnitude.V)
        assert q0.rxy.reference_magnitude.A == 1e-3

    def test_generate_config_measure(self, qubit_fixture, expected_values, request):
        """Setting values updates the correct values in the config."""
        q0 = request.getfixturevalue(qubit_fixture)
        # Set values for measure
        q0.measure.pulse_amp = 0.1234
        q0.measure.pulse_duration = 300e-6
        q0.measure.acq_channel = 123
        q0.measure.acq_delay = 13e-6
        q0.measure.integration_time = 8e-7
        q0.measure.reset_clock_phase = False

        if "qubit_specific_param" in expected_values:
            for key in expected_values["qubit_specific_param"]:
                if expected_values["qubit_specific_param"][key]["settable"] is not None:
                    setattr(
                        q0.measure, key, expected_values["qubit_specific_param"][key]["settable"]
                    )

        dev_cfg = q0.generate_device_config()
        cfg_measure = dev_cfg.elements[q0.name]["measure"]

        # Assert values are in right place
        assert cfg_measure.factory_kwargs["port"] == f"{q0.name}:res"
        assert cfg_measure.factory_kwargs["clock"] == f"{q0.name}.ro"
        assert cfg_measure.factory_kwargs["pulse_type"] == "SquarePulse"
        assert cfg_measure.factory_kwargs["pulse_amp"] == 0.1234
        assert cfg_measure.factory_kwargs["pulse_duration"] == 300e-6
        assert cfg_measure.factory_kwargs["acq_delay"] == 13e-6
        assert cfg_measure.factory_kwargs["acq_duration"] == 8e-7
        assert cfg_measure.factory_kwargs["acq_channel"] == 123
        assert not cfg_measure.factory_kwargs["reset_clock_phase"]

        if "qubit_specific_param" in expected_values:
            for key in expected_values["qubit_specific_param"]:
                assert (
                    cfg_measure.factory_kwargs[key]
                    == expected_values["qubit_specific_param"][key]["gettable"]
                )

        # Changing values of the measure
        q0.measure.acq_channel = "ch_123"

        dev_cfg = q0.generate_device_config()
        cfg_measure = dev_cfg.elements[q0.name]["measure"]

        # Assert values are in right place
        assert cfg_measure.factory_kwargs["acq_channel"] == "ch_123"
