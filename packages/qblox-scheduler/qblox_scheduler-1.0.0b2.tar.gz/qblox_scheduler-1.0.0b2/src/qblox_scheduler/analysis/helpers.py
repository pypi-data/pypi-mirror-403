# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Helper functions for analysis."""

from collections.abc import Hashable, Iterable
from typing import overload

import xarray


@overload
def acq_coords_to_dims(
    data: xarray.Dataset,
    coords: list[Hashable],
    acq_channels: Iterable[Hashable] | None = None,
) -> xarray.Dataset: ...
@overload
def acq_coords_to_dims(
    data: xarray.DataArray,
    coords: list[Hashable],
    acq_channels: Iterable[Hashable] | None = None,
) -> xarray.DataArray: ...
def acq_coords_to_dims(
    data: xarray.Dataset | xarray.DataArray,
    coords: list[Hashable],
    acq_channels: Iterable[Hashable] | None = None,
):
    """
    Reshapes the acquisitions dataset or dataarray
    so that the given coords become dimensions. It can also reshape
    from a 1 dimensional data to a multi-dimensional data along the given coords.
    If a dataset is given, all acquisition channels are reshaped,
    unless acq_channels are given.

    Parameters
    ----------
    data
        The data to be converted to multi-dimensions.
        Can be a Dataset or a DataArray.
    coords
        The coords keys that needs to be converted to dimensions.
    acq_channels
        In case of a Dataset, these acquisition channels
        need to be converted.

    Returns
    -------
        A DataArray or Dataset that has multi-dimensional
        dimensions along the specified coords.

    Raises
    ------
    ValueError
        If there are no coords or
        if the data does not contain the acquisition index dimension name.

    """
    if len(coords) == 0:
        raise ValueError(
            "Attempting to convert acquisition data to multidimensional, 'coords' cannot be empty."
        )

    if isinstance(data, xarray.DataArray):
        if (acq_index_dim_name := data.attrs.get("acq_index_dim_name")) is None:
            raise ValueError(
                "Attempting to convert acquisition data to multidimensional, "
                "acq_index dimension not found."
            )
        if len(coords) == 1:
            # 1 dimensional case.
            # Swap the old dimension with the new one.
            data = data.swap_dims({acq_index_dim_name: coords[0]})
            # After swapping, we drop the old dimension.
            return data.drop_vars(acq_index_dim_name)
        else:
            # Multidimensional case.
            # set_index and unstack here.
            return data.set_index({acq_index_dim_name: coords}).unstack(acq_index_dim_name)
    else:

        def convert_conditionally(acq_channel: Hashable) -> xarray.DataArray:
            if (acq_channels is None) or (acq_channel in acq_channels):
                return acq_coords_to_dims(data[acq_channel], coords)
            else:
                return data[acq_channel]

        return xarray.Dataset(
            {acq_channel: convert_conditionally(acq_channel) for acq_channel in data.data_vars},
            attrs=data.attrs,
        )
