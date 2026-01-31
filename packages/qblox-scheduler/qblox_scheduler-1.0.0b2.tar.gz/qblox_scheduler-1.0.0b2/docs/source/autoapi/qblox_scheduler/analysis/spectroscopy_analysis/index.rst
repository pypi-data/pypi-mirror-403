spectroscopy_analysis
=====================

.. py:module:: qblox_scheduler.analysis.spectroscopy_analysis 


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.spectroscopy_analysis.QubitFluxSpectroscopyAnalysis
   qblox_scheduler.analysis.spectroscopy_analysis.QubitSpectroscopyAnalysis
   qblox_scheduler.analysis.spectroscopy_analysis.ResonatorSpectroscopyAnalysis
   qblox_scheduler.analysis.spectroscopy_analysis.ResonatorFluxSpectroscopyAnalysis




.. py:class:: QubitFluxSpectroscopyAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`qblox_scheduler.analysis.base_analysis.BaseAnalysis`


   Analysis class for qubit flux spectroscopy.

   .. admonition:: Example

       .. jupyter-execute::

           import warnings

           from qblox_scheduler.analysis.spectroscopy_analysis import QubitFluxSpectroscopyAnalysis
           with warnings.catch_warnings():
               warnings.simplefilter("ignore")
               from qblox_scheduler.analysis.data_handling import OutputDirectoryManager as mng

           # load example data
           test_data_dir = "../tests/test_data"
           mng.set_datadir(test_data_dir)

           # run analysis and plot results
           analysis = (
               QubitFluxSpectroscopyAnalysis(tuid="20230309-235354-353-9c94c5")
               .run()
               .display_figs_mpl()
           )



   .. py:method:: process_data() -> None

      Process the data so that the analysis can make assumptions on the format.



   .. py:method:: run_fitting() -> None

      Fits a QuadraticModel model to the frequency response vs. flux offset.



   .. py:method:: analyze_fit_results() -> None

      Check the fit success and populate :code:`.quantities_of_interest`.



   .. py:method:: create_figures() -> None

      Generate plot of magnitude and phase images, with superposed model fit.



.. py:class:: QubitSpectroscopyAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`qblox_scheduler.analysis.base_analysis.BaseAnalysis`


   Analysis for a qubit spectroscopy experiment.

   Fits a Lorentzian function to qubit spectroscopy
   data and finds the 0-1 transition frequency.


   .. py:method:: process_data() -> None

      Populate the :code:`.dataset_processed`.



   .. py:method:: run_fitting() -> None

      Fit a Lorentzian function to the data.



   .. py:method:: analyze_fit_results() -> None

      Check fit success and populates :code:`.quantities_of_interest`.



   .. py:method:: create_figures() -> None

      Create qubit spectroscopy figure.



.. py:class:: ResonatorSpectroscopyAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`qblox_scheduler.analysis.base_analysis.BaseAnalysis`


   Analysis for a spectroscopy experiment of a hanger resonator.


   .. py:method:: process_data()

      Verifies that the data is measured as magnitude and phase and casts it to
      a dataset of complex valued transmission :math:`S_{21}`.



   .. py:method:: run_fitting()

      Fits a :class:`~qblox_scheduler.analysis.fitting_models.ResonatorModel` to the data.



   .. py:method:: analyze_fit_results()

      Checks fit success and populates :code:`.quantities_of_interest`.



   .. py:method:: create_figures()

      Plots the measured and fitted transmission :math:`S_{21}` as the I and Q
      component vs frequency, the magnitude and phase vs frequency,
      and on the complex I,Q plane.



   .. py:method:: _create_fig_s21_real_imag()


   .. py:method:: _create_fig_s21_magn_phase()


   .. py:method:: _create_fig_s21_complex()


.. py:class:: ResonatorFluxSpectroscopyAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`qblox_scheduler.analysis.base_analysis.BaseAnalysis`


   Analysis class for resonator flux spectroscopy.

   .. admonition:: Example

       .. jupyter-execute::

           import warnings

           from qblox_scheduler.analysis.spectroscopy_analysis import (
               ResonatorFluxSpectroscopyAnalysis
           )
           with warnings.catch_warnings():
               warnings.simplefilter("ignore")
               from qblox_scheduler.analysis.data_handling import OutputDirectoryManager as mng

           # load example data
           test_data_dir = "../tests/test_data"
           mng.set_datadir(test_data_dir)

           # run analysis and plot results
           analysis = (
               ResonatorFluxSpectroscopyAnalysis(tuid="20230308-235659-059-cf471e")
               .run()
               .display_figs_mpl()
           )



   .. py:method:: process_data() -> None

      Process the data so that the analysis can make assumptions on the format.



   .. py:method:: run_fitting() -> None

      Fits a sinusoidal model to the frequency response vs. flux offset.



   .. py:method:: analyze_fit_results() -> None

      Check the fit success and populate :code:`.quantities_of_interest`.



   .. py:method:: create_figures() -> None

      Generate plot of magnitude and phase images, with superposed model fit.



