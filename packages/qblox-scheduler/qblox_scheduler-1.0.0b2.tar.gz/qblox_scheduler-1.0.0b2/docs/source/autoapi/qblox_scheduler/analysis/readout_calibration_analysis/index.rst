readout_calibration_analysis
============================

.. py:module:: qblox_scheduler.analysis.readout_calibration_analysis 

.. autoapi-nested-parse::

   Module containing an analysis class for two-state readout calibration.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.readout_calibration_analysis.ReadoutCalibrationAnalysis




.. py:class:: ReadoutCalibrationAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`qblox_scheduler.analysis.base_analysis.BaseAnalysis`


   Find threshold and angle which discriminates qubit state.


   .. admonition:: Example

       .. jupyter-execute::

           import os
           import warnings

           with warnings.catch_warnings():
               warnings.simplefilter("ignore")
               from qblox_scheduler.analysis.data_handling import OutputDirectoryManager as mng
           from qblox_scheduler.analysis.readout_calibration_analysis import (
               ReadoutCalibrationAnalysis,
           )

           # load example data
           test_data_dir = "../tests/test_data"
           mng.set_datadir(test_data_dir)
           ReadoutCalibrationAnalysis(tuid="20230509-152441-841-faef49").run().display_figs_mpl()



   .. py:method:: process_data() -> None

      Process the data so that the analysis can make assumptions on the format.



   .. py:method:: run_fitting() -> None

      Fit a state discriminator to the readout calibration data.



   .. py:method:: _get_points() -> tuple


   .. py:method:: analyze_fit_results() -> None

      Check the fit success and populate :code:`.quantities_of_interest`.



   .. py:method:: create_figures() -> None

      Generate figures of interest.

      matplotlib figures and axes objects are added to
      the ``.figs_mpl`` and ``.axs_mpl`` dictionaries, respectively.



