conditional_oscillation_analysis
================================

.. py:module:: qblox_scheduler.analysis.conditional_oscillation_analysis 

.. autoapi-nested-parse::

   Module containing an analysis class for the conditional oscillation experiment.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.conditional_oscillation_analysis.ConditionalOscillationAnalysis



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.conditional_oscillation_analysis._add_center
   qblox_scheduler.analysis.conditional_oscillation_analysis._center_and_fit_sinus



.. py:function:: _add_center(param_name: str, data: numpy.typing.NDArray, params: lmfit.parameter.Parameters) -> None

.. py:function:: _center_and_fit_sinus(y: numpy.typing.NDArray, x: numpy.typing.NDArray) -> lmfit.model.ModelResult

.. py:class:: ConditionalOscillationAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`qblox_scheduler.analysis.base_analysis.BaseAnalysis`


   Analysis class for the conditional oscillation experiment.

   For a reference to the conditional oscillation experiment, please
   see section D in the supplemental material of
   this paper: https://arxiv.org/abs/1903.02492

   .. admonition:: Example

       .. jupyter-execute::

           import warnings

           from qblox_scheduler.analysis.conditional_oscillation_analysis import (
               ConditionalOscillationAnalysis
           )
           with warnings.catch_warnings():
               warnings.simplefilter("ignore")
               from qblox_scheduler.analysis.data_handling import OutputDirectoryManager as mng

           # load example data
           test_data_dir = "../tests/test_data"
           mng.set_datadir(test_data_dir)

           # run analysis and plot results
           analysis = (
               ConditionalOscillationAnalysis(tuid="20230509-165523-132-dcfea7")
               .run()
               .display_figs_mpl()
           )



   .. py:method:: process_data() -> None

      Process the data so that the analysis can make assumptions on the format.



   .. py:method:: run_fitting() -> None

      Fit two sinusoidal model to the off/on experiments.



   .. py:method:: analyze_fit_results() -> None

      Check fit success and populates :code:`.quantities_of_interest`.



   .. py:method:: create_figures() -> None

      Generate figures of interest.

      matplolib figures and axes objects are added to
      the .figs_mpl and .axs_mpl dictionaries., respectively.



