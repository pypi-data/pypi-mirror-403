helpers
=======

.. py:module:: qblox_scheduler.analysis.helpers 

.. autoapi-nested-parse::

   Helper functions for analysis.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.helpers.acq_coords_to_dims



.. py:function:: acq_coords_to_dims(data: xarray.Dataset, coords: list[collections.abc.Hashable], acq_channels: collections.abc.Iterable[collections.abc.Hashable] | None = None) -> xarray.Dataset
                 acq_coords_to_dims(data: xarray.DataArray, coords: list[collections.abc.Hashable], acq_channels: collections.abc.Iterable[collections.abc.Hashable] | None = None) -> xarray.DataArray

   Reshapes the acquisitions dataset or dataarray
   so that the given coords become dimensions. It can also reshape
   from a 1 dimensional data to a multi-dimensional data along the given coords.
   If a dataset is given, all acquisition channels are reshaped,
   unless acq_channels are given.

   :param data: The data to be converted to multi-dimensions.
                Can be a Dataset or a DataArray.
   :param coords: The coords keys that needs to be converted to dimensions.
   :param acq_channels: In case of a Dataset, these acquisition channels
                        need to be converted.

   :returns: A DataArray or Dataset that has multi-dimensional
             dimensions along the specified coords.

   :raises ValueError: If there are no coords or
       if the data does not contain the acquisition index dimension name.


