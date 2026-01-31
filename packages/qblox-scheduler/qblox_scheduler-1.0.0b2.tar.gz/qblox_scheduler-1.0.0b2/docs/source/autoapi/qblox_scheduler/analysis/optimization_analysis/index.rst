optimization_analysis
=====================

.. py:module:: qblox_scheduler.analysis.optimization_analysis 


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.optimization_analysis.OptimizationAnalysis



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.optimization_analysis.iteration_plots



.. py:class:: OptimizationAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`qblox_scheduler.analysis.base_analysis.BaseAnalysis`


   An analysis class which extracts the optimal quantities from an N-dimensional
   interpolating experiment.


   .. py:method:: run(minimize: bool = True)

      :param minimize: Boolean which determines whether to report the minimum or the maximum.
                       True for minimize.
                       False for maximize.

      :returns: :class:`~qblox_scheduler.analysis.optimization_analysis.OptimizationAnalysis`:
                    The instance of this analysis.




   .. py:method:: process_data()

      Finds the optimal (minimum or maximum) for y0 and saves the xi and y0
      values in the :code:`quantities_of_interest`.



   .. py:method:: create_figures()

      Plot each of the x variables against each of the y variables.



.. py:function:: iteration_plots(dataset, quantities_of_interest)

   For every x and y variable, plot a graph of that variable vs the iteration index.


