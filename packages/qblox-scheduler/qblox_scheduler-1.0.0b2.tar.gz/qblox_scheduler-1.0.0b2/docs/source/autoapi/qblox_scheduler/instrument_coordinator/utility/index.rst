utility
=======

.. py:module:: qblox_scheduler.instrument_coordinator.utility 

.. autoapi-nested-parse::

   Utility functions for the instrument coordinator and components.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.instrument_coordinator.utility.search_settable_param
   qblox_scheduler.instrument_coordinator.utility.parameter_value_same_as_cache
   qblox_scheduler.instrument_coordinator.utility.lazy_set
   qblox_scheduler.instrument_coordinator.utility.check_already_existing_acquisition
   qblox_scheduler.instrument_coordinator.utility.add_acquisition_coords_binned
   qblox_scheduler.instrument_coordinator.utility.add_acquisition_coords_nonbinned
   qblox_scheduler.instrument_coordinator.utility.merge_acquisition_sets



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.instrument_coordinator.utility.logger


.. py:data:: logger

.. py:function:: search_settable_param(instrument: qcodes.instrument.instrument_base.InstrumentBase, nested_parameter_name: str) -> qcodes.parameters.parameter.Parameter

   Searches for a settable parameter in nested instrument hierarchies.

   For example `instrument.submodule_1.channel_1.parameter.`

   :param instrument: The root QCoDeS instrument where the parameter resides.
   :param nested_parameter_name: Hierarchical nested parameter name.

   :returns: Parameter:



.. py:function:: parameter_value_same_as_cache(instrument: qcodes.instrument.instrument_base.InstrumentBase, parameter_name: str, val: object) -> bool

   Returns whether the value of a QCoDeS parameter is the same as the value in cache.

   :param instrument: The QCoDeS instrument to set the parameter on.
   :param parameter_name: Name of the parameter to set.
   :param val: Value to set it to.

   :returns: bool



.. py:function:: lazy_set(instrument: qcodes.instrument.instrument_base.InstrumentBase, parameter_name: str, val: object) -> None

   Set the value of a QCoDeS parameter only if it is different from the value in cache.

   :param instrument: The QCoDeS instrument to set the parameter on.
   :param parameter_name: Name of the parameter to set.
   :param val: Value to set it to.


.. py:function:: check_already_existing_acquisition(new_dataset: xarray.Dataset, current_dataset: xarray.Dataset) -> None

   Verifies non-overlapping data in new_dataset and current_dataset.

   If there is, it will raise an error.

   :param new_dataset: New dataset.
   :param current_dataset: Current dataset.


.. py:function:: add_acquisition_coords_binned(data_array: xarray.DataArray, coords: list[dict], acq_index_dim_name: collections.abc.Hashable) -> None

   Modifies the argument data_array,
   it adds the coords to it.

   This function only applies to binned acquisitions.

   Coordinates in the acquisition channels data is a list of dictionary,
   and each dictionary is a coordinate. In the return data however,
   it should be a dict, for each coords key it should store a list of the values.

   xarray requires the coordinates to specify on which xarray dimension they are applied to.
   That's why the acq_index_dim_name is used here. Note: dimension and coords are different.


.. py:function:: add_acquisition_coords_nonbinned(data_array: xarray.DataArray, coords: dict, acq_index_dim_name: collections.abc.Hashable) -> None

   Modifies the argument data_array,
   it adds the coords to it.

   This function only applies to nonbinned acquisitions.

   Coordinates in the acquisition channels data is a dictionary,
   and each dictionary is a coordinate. In the return data however,
   it should be a dict, for each coords key it should store a list of the values.

   xarray requires the coordinates to specify on which xarray dimension they are applied to.
   That's why the acq_index_dim_name is used here. Note: dimension and coords are different.


.. py:function:: merge_acquisition_sets(*data_sets: xarray.Dataset) -> xarray.Dataset

   Merge any amount of acquisition datasets into one,
   adjusting coordinates if necessary.


