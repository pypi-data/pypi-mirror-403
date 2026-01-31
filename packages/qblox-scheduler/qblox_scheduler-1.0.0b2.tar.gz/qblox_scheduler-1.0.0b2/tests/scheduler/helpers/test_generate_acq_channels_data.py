# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch

import pytest

from qblox_scheduler.backends import SerialCompiler
from qblox_scheduler.enums import BinMode
from qblox_scheduler.helpers.generate_acq_channels_data import (
    AcquisitionIndices,
    generate_acq_channels_data,
)
from qblox_scheduler.operations.acquisition_library import (
    NumericalSeparatedWeightedIntegration,
    NumericalWeightedIntegration,
    SSBIntegrationComplex,
    ThresholdedAcquisition,
    Trace,
    TriggerCount,
    WeightedIntegratedSeparated,
    WeightedThresholdedAcquisition,
)
from qblox_scheduler.operations.control_flow_library import LoopOperation
from qblox_scheduler.operations.expressions import DType
from qblox_scheduler.operations.loop_domains import linspace
from qblox_scheduler.schedules.schedule import (
    AcquisitionChannelData,
    Schedulable,
    TimeableSchedule,
)


@pytest.mark.parametrize(
    "protocol,protocol_str,protocol_opt_args",
    [
        (
            SSBIntegrationComplex,
            "SSBIntegrationComplex",
            {"duration": 1e-6},
        ),
        (
            ThresholdedAcquisition,
            "ThresholdedAcquisition",
            {"duration": 1e-6},
        ),
        (
            WeightedThresholdedAcquisition,
            "WeightedThresholdedAcquisition",
            {"weights_a": [0.5], "weights_b": [0.5]},
        ),
        (
            WeightedIntegratedSeparated,
            "WeightedIntegratedSeparated",
            {"duration": 1e-6, "waveform_a": [0.5], "waveform_b": [0.5]},
        ),
        (
            NumericalSeparatedWeightedIntegration,
            "NumericalSeparatedWeightedIntegration",
            {"weights_a": [0.5], "weights_b": [0.5]},
        ),
        (
            NumericalWeightedIntegration,
            "NumericalWeightedIntegration",
            {"weights_a": [0.5], "weights_b": [0.5]},
        ),
    ],
)
def test_binned_average(
    mock_setup_basic_transmon_with_standard_params,
    protocol,
    protocol_str,
    protocol_opt_args,
):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    schedule = TimeableSchedule("Test schedule", repetitions=2)
    schedulables: list[Schedulable] = []

    schedulables.append(
        schedule.add(
            protocol(
                acq_channel=0,
                bin_mode=BinMode.AVERAGE,
                coords={"amp": 0.1, "freq": 1.0},
                port="q0:res",
                clock="q0.ro",
                **protocol_opt_args,
            )
        )
    )
    schedulables.append(
        schedule.add(
            protocol(
                acq_channel=0,
                bin_mode=BinMode.AVERAGE,
                coords={"amp": 0.2, "freq": 2.0},
                port="q0:res",
                clock="q0.ro",
                **protocol_opt_args,
            )
        )
    )
    schedulables.append(
        schedule.add(
            protocol(
                acq_channel=1,
                bin_mode=BinMode.AVERAGE,
                coords={"amp": 0.3, "freq": 3.0},
                port="q0:res",
                clock="q0.ro",
                **protocol_opt_args,
            )
        )
    )
    schedulables.append(
        schedule.add(
            protocol(
                acq_channel=1,
                bin_mode=BinMode.AVERAGE,
                coords={"amp": 0.4, "freq": 4.0},
                port="q0:res",
                clock="q0.ro",
                **protocol_opt_args,
            )
        )
    )
    schedulables.append(
        schedule.add(
            protocol(
                acq_channel=1,
                bin_mode=BinMode.AVERAGE,
                coords=None,
                port="q0:res",
                clock="q0.ro",
                **protocol_opt_args,
            )
        )
    )
    schedulables.append(
        schedule.add(
            protocol(
                acq_channel=1,
                bin_mode=BinMode.AVERAGE,
                coords={"amp": 0.6, "freq": 6.0},
                port="q0:res",
                clock="q0.ro",
                **protocol_opt_args,
            )
        )
    )
    schedulables.append(
        schedule.add(
            protocol(
                acq_channel=2,
                bin_mode=BinMode.AVERAGE,
                coords={"amp": 0.7, "freq": 7.0},
                port="q0:res",
                clock="q0.ro",
                **protocol_opt_args,
            )
        )
    )

    compiler = SerialCompiler("test")
    partially_compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    acq_channels_data, schedulable_label_to_acq_index = generate_acq_channels_data(
        partially_compiled_sched
    )

    expected_acq_channels_data = {
        0: AcquisitionChannelData(
            acq_index_dim_name="acq_index_0",
            protocol=protocol_str,
            bin_mode=BinMode.AVERAGE,
            coords=[{"amp": 0.1, "freq": 1.0}, {"amp": 0.2, "freq": 2.0}],
        ),
        1: AcquisitionChannelData(
            acq_index_dim_name="acq_index_1",
            protocol=protocol_str,
            bin_mode=BinMode.AVERAGE,
            coords=[
                {"amp": 0.3, "freq": 3.0},
                {"amp": 0.4, "freq": 4.0},
                {},
                {"amp": 0.6, "freq": 6.0},
            ],
        ),
        2: AcquisitionChannelData(
            acq_index_dim_name="acq_index_2",
            protocol=protocol_str,
            bin_mode=BinMode.AVERAGE,
            coords=[{"amp": 0.7, "freq": 7.0}],
        ),
    }

    expected_schedulable_label_to_acq_index = {
        (schedulables[0]["name"],): AcquisitionIndices(0, None, 1),
        (schedulables[1]["name"],): AcquisitionIndices(1, None, 1),
        (schedulables[2]["name"],): AcquisitionIndices(0, None, 1),
        (schedulables[3]["name"],): AcquisitionIndices(1, None, 1),
        (schedulables[4]["name"],): AcquisitionIndices(2, None, 1),
        (schedulables[5]["name"],): AcquisitionIndices(3, None, 1),
        (schedulables[6]["name"],): AcquisitionIndices(0, None, 1),
    }

    assert expected_acq_channels_data == acq_channels_data
    assert expected_schedulable_label_to_acq_index == schedulable_label_to_acq_index


@pytest.mark.parametrize(
    "protocol,protocol_str,protocol_opt_args",
    [
        (
            SSBIntegrationComplex,
            "SSBIntegrationComplex",
            {"duration": 1e-6},
        ),
        (
            ThresholdedAcquisition,
            "ThresholdedAcquisition",
            {"duration": 1e-6},
        ),
        (
            WeightedThresholdedAcquisition,
            "WeightedThresholdedAcquisition",
            {"weights_a": [0.5], "weights_b": [0.5]},
        ),
        (
            WeightedIntegratedSeparated,
            "WeightedIntegratedSeparated",
            {"duration": 1e-6, "waveform_a": [0.5], "waveform_b": [0.5]},
        ),
        (
            NumericalSeparatedWeightedIntegration,
            "NumericalSeparatedWeightedIntegration",
            {"weights_a": [0.5], "weights_b": [0.5]},
        ),
        (
            NumericalWeightedIntegration,
            "NumericalWeightedIntegration",
            {"weights_a": [0.5], "weights_b": [0.5]},
        ),
    ],
)
def test_binned_append(
    mock_setup_basic_transmon_with_standard_params,
    protocol,
    protocol_str,
    protocol_opt_args,
):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    schedulables: list[Schedulable] = []

    schedule = TimeableSchedule("Test schedule", repetitions=2)

    schedulables.append(
        schedule.add(
            protocol(
                acq_channel=0,
                bin_mode=BinMode.APPEND,
                coords={"amp": 0.1, "freq": 1.0},
                port="q0:res",
                clock="q0.ro",
                **protocol_opt_args,
            )
        )
    )
    schedulables.append(
        schedule.add(
            protocol(
                acq_channel=0,
                bin_mode=BinMode.APPEND,
                coords=None,
                port="q0:res",
                clock="q0.ro",
                **protocol_opt_args,
            )
        )
    )
    schedulables.append(
        schedule.add(
            protocol(
                acq_channel=0,
                bin_mode=BinMode.APPEND,
                coords={"amp": 0.3, "freq": 3.0},
                port="q0:res",
                clock="q0.ro",
                **protocol_opt_args,
            )
        )
    )

    compiler = SerialCompiler("test")
    partially_compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    acq_channels_data, schedulable_label_to_acq_index = generate_acq_channels_data(
        partially_compiled_sched
    )

    expected_acq_channels_data = {
        0: AcquisitionChannelData(
            acq_index_dim_name="acq_index_0",
            protocol=protocol_str,
            bin_mode=BinMode.APPEND,
            coords=[
                {"amp": 0.1, "freq": 1.0},
                {},
                {"amp": 0.3, "freq": 3.0},
            ],
        ),
    }

    expected_schedulable_label_to_acq_index = {
        (schedulables[0]["name"],): AcquisitionIndices(0, [], 1),
        (schedulables[1]["name"],): AcquisitionIndices(1, [], 1),
        (schedulables[2]["name"],): AcquisitionIndices(2, [], 1),
    }

    assert expected_acq_channels_data == acq_channels_data
    assert expected_schedulable_label_to_acq_index == schedulable_label_to_acq_index


@pytest.mark.parametrize(
    "protocol,protocol_str,protocol_opt_args",
    [
        (
            SSBIntegrationComplex,
            "SSBIntegrationComplex",
            {"duration": 1e-6},
        ),
        (
            ThresholdedAcquisition,
            "ThresholdedAcquisition",
            {"duration": 1e-6},
        ),
        (
            WeightedThresholdedAcquisition,
            "WeightedThresholdedAcquisition",
            {"weights_a": [0.5], "weights_b": [0.5]},
        ),
        (
            WeightedIntegratedSeparated,
            "WeightedIntegratedSeparated",
            {"duration": 1e-6, "waveform_a": [0.5], "waveform_b": [0.5]},
        ),
        (
            NumericalSeparatedWeightedIntegration,
            "NumericalSeparatedWeightedIntegration",
            {"weights_a": [0.5], "weights_b": [0.5]},
        ),
        (
            NumericalWeightedIntegration,
            "NumericalWeightedIntegration",
            {"weights_a": [0.5], "weights_b": [0.5]},
        ),
    ],
)
def test_binned_append_loop(
    mock_setup_basic_transmon_with_standard_params,
    protocol,
    protocol_str,
    protocol_opt_args,
):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    schedule = TimeableSchedule("Schedule", repetitions=2)

    inner_sched = TimeableSchedule("Inner schedule")

    inner_inner_sched = TimeableSchedule("Inner inner schedule")
    inner_inner_sched.add(
        protocol(
            acq_channel=0,
            bin_mode=BinMode.APPEND,
            coords={"amp": 0.1, "freq": 1.0},
            port="q0:res",
            clock="q0.ro",
            **protocol_opt_args,
        )
    )
    inner_sched.add(LoopOperation(inner_inner_sched, repetitions=4))
    schedule.add(LoopOperation(inner_sched, repetitions=3))

    compiler = SerialCompiler("test")
    partially_compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    acq_channels_data, schedulable_label_to_acq_index = generate_acq_channels_data(
        partially_compiled_sched
    )

    expected_acq_channels_data = {
        0: AcquisitionChannelData(
            acq_index_dim_name="acq_index_0",
            protocol=protocol_str,
            bin_mode=BinMode.APPEND,
            coords=[{"loop_repetition_0": lr, "amp": 0.1, "freq": 1.0} for lr in range(4 * 3)],
        ),
    }

    def _first_key(d: dict):
        return list(d.keys())[0]

    def _first_val(d: dict):
        return list(d.values())[0]

    outer_schedulable_name = _first_key(partially_compiled_sched.schedulables)
    inner_schedulable_name = _first_key(
        _first_val(partially_compiled_sched.operations).body.schedulables
    )
    inner_inner_schedulable_name = _first_key(
        _first_val(
            _first_val(partially_compiled_sched.operations).body.operations
        ).body.schedulables
    )
    expected_schedulable_label_to_acq_index = {
        (
            outer_schedulable_name,
            None,
            inner_schedulable_name,
            None,
            inner_inner_schedulable_name,
        ): AcquisitionIndices(0, [BinMode.APPEND, BinMode.APPEND], 12),
    }

    assert expected_acq_channels_data == acq_channels_data
    assert expected_schedulable_label_to_acq_index == schedulable_label_to_acq_index


def test_trace_and_binned(mock_setup_basic_transmon_with_standard_params):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    schedulables: list[Schedulable] = []

    schedule = TimeableSchedule("Test schedule", repetitions=2)

    schedulables.append(
        schedule.add(
            SSBIntegrationComplex(
                acq_channel=0,
                bin_mode=BinMode.AVERAGE,
                coords=None,
                port="q0:res",
                clock="q0.ro",
                duration=1e-6,
            )
        )
    )
    schedulables.append(
        schedule.add(
            Trace(
                acq_channel=1,
                bin_mode=BinMode.AVERAGE,
                coords={"amp": 0.1, "freq": 1.0},
                port="q0:res",
                clock="q0.ro",
                duration=1e-6,
            )
        )
    )

    compiler = SerialCompiler("test")
    partially_compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    acq_channels_data, schedulable_label_to_acq_index = generate_acq_channels_data(
        partially_compiled_sched
    )

    expected_acq_channels_data = {
        0: AcquisitionChannelData(
            acq_index_dim_name="acq_index_0",
            protocol="SSBIntegrationComplex",
            bin_mode=BinMode.AVERAGE,
            coords=[{}],
        ),
        1: AcquisitionChannelData(
            acq_index_dim_name="acq_index_1",
            protocol="Trace",
            bin_mode=BinMode.AVERAGE,
            coords={"amp": 0.1, "freq": 1.0},
        ),
    }

    expected_schedulable_label_to_acq_index = {
        (schedulables[0]["name"],): AcquisitionIndices(0, None, 1),
    }

    assert expected_acq_channels_data == acq_channels_data
    assert expected_schedulable_label_to_acq_index == schedulable_label_to_acq_index


def test_trigger_count_distribution(mock_setup_basic_transmon_with_standard_params):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    schedulables: list[Schedulable] = []

    schedule = TimeableSchedule("Test schedule")

    schedulables.append(
        schedule.add(
            TriggerCount(
                acq_channel=1,
                bin_mode=BinMode.DISTRIBUTION,
                port="q0:res",
                clock="q0.ro",
                duration=1e-6,
            )
        )
    )

    schedulables.append(
        schedule.add(
            TriggerCount(
                acq_channel=1,
                bin_mode=BinMode.DISTRIBUTION,
                port="q0:res",
                clock="q0.ro",
                duration=1e-6,
            )
        )
    )

    compiler = SerialCompiler("test")
    partially_compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    acq_channels_data, schedulable_label_to_acq_index = generate_acq_channels_data(
        partially_compiled_sched
    )

    expected_acq_channels_data = {
        1: AcquisitionChannelData(
            acq_index_dim_name="acq_index_1",
            protocol="TriggerCount",
            bin_mode=BinMode.DISTRIBUTION,
            coords={},
        ),
    }

    expected_schedulable_label_to_acq_index = {}

    assert expected_acq_channels_data == acq_channels_data
    assert expected_schedulable_label_to_acq_index == schedulable_label_to_acq_index


def test_trigger_count_append(mock_setup_basic_transmon_with_standard_params):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    schedulables: list[Schedulable] = []

    schedule = TimeableSchedule("Test schedule", repetitions=3)

    schedulables.append(
        schedule.add(
            TriggerCount(
                acq_channel=1,
                bin_mode=BinMode.APPEND,
                coords={"amp": 0.1, "freq": 1.0},
                port="q0:res",
                clock="q0.ro",
                duration=1e-6,
            )
        )
    )

    compiler = SerialCompiler("test")
    partially_compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    acq_channels_data, schedulable_label_to_acq_index = generate_acq_channels_data(
        partially_compiled_sched
    )

    expected_acq_channels_data = {
        1: AcquisitionChannelData(
            acq_index_dim_name="acq_index_1",
            protocol="TriggerCount",
            bin_mode=BinMode.APPEND,
            coords=[{"amp": 0.1, "freq": 1.0}],
        ),
    }

    expected_schedulable_label_to_acq_index = {
        (schedulables[0]["name"],): AcquisitionIndices(0, [], 1),
    }

    assert expected_acq_channels_data == acq_channels_data
    assert expected_schedulable_label_to_acq_index == schedulable_label_to_acq_index


def test_trigger_count_sum(mock_setup_basic_transmon_with_standard_params):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    schedulables: list[Schedulable] = []

    schedule = TimeableSchedule("Test schedule", repetitions=3)

    schedulables.append(
        schedule.add(
            TriggerCount(
                acq_channel=1,
                bin_mode=BinMode.SUM,
                coords={"amp": 0.1, "freq": 1.0},
                port="q0:res",
                clock="q0.ro",
                duration=1e-6,
            )
        )
    )

    schedulables.append(
        schedule.add(
            TriggerCount(
                acq_channel=1,
                bin_mode=BinMode.SUM,
                coords=None,
                port="q0:res",
                clock="q0.ro",
                duration=1e-6,
            )
        )
    )

    compiler = SerialCompiler("test")
    partially_compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    acq_channels_data, schedulable_label_to_acq_index = generate_acq_channels_data(
        partially_compiled_sched
    )

    expected_acq_channels_data = {
        1: AcquisitionChannelData(
            acq_index_dim_name="acq_index_1",
            protocol="TriggerCount",
            bin_mode=BinMode.SUM,
            coords=[{"amp": 0.1, "freq": 1.0}, {}],
        ),
    }

    expected_schedulable_label_to_acq_index = {
        (schedulables[0]["name"],): AcquisitionIndices(0, None, 1),
        (schedulables[1]["name"],): AcquisitionIndices(1, None, 1),
    }

    assert expected_acq_channels_data == acq_channels_data
    assert expected_schedulable_label_to_acq_index == schedulable_label_to_acq_index


def test_shared_coords_warning(
    mock_setup_basic_transmon_with_standard_params,
):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    schedule = TimeableSchedule("Test schedule", repetitions=2)
    schedulables: list[Schedulable] = []

    schedulables.append(
        schedule.add(
            SSBIntegrationComplex(
                acq_channel=0,
                bin_mode=BinMode.AVERAGE,
                coords={"amp": 0.1},
                port="q0:res",
                clock="q0.ro",
                duration=100e-9,
            )
        )
    )
    schedulables.append(
        schedule.add(
            SSBIntegrationComplex(
                acq_channel=1,
                bin_mode=BinMode.AVERAGE,
                coords={"amp": 0.2, "freq": 2.0},
                port="q0:res",
                clock="q0.ro",
                duration=100e-9,
            )
        )
    )

    compiler = SerialCompiler("test")
    partially_compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    with pytest.warns(
        match="The coords key `amp` is shared between "
        "`0` and `1`. "
        "This is not yet fully supported, please try different keys. "
        "See https://gitlab.com/quantify-os/quantify-scheduler/-/issues/497."
    ):
        _acq_channels_data, _schedulable_label_to_acq_index = generate_acq_channels_data(
            partially_compiled_sched
        )


def test_expressions_as_coords(
    mock_setup_basic_transmon_with_standard_params,
):
    quantum_device = mock_setup_basic_transmon_with_standard_params["quantum_device"]

    schedule = TimeableSchedule("Schedule", repetitions=1)

    with (
        schedule.loop(linspace(0.0, 1.0, 2, DType.AMPLITUDE)) as amp_1,
        schedule.loop(linspace(1.0, 2.0, 3, DType.AMPLITUDE)) as amp_2,
    ):
        schedule.add(
            SSBIntegrationComplex(
                acq_channel=0,
                coords={"freq": 100, "amp_1": amp_1, "amp_avg": (amp_2 + amp_1) / 2},
                acq_index=None,
                bin_mode=BinMode.APPEND,
                port="q0:res",
                clock="q0.01",
                duration=100e-9,
            )
        )

    compiler = SerialCompiler("test")
    partially_compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    acq_channels_data, _schedulable_label_to_acq_index = generate_acq_channels_data(
        partially_compiled_sched
    )

    expected_acq_channels_data = {
        0: AcquisitionChannelData(
            acq_index_dim_name="acq_index_0",
            protocol="SSBIntegrationComplex",
            bin_mode=BinMode.APPEND,
            coords=[
                {
                    "freq": 100,
                    "amp_1": 0.0,
                    "amp_avg": 0.5,
                    "loop_repetition_0": 0,
                },
                {
                    "freq": 100,
                    "amp_1": 0.0,
                    "amp_avg": 0.75,
                    "loop_repetition_0": 1,
                },
                {
                    "freq": 100,
                    "amp_1": 0.0,
                    "amp_avg": 1.0,
                    "loop_repetition_0": 2,
                },
                {
                    "freq": 100,
                    "amp_1": 1.0,
                    "amp_avg": 1.0,
                    "loop_repetition_0": 3,
                },
                {
                    "freq": 100,
                    "amp_1": 1.0,
                    "amp_avg": 1.25,
                    "loop_repetition_0": 4,
                },
                {
                    "freq": 100,
                    "amp_1": 1.0,
                    "amp_avg": 1.5,
                    "loop_repetition_0": 5,
                },
            ],
        )
    }

    assert expected_acq_channels_data == acq_channels_data
