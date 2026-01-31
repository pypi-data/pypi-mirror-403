interpolation_analysis
======================

.. py:module:: qblox_scheduler.analysis.interpolation_analysis 


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.interpolation_analysis.InterpolationAnalysis2D




.. py:class:: InterpolationAnalysis2D(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`qblox_scheduler.analysis.base_analysis.BaseAnalysis`


   An analysis class which generates a 2D interpolating plot for each yi variable in
   the dataset.


   .. py:method:: create_figures()

      Create a 2D interpolating figure for each yi.



