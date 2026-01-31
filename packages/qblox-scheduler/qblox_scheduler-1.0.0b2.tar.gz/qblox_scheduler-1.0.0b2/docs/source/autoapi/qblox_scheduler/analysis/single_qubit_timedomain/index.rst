single_qubit_timedomain
=======================

.. py:module:: qblox_scheduler.analysis.single_qubit_timedomain 

.. autoapi-nested-parse::

   Module containing analyses for common single qubit timedomain experiments.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.single_qubit_timedomain.SingleQubitTimedomainAnalysis
   qblox_scheduler.analysis.single_qubit_timedomain._DecayFigMixin
   qblox_scheduler.analysis.single_qubit_timedomain.T1Analysis
   qblox_scheduler.analysis.single_qubit_timedomain.EchoAnalysis
   qblox_scheduler.analysis.single_qubit_timedomain.RamseyAnalysis
   qblox_scheduler.analysis.single_qubit_timedomain.AllXYAnalysis
   qblox_scheduler.analysis.single_qubit_timedomain.RabiAnalysis




.. py:class:: SingleQubitTimedomainAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`qblox_scheduler.analysis.base_analysis.BaseAnalysis`


   Base Analysis class for single-qubit timedomain experiments.


   .. py:method:: run(calibration_points: Union[bool, Literal['auto']] = 'auto')

      :param calibration_points: Indicates if the data analyzed includes calibration points. If set to
                                 :code:`True`, will interpret the last two data points in the dataset as
                                 :math:`|0\rangle` and :math:`|1\rangle` respectively. If ``"auto"``, will
                                 use :func:`~.has_calibration_points` to determine if the data contains
                                 calibration points.

      :returns: :class:`~.SingleQubitTimedomainAnalysis`:
                    The instance of this analysis.




   .. py:method:: process_data()

      Processes the data so that the analysis can make assumptions on the format.

      Populates self.dataset_processed.S21 with the complex (I,Q) valued transmission,
      and if calibration points are present for the 0 and 1 state, populates
      self.dataset_processed.pop_exc with the excited state population.



   .. py:method:: _rotate_to_calibrated_axis(ref_idx_0: int = -2, ref_idx_1: int = -1)


   .. py:method:: _choose_data_for_fit()


.. py:class:: _DecayFigMixin

   A mixin for common analysis logic.


   .. py:method:: _create_decay_figure(fig_id: str)

      Creates a figure ready for plotting a fit.



.. py:class:: T1Analysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`SingleQubitTimedomainAnalysis`, :py:obj:`_DecayFigMixin`


   Analysis class for a qubit T1 experiment,
   which fits an exponential decay and extracts the T1 time.


   .. py:method:: run_fitting()

      Fit the data to :class:`~qblox_scheduler.analysis.fitting_models.ExpDecayModel`.



   .. py:method:: analyze_fit_results()

      Checks fit success and populates :code:`.quantities_of_interest`.



   .. py:method:: create_figures()

      Create a figure showing the exponential decay and fit.



.. py:class:: EchoAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`SingleQubitTimedomainAnalysis`, :py:obj:`_DecayFigMixin`


   Analysis class for a qubit spin-echo experiment,
   which fits an exponential decay and extracts the T2_echo time.


   .. py:method:: run_fitting()

      Fit the data to :class:`~qblox_scheduler.analysis.fitting_models.ExpDecayModel`.



   .. py:method:: analyze_fit_results()

      Checks fit success and populates :code:`.quantities_of_interest`.



   .. py:method:: create_figures()

      Create a figure showing the exponential decay and fit.



.. py:class:: RamseyAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`SingleQubitTimedomainAnalysis`, :py:obj:`_DecayFigMixin`


   Fits a decaying cosine curve to Ramsey data (possibly with artificial detuning)
   and finds the true detuning, qubit frequency and T2* time.


   .. py:method:: run(artificial_detuning: float = 0, qubit_frequency: float = None, calibration_points: Union[bool, Literal['auto']] = 'auto')

      :param artificial_detuning: The detuning in Hz that will be emulated by adding an extra phase in
                                  software.
      :param qubit_frequency: The initial recorded value of the qubit frequency (before
                              accurate fitting is done) in Hz.
      :param calibration_points: Indicates if the data analyzed includes calibration points. If set to
                                 :code:`True`, will interpret the last two data points in the dataset as
                                 :math:`|0\rangle` and :math:`|1\rangle` respectively. If ``"auto"``, will
                                 use :func:`~.has_calibration_points` to determine if the data contains
                                 calibration points.

      :returns: :class:`~.RamseyAnalysis`:
                    The instance of this analysis.




   .. py:method:: run_fitting()

      Fits a :class:`~qblox_scheduler.analysis.fitting_models.DecayOscillationModel`
      to the data.



   .. py:method:: analyze_fit_results()

      Extract the real detuning and qubit frequency based on the artificial detuning
      and fitted detuning.



   .. py:method:: create_figures()

      Plot Ramsey decay figure.



.. py:class:: AllXYAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`SingleQubitTimedomainAnalysis`


   Normalizes the data from an AllXY experiment and plots against an ideal curve.

   See section 2.3.2 of :cite:t:`reed_entanglement_2013` for an explanation of
   the AllXY experiment and it's applications in diagnosing errors in single-qubit
   control pulses.


   .. py:method:: run()

      Executes the analysis using specific datapoints as calibration points.

      :returns: :class:`~.AllXYAnalysis`:
                    The instance of this analysis.




   .. py:method:: _rotate_to_calibrated_axis()


   .. py:method:: process_data()

      Processes the data so that the analysis can make assumptions on the format.

      Populates self.dataset_processed.S21 with the complex (I,Q) valued transmission,
      and if calibration points are present for the 0 and 1 state, populates
      self.dataset_processed.pop_exc with the excited state population.



   .. py:method:: create_figures()

      To be implemented by subclasses.

      Should generate figures of interest. matplolib figures and axes objects should
      be added to the :code:`.figs_mpl` and :code:`axs_mpl` dictionaries.,
      respectively.



.. py:class:: RabiAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`SingleQubitTimedomainAnalysis`


   Fits a cosine curve to Rabi oscillation data and finds the qubit drive
   amplitude required to implement a pi-pulse.

   The analysis will automatically rotate the data so that the data lies along the
   axis with the best SNR.


   .. py:method:: run(calibration_points: bool = True)

      :param calibration_points: Specifies if the data should be rotated so that it lies along the axis with
                                 the best SNR.

      :returns: :class:`~.RabiAnalysis`:
                    The instance of this analysis.




   .. py:method:: _rotate_to_calibrated_axis()

      If calibration points are True, automatically determine the point farthest
      from the 0 point to use as a reference to rotate the data.

      This will ensure the data lies along the axis with the best SNR.



   .. py:method:: _choose_data_for_fit()


   .. py:method:: run_fitting()

      Fits a :class:`~qblox_scheduler.analysis.fitting_models.RabiModel` to the data.



   .. py:method:: analyze_fit_results()

      Checks fit success and populates :code:`.quantities_of_interest`.



   .. py:method:: create_figures()

      Creates Rabi oscillation figure



