# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Contains helper functions to reshape data."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import xarray as xr

import quantify_core
from qblox_scheduler.analysis.data_handling import AnalysisDataContainer
from quantify_core.data.handling import (
    _is_uniformly_spaced_array,
    gen_tuid,
)

if TYPE_CHECKING:
    from quantify_core.data.types import TUID
from quantify_core.measurement.control import MeasurementControl

if TYPE_CHECKING:
    from collections.abc import Sequence

    from xarray import Dataset


def save_to_experiment(
    tuid: str,
    dataset: Dataset | None,
    save_snapshot: bool = True,
    save_dataset: bool = True,
) -> None:
    """
    Save a dataset or a snapshot to an experiment folder.

    Examples
    --------
    .. code-block:: python

        dataset = instrument_coordinator.run()
        save_to_experiment(dataset)

    Parameters
    ----------
    dataset
        The dataset to save
    save_snapshot
        Whether to save a snapshot of the experiment
    tuid
        The time-based unique identifier (TUID) of the form YYYYmmDD-HHMMSS-sss-****** for the
        dataset. Used also for the directory creation where the snapshot is saved
    save_dataset
        Whether to save the dataset of the experiment

    """
    name = dataset.attrs.get("name", "") if dataset is not None else ""
    experiment_data = AnalysisDataContainer(tuid=tuid, name=name)

    if save_snapshot:
        experiment_data.save_snapshot()

    if save_dataset and dataset is not None:
        dataset.attrs["tuid"] = tuid
        dataset = _convert_int_keys_to_strings(dataset)
        experiment_data.write_dataset(dataset)


def _convert_int_keys_to_strings(dataset: Dataset) -> Dataset:
    """
    Convert all integer keys in an xarray Dataset to string keys.

    Parameters
    ----------
    dataset
        The dataset to convert

    Returns
    -------
        The converted dataset

    """
    # Check data variables
    data_vars_to_rename = {}
    for var_key in list(dataset.data_vars):
        if isinstance(var_key, int):
            data_vars_to_rename[var_key] = str(var_key)

    coords_to_rename = {}
    for coord_key in list(dataset.coords):
        if isinstance(coord_key, int):
            coords_to_rename[coord_key] = str(coord_key)

    if data_vars_to_rename:
        dataset = dataset.rename(data_vars_to_rename)

    if coords_to_rename:
        dataset = dataset.rename(coords_to_rename)

    return dataset


# TODO: remove this function before official release.
# tracked by https://qblox.atlassian.net/browse/QTFY-860
def reshape_for_analysis(
    gettable_dataset: Dataset,
    x_label: str | list[str] = "",
    x_unit: str | list[str] = "a.u.",
    x_values: Sequence[int | float | complex | np.number] | None = None,
    name: str = "processed_measurement",
    batched: bool = True,
    real_imag: bool = True,
    tuid: TUID | str | None = None,
) -> Dataset:
    """
    Process a dataset returned by a ``gettable.get()`` or
    ``instrument_coordinator.run()`` into a complete xarray Dataset similar to what
    would be returned by ``MeasurementControl.run()``. The dataset is
    compatible with the analysis classes in ``qblox_scheduler.analysis``.

    Parameters
    ----------
    gettable_dataset
        A "raw" dataset returned by ``gettable.get()`` or ``instrument_coordinator.run()``
    x_label
        Label for the x-axis
    x_unit
        Unit for the x-axis
    x_values
        Values for the x-axis
    name
        Name for the dataset
    batched
        Whether the data is batched (True) or iterative (False)
    real_imag
        If True, returns I/Q values. If False, returns magnitude/phase (degrees)
    tuid
        The TUID for the dataset. If ``None``, a new TUID will be generated.


    Examples
    --------
    .. code-block:: python

        dataset = instrument_coordinator.run()
        dataset = reshape_for_analysis(dataset, settable)
        T1Analysis(dataset).run()

    Returns
    -------
        A dataset formatted like a MeasurementControl.run() result

    """
    processed_data = MeasurementControl._process_acquired_data(
        acquired_data=gettable_dataset, batched=batched, real_imag=real_imag
    )

    data_length = len(processed_data[0]) if processed_data else 1

    settable_name = x_label
    settable_long_name = x_label
    settable_unit = x_unit
    is_settable_batched = batched

    coordinate_values = np.array(x_values) if x_values is not None else np.arange(data_length)

    data_vars = {}

    for i, data_array in enumerate(processed_data):
        if real_imag:
            if i % 2 == 0:
                y_name = f"I{i // 2}" if i > 0 else "I"
                y_long_name = f"Real part {i // 2}" if i > 0 else "Real part"
                y_units = "V"
            else:
                y_name = f"Q{i // 2}" if i > 1 else "Q"
                y_long_name = f"Imaginary part {i // 2}" if i > 1 else "Imaginary part"
                y_units = "V"
        elif i % 2 == 0:
            y_name = f"Magnitude{i // 2}" if i > 0 else "Magnitude"
            y_long_name = f"Magnitude {i // 2}" if i > 0 else "Magnitude"
            y_units = "V"
        else:
            y_name = f"Phase{i // 2}" if i > 1 else "Phase"
            y_long_name = f"Phase {i // 2}" if i > 1 else "Phase"
            y_units = "deg"

        attrs = {
            "units": y_units,
            "name": y_name,
            "long_name": y_long_name,
            "batched": batched,
        }

        if batched:
            attrs["batch_size"] = len(data_array)

        data_vars[f"y{i}"] = xr.DataArray(data=data_array, dims=["dim_0"], attrs=attrs)

    x0_attrs = {
        "name": settable_name,
        "long_name": settable_long_name,
        "full_name": settable_name,
        "units": settable_unit,
        "batched": is_settable_batched,
        "is_main_coord": True,
        "uniformly_spaced": _is_uniformly_spaced_array(coordinate_values),
    }

    if is_settable_batched:
        x0_attrs["batch_size"] = len(coordinate_values)  # pyright: ignore

    dataset = xr.Dataset(
        data_vars=data_vars,
        coords={"x0": xr.DataArray(data=coordinate_values, dims=["dim_0"], attrs=x0_attrs)},
    )

    dataset.attrs["tuid"] = tuid or gen_tuid()
    dataset.attrs["name"] = name
    dataset.attrs["grid_2d"] = False
    dataset.attrs["grid_2d_uniformly_spaced"] = False
    dataset.attrs["1d_2_settables_uniformly_spaced"] = False
    dataset.attrs["xlen"] = data_length
    dataset.attrs["ylen"] = 1
    dataset.attrs["quantify_version"] = quantify_core._version.__version__

    return dataset
