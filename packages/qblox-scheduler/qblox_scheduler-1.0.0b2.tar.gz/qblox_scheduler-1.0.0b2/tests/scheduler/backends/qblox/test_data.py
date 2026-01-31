from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import xarray as xr

from qblox_scheduler.backends.qblox.data import (
    save_to_experiment,
)


class TestSaveToExperiment:
    @pytest.fixture
    def dataset(self):
        dataset = xr.Dataset()
        data = np.array([0.1])
        coords = np.array([1e-6])

        dataset = xr.Dataset(
            data_vars={
                "y0": xr.DataArray(
                    data,
                    dims=["acq_index_0"],
                    attrs={
                        "acq_protocol": "SSBIntegrationComplex",
                        "acq_index_dim_name": "acq_index_0",
                    },
                ),
                "y1": xr.DataArray(
                    data * 2,
                    dims=["acq_index_0"],
                    attrs={
                        "acq_protocol": "SSBIntegrationComplex",
                        "acq_index_dim_name": "acq_index_0",
                    },
                ),
            },
            coords={"x0": ("acq_index_0", coords)},
        )
        dataset.attrs["tuid"] = "20230101-120000-000-abcdef"

        return dataset

    @pytest.fixture
    def dataset_without_tuid(self):
        return xr.Dataset()

    @patch("qblox_scheduler.backends.qblox.data._convert_int_keys_to_strings")
    @patch("qblox_scheduler.backends.qblox.data.AnalysisDataContainer")
    def test_save_with_dataset_tuid(self, mock_analysis_data_container, mock_convert, dataset):
        mock_experiment = MagicMock()
        mock_analysis_data_container.return_value = mock_experiment
        mock_convert.return_value = dataset
        explicit_tuid = "12341212-123412-123-abcdef"
        save_to_experiment(explicit_tuid, dataset)

        expected_tuid = dataset.attrs["tuid"]
        mock_analysis_data_container.assert_called_once()
        args, kwargs = mock_analysis_data_container.call_args
        assert kwargs["tuid"] == expected_tuid
        assert kwargs.get("name", args[1] if len(args) > 1 else "") == ""
        mock_convert.assert_called_once_with(dataset)
        mock_experiment.write_dataset.assert_called_once_with(dataset)
        mock_experiment.save_snapshot.assert_called_once()

    @patch("qblox_scheduler.backends.qblox.data._convert_int_keys_to_strings")
    @patch("qblox_scheduler.backends.qblox.data.AnalysisDataContainer")
    def test_save_with_explicit_tuid(self, mock_analysis_data_container, mock_convert, dataset):
        mock_experiment = MagicMock()
        mock_analysis_data_container.return_value = mock_experiment
        mock_convert.return_value = dataset
        explicit_tuid = "12341212-123412-123-abcdef"

        save_to_experiment(explicit_tuid, dataset)

        mock_analysis_data_container.assert_called_once()
        args, kwargs = mock_analysis_data_container.call_args
        assert kwargs["tuid"] == explicit_tuid
        assert kwargs.get("name", args[1] if len(args) > 1 else "") == ""
        mock_convert.assert_called_once_with(dataset)
        mock_experiment.write_dataset.assert_called_once_with(dataset)
        mock_experiment.save_snapshot.assert_called_once()

    @patch("qblox_scheduler.backends.qblox.data._convert_int_keys_to_strings")
    @patch("qblox_scheduler.backends.qblox.data.AnalysisDataContainer")
    def test_save_without_snapshot(self, mock_analysis_data_container, mock_convert, dataset):
        mock_experiment = MagicMock()
        mock_analysis_data_container.return_value = mock_experiment
        mock_convert.return_value = dataset
        explicit_tuid = "12341212-123412-123-abcdef"

        save_to_experiment(explicit_tuid, dataset, save_snapshot=False)

        expected_tuid = dataset.attrs["tuid"]
        mock_analysis_data_container.assert_called_once()
        args, kwargs = mock_analysis_data_container.call_args
        assert kwargs["tuid"] == expected_tuid
        assert kwargs.get("name", args[1] if len(args) > 1 else "") == ""
        mock_convert.assert_called_once_with(dataset)
        mock_experiment.write_dataset.assert_called_once_with(dataset)
        mock_experiment.save_snapshot.assert_not_called()
