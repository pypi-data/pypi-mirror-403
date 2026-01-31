import numpy as np
import pytest
import xarray as xr

from qblox_scheduler.analysis.data import (
    reshape_for_analysis,
)


class TestReshapeForAnalysis:
    @pytest.fixture
    def gettable_dataset(self):
        data = np.array([0.1, 0.2, 0.3])
        coords = np.array([1e-6, 2e-6, 3e-6])

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
        return dataset

    def test_reshape_real_imag_batched(self, gettable_dataset):
        result = reshape_for_analysis(
            gettable_dataset, x_unit="s", x_label="test_param", batched=True, real_imag=True
        )

        assert "y0" in result.data_vars
        assert "y1" in result.data_vars
        assert "dim_0" in result.dims
        assert "x0" in result.coords

        assert result.y0.attrs["name"] == "I"
        assert result.y0.attrs["long_name"] == "Real part"
        assert result.y0.attrs["units"] == "V"
        assert result.y0.attrs["batched"] is True

        assert result.y1.attrs["name"] == "Q"
        assert result.y1.attrs["long_name"] == "Imaginary part"
        assert result.y1.attrs["units"] == "V"

        assert result.x0.attrs["name"] == "test_param"
        assert result.x0.attrs["units"] == "s"
        assert result.x0.attrs["batched"] is True
        assert result.x0.attrs["batch_size"] == 3

        assert "tuid" in result.attrs
        assert result.attrs["grid_2d"] is False
        assert result.attrs["xlen"] == 3

    def test_reshape_mag_phase_non_batched(self):
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

        result = reshape_for_analysis(dataset, x_values=[1e-6], batched=False, real_imag=False)

        assert result.y0.attrs["name"] == "Magnitude"
        assert result.y0.attrs["units"] == "V"
        assert result.y0.attrs["batched"] is False

        assert result.y1.attrs["name"] == "Phase"
        assert result.y1.attrs["units"] == "deg"
        assert result.y1.attrs["batched"] is False

    def test_custom_tuid(self, gettable_dataset):
        custom_tuid = "20230101-120000-000-abcdef"
        result = reshape_for_analysis(gettable_dataset, tuid=custom_tuid)

        assert result.attrs["tuid"] == custom_tuid
