# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
"""Tests for the analysis helpers module."""

import pytest
import xarray
from xarray import DataArray, Dataset

from qblox_scheduler.analysis.helpers import acq_coords_to_dims


def test_acq_coords_to_dims_data_array_one_dim():
    data = DataArray(
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
        dims=["acq_index_0"],
        coords={
            "acq_index_0": [0, 1, 2, 3, 4, 5],
            "freq": ("acq_index_0", [1000, 2000, 3000, 4000, 5000, 6000]),
            "extra": ("acq_index_0", [11, 12, 13, 14, 15, 16]),
        },
        attrs={"acq_protocol": "SSBIntegrationComplex", "acq_index_dim_name": "acq_index_0"},
    )
    converted_data = acq_coords_to_dims(data, coords=["freq"])
    expected_converted_data = DataArray(
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
        dims=["freq"],
        coords={
            "freq": [1000, 2000, 3000, 4000, 5000, 6000],
            "extra": ("freq", [11, 12, 13, 14, 15, 16]),
        },
        attrs={"acq_protocol": "SSBIntegrationComplex", "acq_index_dim_name": "acq_index_0"},
    )
    xarray.testing.assert_identical(converted_data, expected_converted_data)


def test_acq_coords_to_dims_data_array_multi_dim():
    data = DataArray(
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
        dims=["acq_index_0"],
        coords={
            "acq_index_0": [0, 1, 2, 3, 4, 5],
            "freq": ("acq_index_0", [1000, 1000, 1000, 2000, 2000, 2000]),
            "amp": ("acq_index_0", [0.2, 0.4, 0.6, 0.2, 0.4, 0.6]),
            "extra": ("acq_index_0", [11, 12, 13, 14, 15, 16]),
        },
        attrs={"acq_protocol": "SSBIntegrationComplex", "acq_index_dim_name": "acq_index_0"},
    )
    converted_data = acq_coords_to_dims(data, coords=["freq", "amp"])
    expected_converted_data = DataArray(
        [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        dims=["freq", "amp"],
        coords={
            "freq": [1000, 2000],
            "amp": [0.2, 0.4, 0.6],
            "extra": (("freq", "amp"), [[11, 12, 13], [14, 15, 16]]),
        },
        attrs={"acq_protocol": "SSBIntegrationComplex", "acq_index_dim_name": "acq_index_0"},
    )
    xarray.testing.assert_identical(converted_data, expected_converted_data)


def test_acq_coords_to_dims_data_array_with_repetitions_one_dim():
    data = DataArray(
        [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        dims=["repetitions", "acq_index_0"],
        coords={
            "acq_index_0": [0, 1, 2],
            "repetitions": [0, 1],
            "freq": ("acq_index_0", [1000, 2000, 3000]),
            "extra": ("acq_index_0", [11, 12, 13]),
        },
        attrs={"acq_protocol": "SSBIntegrationComplex", "acq_index_dim_name": "acq_index_0"},
    )
    converted_data = acq_coords_to_dims(data, coords=["freq"])
    expected_converted_data = DataArray(
        [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        dims=["repetitions", "freq"],
        coords={
            "repetitions": [0, 1],
            "freq": [1000, 2000, 3000],
            "extra": ("freq", [11, 12, 13]),
        },
        attrs={"acq_protocol": "SSBIntegrationComplex", "acq_index_dim_name": "acq_index_0"},
    )
    xarray.testing.assert_identical(converted_data, expected_converted_data)


def test_acq_coords_to_dims_data_array_with_repetitions_multidim():
    data = DataArray(
        [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6], [0.7, 0.8, 0.9, 1.0, 1.1, 1.2]],
        dims=["repetitions", "acq_index_0"],
        coords={
            "acq_index_0": [0, 1, 2, 3, 4, 5],
            "repetitions": [0, 1],
            "freq": ("acq_index_0", [1000, 1000, 1000, 2000, 2000, 2000]),
            "amp": ("acq_index_0", [0.2, 0.4, 0.6, 0.2, 0.4, 0.6]),
            "extra": ("acq_index_0", [11, 12, 13, 14, 15, 16]),
        },
        attrs={"acq_protocol": "SSBIntegrationComplex", "acq_index_dim_name": "acq_index_0"},
    )
    converted_data = acq_coords_to_dims(data, coords=["freq", "amp"])
    expected_converted_data = DataArray(
        [[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]], [[0.7, 0.8, 0.9], [1.0, 1.1, 1.2]]],
        dims=["repetitions", "freq", "amp"],
        coords={
            "repetitions": [0, 1],
            "freq": [1000, 2000],
            "amp": [0.2, 0.4, 0.6],
            "extra": (("freq", "amp"), [[11, 12, 13], [14, 15, 16]]),
        },
        attrs={"acq_protocol": "SSBIntegrationComplex", "acq_index_dim_name": "acq_index_0"},
    )
    xarray.testing.assert_identical(converted_data, expected_converted_data)


def test_acq_coords_to_dims_raise_unknown_dims():
    data = DataArray(
        [[0.1, 0.2], [0.3, 0.4]],
        dims=["acq_index_0", "acq_index_1"],
        coords={
            "acq_index_0": [0, 1],
            "acq_index_1": [0, 1],
            "freq": ("acq_index_0", [1000, 2000]),
        },
        attrs={"acq_protocol": "SSBIntegrationComplex"},
    )
    with pytest.raises(
        ValueError,
        match="Attempting to convert acquisition data to multidimensional, "
        "acq_index dimension not found.",
    ):
        acq_coords_to_dims(data, coords=["freq"])


def test_acq_coords_to_dims_raise_empty_coords():
    data = DataArray(
        [0.1, 0.2],
        dims=["acq_index_0"],
        coords={
            "acq_index_0": [0, 1],
            "freq": ("acq_index_0", [1000, 2000]),
        },
        attrs={"acq_protocol": "SSBIntegrationComplex", "acq_index_dim_name": "acq_index_0"},
    )
    with pytest.raises(
        ValueError,
        match="Attempting to convert acquisition data to multidimensional, "
        "'coords' cannot be empty.",
    ):
        acq_coords_to_dims(data, coords=[])


def test_acq_coords_to_dims_dataset():
    data_0 = DataArray(
        [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6], [0.7, 0.8, 0.9, 1.0, 1.1, 1.2]],
        dims=["repetitions", "acq_index_0"],
        coords={
            "acq_index_0": [0, 1, 2, 3, 4, 5],
            "repetitions": [0, 1],
            "freq_0": ("acq_index_0", [1000, 1000, 1000, 2000, 2000, 2000]),
            "amp_0": ("acq_index_0", [0.2, 0.4, 0.6, 0.2, 0.4, 0.6]),
            "extra_0": ("acq_index_0", [11, 12, 13, 14, 15, 16]),
        },
        attrs={"acq_protocol": "SSBIntegrationComplex", "acq_index_dim_name": "acq_index_0"},
    )
    data_1 = DataArray(
        [0.1, 0.2, 0.3, 0.4],
        dims=["acq_index_1"],
        coords={
            "acq_index_1": [0, 1, 2, 3],
            "freq_1": ("acq_index_1", [1000, 1000, 2000, 2000]),
            "amp_1": ("acq_index_1", [0.2, 0.4, 0.2, 0.4]),
            "extra_1": ("acq_index_1", [11, 12, 13, 14]),
        },
        attrs={"acq_protocol": "SSBIntegrationComplex", "acq_index_dim_name": "acq_index_1"},
    )
    data = Dataset({"acq_channel_0": data_0, "acq_channel_1": data_1})

    converted_data = acq_coords_to_dims(
        data, coords=["freq_0", "amp_0"], acq_channels=["acq_channel_0"]
    )

    expected_converted_data_0 = DataArray(
        [[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]], [[0.7, 0.8, 0.9], [1.0, 1.1, 1.2]]],
        dims=["repetitions", "freq_0", "amp_0"],
        coords={
            "repetitions": [0, 1],
            "freq_0": [1000, 2000],
            "amp_0": [0.2, 0.4, 0.6],
            "extra_0": (("freq_0", "amp_0"), [[11, 12, 13], [14, 15, 16]]),
        },
        attrs={"acq_protocol": "SSBIntegrationComplex", "acq_index_dim_name": "acq_index_0"},
    )
    expected_converted_data = Dataset(
        {"acq_channel_0": expected_converted_data_0, "acq_channel_1": data_1}
    )

    xarray.testing.assert_identical(converted_data, expected_converted_data)
