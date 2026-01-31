data
====

.. py:module:: qblox_scheduler.analysis.data 

.. autoapi-nested-parse::

   Contains helper functions to reshape data.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.data.reshape_for_analysis



.. py:function:: reshape_for_analysis(gettable_dataset: xarray.Dataset, x_label: str | list[str] = '', x_unit: str | list[str] = 'a.u.', x_values: collections.abc.Sequence[int | float | complex | numpy.number] | None = None, name: str = 'processed_measurement', batched: bool = True, real_imag: bool = True, tuid: quantify_core.data.types.TUID | str | None = None) -> xarray.Dataset

   Process a dataset returned by a ``gettable.get()`` or
   ``instrument_coordinator.run()`` into a complete xarray Dataset similar to what
   would be returned by ``MeasurementControl.run()``. The dataset is
   compatible with the analysis classes in ``qblox_scheduler.analysis``.

   :param gettable_dataset: A "raw" dataset returned by ``gettable.get()`` or ``instrument_coordinator.run()``
   :param x_label: Label for the x-axis
   :param x_unit: Unit for the x-axis
   :param x_values: Values for the x-axis
   :param name: Name for the dataset
   :param batched: Whether the data is batched (True) or iterative (False)
   :param real_imag: If True, returns I/Q values. If False, returns magnitude/phase (degrees)
   :param tuid: The TUID for the dataset. If ``None``, a new TUID will be generated.

   .. rubric:: Examples

   .. code-block:: python

       dataset = instrument_coordinator.run()
       dataset = reshape_for_analysis(dataset, settable)
       T1Analysis(dataset).run()

   :returns: A dataset formatted like a MeasurementControl.run() result



