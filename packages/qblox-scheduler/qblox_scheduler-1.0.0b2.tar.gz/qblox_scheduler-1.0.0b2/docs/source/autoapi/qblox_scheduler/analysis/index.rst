analysis
========

.. py:module:: qblox_scheduler.analysis 

.. autoapi-nested-parse::

   Module containing analysis functionalities.



Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   base_analysis/index.rst
   calibration/index.rst
   conditional_oscillation_analysis/index.rst
   cosine_analysis/index.rst
   data/index.rst
   data_handling/index.rst
   fitting_models/index.rst
   helpers/index.rst
   interpolation_analysis/index.rst
   optimization_analysis/index.rst
   readout_calibration_analysis/index.rst
   single_qubit_timedomain/index.rst
   spectroscopy_analysis/index.rst
   time_of_flight_analysis/index.rst
   types/index.rst


Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.Basic2DAnalysis
   qblox_scheduler.analysis.BasicAnalysis
   qblox_scheduler.analysis.CosineAnalysis
   qblox_scheduler.analysis.AnalysisDataContainer
   qblox_scheduler.analysis.OutputDirectoryManager
   qblox_scheduler.analysis.InterpolationAnalysis2D
   qblox_scheduler.analysis.OptimizationAnalysis
   qblox_scheduler.analysis.AllXYAnalysis
   qblox_scheduler.analysis.EchoAnalysis
   qblox_scheduler.analysis.RabiAnalysis
   qblox_scheduler.analysis.RamseyAnalysis
   qblox_scheduler.analysis.T1Analysis
   qblox_scheduler.analysis.ResonatorSpectroscopyAnalysis



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.acq_coords_to_dims



.. py:class:: Basic2DAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`BaseAnalysis`


   A basic analysis that extracts the data from the latest file matching the label
   and plots and stores the data in the experiment container.


   .. py:method:: create_figures()

      To be implemented by subclasses.

      Should generate figures of interest. matplolib figures and axes objects should
      be added to the :code:`.figs_mpl` and :code:`axs_mpl` dictionaries.,
      respectively.



.. py:class:: BasicAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`BaseAnalysis`


   A basic analysis that extracts the data from the latest file matching the label
   and plots and stores the data in the experiment container.


   .. py:method:: create_figures()

      Creates a line plot x vs y for every data variable yi and coordinate xi in the
      dataset.



.. py:class:: CosineAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`qblox_scheduler.analysis.base_analysis.BaseAnalysis`


   Exemplary analysis subclass that fits a cosine to a dataset.


   .. py:method:: process_data()

      In some cases, you might need to process the data, e.g., reshape, filter etc.,
      before starting the analysis. This is the method where it should be done.

      See :meth:`~qblox_scheduler.analysis.spectroscopy_analysis.ResonatorSpectroscopyAnalysis.process_data`
      for an implementation example.



   .. py:method:: run_fitting()

      Fits a :class:`~qblox_scheduler.analysis.fitting_models.CosineModel` to the data.



   .. py:method:: create_figures()

      Creates a figure with the data and the fit.



   .. py:method:: analyze_fit_results()

      Checks fit success and populates :code:`quantities_of_interest`.



.. py:class:: AnalysisDataContainer(tuid: str, name: str)

   Class which represents all data related to an experiment. This allows the user to
   run experiments and store data. The class serves as an
   initial interface and uses the directory paths set by OutputDirectoryManager.


   .. py:attribute:: DATASET_NAME
      :type:  ClassVar[str]
      :value: 'dataset.hdf5'



   .. py:attribute:: SNAPSHOT_FILENAME
      :type:  ClassVar[str]
      :value: 'snapshot.json'



   .. py:attribute:: _TUID_LENGTH
      :type:  ClassVar[int]
      :value: 26



   .. py:attribute:: tuid


   .. py:attribute:: day_folder


   .. py:attribute:: data_folder


   .. py:property:: experiment_name
      :type: str


      The name of the experiment.


   .. py:method:: load_dataset(tuid: quantify_core.data.types.TUID, name: str = DATASET_NAME) -> xarray.Dataset
      :classmethod:


      Loads a dataset specified by a tuid.

      :param tuid: A :class:`~quantify_core.data.types.TUID` string. It is also possible to specify
                   only the first part of a tuid.
      :param name: Name of the dataset.

      :returns: :
                    The dataset.




   .. py:method:: load_dataset_from_path(path: pathlib.Path | str) -> xarray.Dataset
      :classmethod:


      Loads a :class:`~xarray.Dataset` with a specific engine preference.

      Before returning the dataset :meth:`AdapterH5NetCDF.recover()
      <quantify_core.data.dataset_adapters.AdapterH5NetCDF.recover>` is applied.

      This function tries to load the dataset until success with the following engine
      preference:

      - ``"h5netcdf"``
      - ``"netcdf4"``
      - No engine specified (:func:`~xarray.load_dataset` default)

      :param path: Path to the dataset.

      :returns: :
                    The loaded dataset.




   .. py:method:: write_dataset(dataset: xarray.Dataset) -> None

      Writes the quantify dataset to the directory specified by
      `~.data_folder`.

      :param dataset: The dataset to be written to the directory



   .. py:method:: save_snapshot(snapshot: Optional[dict[str, Any]] = None, compression: Literal['bz2', 'gzip', 'lzma'] | None = None) -> None

      Writes the snapshot to disk as specified by
      `~.data_folder`.

      :param snapshot: The snapshot to be written to the directory
      :param compression: The compression type to use. Can be one of 'gzip', 'bz2', 'lzma'.
                          Defaults to None, which means no compression.



   .. py:method:: get_latest_tuid(contains: str = '') -> quantify_core.data.types.TUID
      :classmethod:


      Returns the most recent tuid.

      .. tip::

          This function is similar to :func:`~get_tuids_containing` but is preferred if
          one is only interested in the most recent
          :class:`~quantify_core.data.types.TUID` for performance reasons.

      :param contains: An optional string contained in the experiment name.

      :returns: :
                    The latest TUID.

      :raises FileNotFoundError: No data found.



   .. py:method:: get_tuids_containing(contains: str = '', t_start: datetime.datetime | str | None = None, t_stop: datetime.datetime | str | None = None, max_results: int = sys.maxsize, reverse: bool = False) -> list[quantify_core.data.types.TUID]
      :classmethod:


      Returns a list of tuids containing a specific label.

      .. tip::

          If one is only interested in the most recent
          :class:`~quantify_core.data.types.TUID`, :func:`~get_latest_tuid` is preferred
          for performance reasons.

      :param contains: A string contained in the experiment name.
      :param t_start: datetime to search from, inclusive. If a string is specified, it will be
                      converted to a datetime object using :obj:`~dateutil.parser.parse`.
                      If no value is specified, will use the year 1 as a reference t_start.
      :param t_stop: datetime to search until, exclusive. If a string is specified, it will be
                     converted to a datetime object using :obj:`~dateutil.parser.parse`.
                     If no value is specified, will use the current time as a reference t_stop.
      :param max_results: Maximum number of results to return. Defaults to unlimited.
      :param reverse: If False, sorts tuids chronologically, if True sorts by most recent.

      :returns: list
                    A list of :class:`~quantify_core.data.types.TUID`: objects.

      :raises FileNotFoundError: No data found.



   .. py:method:: locate_experiment_container(tuid: str) -> pathlib.Path
      :classmethod:


      Returns the experiment container for the given tuid.



.. py:class:: OutputDirectoryManager

   Manages output directory paths for Qblox Scheduler data storage.

   The class maintains a single instance throughout
   the application lifecycle, ensuring consistent directory management.

   .. attribute:: _datadir

      The current data directory path. Private attribute managed through
      setter and getter methods.

      :type: str or Path


   .. py:attribute:: DATADIR
      :type:  ClassVar[pathlib.Path]


   .. py:method:: set_datadir(datadir: pathlib.Path | str | None = None) -> None
      :classmethod:


      Sets the data directory.

      :param datadir: Path of the data directory. If set to ``None``, resets the datadir to the
                      default datadir (``<top_level>/data``).
      :type datadir: pathlib.Path or str or None



   .. py:method:: get_datadir() -> pathlib.Path
      :classmethod:


      Returns the current data directory.

      :returns: :
                    The current data directory.




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


.. py:class:: InterpolationAnalysis2D(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`qblox_scheduler.analysis.base_analysis.BaseAnalysis`


   An analysis class which generates a 2D interpolating plot for each yi variable in
   the dataset.


   .. py:method:: create_figures()

      Create a 2D interpolating figure for each yi.



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


