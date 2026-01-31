base_analysis
=============

.. py:module:: qblox_scheduler.analysis.base_analysis 

.. autoapi-nested-parse::

   Module containing the analysis abstract base class and several basic analyses.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.base_analysis._FiguresMplCache
   qblox_scheduler.analysis.base_analysis.AnalysisSteps
   qblox_scheduler.analysis.base_analysis.AnalysisMeta
   qblox_scheduler.analysis.base_analysis.BaseAnalysis
   qblox_scheduler.analysis.base_analysis.BasicAnalysis
   qblox_scheduler.analysis.base_analysis.Basic1DAnalysis
   qblox_scheduler.analysis.base_analysis.Basic2DAnalysis



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.base_analysis.flatten_lmfit_modelresult
   qblox_scheduler.analysis.base_analysis.lmfit_par_to_ufloat
   qblox_scheduler.analysis.base_analysis.check_lmfit
   qblox_scheduler.analysis.base_analysis.wrap_text
   qblox_scheduler.analysis.base_analysis.analysis_steps_to_str



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.base_analysis.FIGURES_LRU_CACHE_SIZE
   qblox_scheduler.analysis.base_analysis.settings


.. py:data:: FIGURES_LRU_CACHE_SIZE
   :value: 8


.. py:class:: _FiguresMplCache

   .. py:attribute:: figs
      :type:  dict[str, matplotlib.figure.Figure]


   .. py:attribute:: axes
      :type:  dict[str, matplotlib.axes.Axes]


   .. py:attribute:: initialized
      :type:  bool


.. py:data:: settings

   For convenience the analysis framework provides a set of global settings.

   For available settings see :class:`~BaseAnalysis`.
   These can be overwritten for each instance of an analysis.

   .. rubric:: Examples

   >>> from qblox_scheduler.analysis import base_analysis as ba
   ... ba.settings["mpl_dpi"] = 300  # set resolution of matplotlib figures

.. py:class:: AnalysisSteps(*args, **kwds)

   Bases: :py:obj:`enum.Enum`


   An enumerate of the steps executed by the :class:`~BaseAnalysis` (and the default
   for subclasses).

   The involved steps are:

   - ``AnalysisSteps.STEP_1_PROCESS_DATA`` (:meth:`BaseAnalysis.process_data`)
   - ``AnalysisSteps.STEP_2_RUN_FITTING``  (:meth:`BaseAnalysis.run_fitting`)
   - ``AnalysisSteps.STEP_3_ANALYZE_FIT_RESULTS`` (:meth:`BaseAnalysis.analyze_fit_results`)
   - ``AnalysisSteps.STEP_4_CREATE_FIGURES`` (:meth:`BaseAnalysis.create_figures`)
   - ``AnalysisSteps.STEP_5_ADJUST_FIGURES``  (:meth:`BaseAnalysis.adjust_figures`)
   - ``AnalysisSteps.STEP_6_SAVE_FIGURES``  (:meth:`BaseAnalysis.save_figures`)
   - ``AnalysisSteps.STEP_7_SAVE_QUANTITIES_OF_INTEREST`` (:meth:`BaseAnalysis.save_quantities_of_interest`)
   - ``AnalysisSteps.STEP_8_SAVE_PROCESSED_DATASET``  (:meth:`BaseAnalysis.save_processed_dataset`)
   - ``AnalysisSteps.STEP_9_SAVE_FIT_RESULTS`` (:meth:`BaseAnalysis.save_fit_results`)

   A custom analysis flow (e.g. inserting new steps) can be created by implementing
   an object similar to this one and overriding the
   :obj:`~BaseAnalysis.analysis_steps`.


   .. py:attribute:: STEP_1_PROCESS_DATA
      :value: 'process_data'



   .. py:attribute:: STEP_2_RUN_FITTING
      :value: 'run_fitting'



   .. py:attribute:: STEP_3_ANALYZE_FIT_RESULTS
      :value: 'analyze_fit_results'



   .. py:attribute:: STEP_4_CREATE_FIGURES
      :value: 'create_figures'



   .. py:attribute:: STEP_5_ADJUST_FIGURES
      :value: 'adjust_figures'



   .. py:attribute:: STEP_6_SAVE_FIGURES
      :value: 'save_figures'



   .. py:attribute:: STEP_7_SAVE_QUANTITIES_OF_INTEREST
      :value: 'save_quantities_of_interest'



   .. py:attribute:: STEP_8_SAVE_PROCESSED_DATASET
      :value: 'save_processed_dataset'



   .. py:attribute:: STEP_9_SAVE_FIT_RESULTS
      :value: 'save_fit_results'



.. py:class:: AnalysisMeta

   Bases: :py:obj:`abc.ABCMeta`


   Metaclass, whose purpose is to avoid storing large amount of figure in memory.

   By convention, analysis object stores figures in ``self.figs_mpl`` and
   ``self.axs_mpl`` dictionaries. This causes troubles for long-running operations,
   because figures are all in memory and eventually this uses all available memory of
   the PC. In order to avoid it, :meth:`BaseAnalysis.create_figures` and its
   derivatives are patched so that all the figures are put in LRU cache and
   reconstructed upon request to :code:`BaseAnalysis.figs_mpl` or
   :code:`BaseAnalysis.axs_mpl` if they were removed from the cache.

   Provided that analyses subclasses follow convention of figures being created in
   :meth:`BaseAnalysis.create_figures`, this approach should solve the memory issue
   and preserve reverse compatibility with present code.


.. py:class:: BaseAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   A template for analysis classes.


   .. py:attribute:: html_header_template
      :value: '<h1>{name}</h1><p style="font-family: monospace">TUID: {tuid}</p>'



   .. py:method:: _repr_html_()

      An html representation of the analysis class.

      Shows the name of the analysis and TUID as well as the
      (.svg) figures generated by this analysis.



   .. py:attribute:: logger


   .. py:attribute:: label
      :value: ''



   .. py:attribute:: tuid
      :value: None



   .. py:attribute:: settings_overwrite


   .. py:attribute:: dataset
      :value: None



   .. py:attribute:: dataset_processed


   .. py:attribute:: analysis_result


   .. py:attribute:: quantities_of_interest


   .. py:attribute:: fit_results


   .. py:attribute:: plot_figures
      :value: True



   .. py:attribute:: analysis_steps

      Defines the steps of the analysis specified as an :class:`~enum.Enum`.
      Can be overridden in a subclass in order to define a custom analysis flow.
      See :class:`~qblox_scheduler.analysis.base_analysis.AnalysisSteps` for a template.


   .. py:method:: load_fit_result(tuid: quantify_core.data.types.TUID, fit_name: str) -> lmfit.model.ModelResult
      :classmethod:


      Load a saved :code:`lmfit.model.ModelResult` object from file. For analyses
      that use custom fit functions, the :code:`cls.fit_function_definitions` object
      must be defined in the subclass for that analysis.

      :param tuid: The TUID reference of the saved analysis.
      :param fit_name: The name of the fit result to be loaded.

      :returns: :
                    The lmfit model result object.




   .. py:property:: name

      The name of the analysis, used in data saving.


   .. py:method:: _get_analysis_dir(tuid: quantify_core.data.types.TUID, name: str, create_missing: bool = True)
      :staticmethod:


      Generate an analysis dir based on a given tuid and analysis class name.

      :param tuid: TUID of the analysis dir.
      :param name: The name of the analysis class.
      :param create_missing: If True, create the analysis dir if it does not already exist.



   .. py:property:: analysis_dir

      Analysis dir based on the tuid of the analysis class instance.
      Will create a directory if it does not exist.


   .. py:method:: _get_results_dir(analysis_dir: str, create_missing: bool = True)
      :staticmethod:


      Generate an results dir based on a given analysis dir path.

      :param analysis_dir: The path of the analysis directory.
      :param create_missing: If True, create the analysis dir if it does not already exist.



   .. py:method:: _analyses_figures_cache()


   .. py:property:: results_dir

      Analysis directory for this analysis.
      Will create a directory if it does not exist.


   .. py:method:: run() -> typing_extensions.Self

      Execute analysis.

      This function is at the core of all analysis. It calls
      :meth:`~qblox_scheduler.analysis.base_analysis.BaseAnalysis.execute_analysis_steps`
      which executes all the methods defined in the.

      First step of any analysis is always extracting data, that is not configurable.
      Errors in `extract_data()` are considered fatal for analysis.
      Later steps are configurable by overriding
      :attr:`~qblox_scheduler.analysis.base_analysis.BaseAnalysis.analysis_steps`.
      Exceptions in these steps are logged and suppressed and analysis is considered
      partially successful.

      This function is typically called right after instantiating an analysis class.

      .. admonition:: Implementing a custom analysis that requires user input
          :class: dropdown, note

          When implementing your own custom analysis you might need to pass in a few
          configuration arguments. That should be achieved by overriding this
          function as show below.

          .. code-block:: python

              from qblox_scheduler.analysis.base_analysis import BaseAnalysis
              from typing_extensions import Self

              class MyAnalysis(BaseAnalysis):
                  def run(self, optional_argument_one: float = 3.5e9) -> Self:
                      # Save the value to be used in some step of the analysis
                      self.optional_argument_one = optional_argument_one

                      # Execute the analysis steps
                      self.execute_analysis_steps()
                      # Return the analysis object
                      return self

                  # ... other relevant methods ...

      :returns: :
                    The instance of the analysis object so that
                    :meth:`~qblox_scheduler.analysis.base_analysis.BaseAnalysis.run()`
                    returns an analysis object.
                    You can initialize, run and assign it to a variable on a
                    single line:, e.g. :code:`a_obj = MyAnalysis().run()`.




   .. py:method:: execute_analysis_steps()

      Executes the methods corresponding to the analysis steps as defined by the
      :attr:`~qblox_scheduler.analysis.base_analysis.BaseAnalysis.analysis_steps`.

      Intended to be called by `.run` when creating a custom analysis that requires
      passing analysis configuration arguments to
      :meth:`~qblox_scheduler.analysis.base_analysis.BaseAnalysis.run`.



   .. py:method:: get_flow() -> tuple

      Returns a tuple with the ordered methods to be called by run analysis.
      Only return the figures methods if :code:`self.plot_figures` is :code:`True`.



   .. py:method:: extract_data()

      If no `dataset` is provided, populates :code:`.dataset` with data from
      the experiment matching the tuid/label.

      This method should be overwritten if an analysis does not relate to a single
      datafile.



   .. py:method:: process_data()

      To be implemented by subclasses.

      Should process, e.g., reshape, filter etc. the data
      before starting the analysis.



   .. py:method:: run_fitting()

      To be implemented by subclasses.

      Should create fitting model(s) and fit data to the model(s) adding the result
      to the :code:`.fit_results` dictionary.



   .. py:method:: _add_fit_res_to_qoi()


   .. py:method:: analyze_fit_results()

      To be implemented by subclasses.

      Should analyze and process the :code:`.fit_results` and add the quantities of
      interest to the :code:`.quantities_of_interest` dictionary.



   .. py:method:: create_figures()

      To be implemented by subclasses.

      Should generate figures of interest. matplolib figures and axes objects should
      be added to the :code:`.figs_mpl` and :code:`axs_mpl` dictionaries.,
      respectively.



   .. py:method:: adjust_figures()

      Perform global adjustments after creating the figures but
      before saving them.

      By default applies `mpl_exclude_fig_titles` and `mpl_transparent_background`
      from :code:`.settings_overwrite` to any matplotlib figures in
      :code:`.figs_mpl`.

      Can be extended in a subclass for additional adjustments.



   .. py:method:: save_processed_dataset()

      Saves a copy of the processed :code:`.dataset_processed` in the analysis folder
      of the experiment.



   .. py:method:: save_quantities_of_interest()

      Saves the :code:`.quantities_of_interest` as a JSON file in the analysis
      directory.

      The file is written using :func:`json.dump` with the
      :class:`qcodes.utils.NumpyJSONEncoder` custom encoder.



   .. py:method:: save_fit_results()

      Saves the :code:`lmfit.model.model_result` objects for each fit in a
      sub-directory within the analysis directory.



   .. py:method:: save_figures()

      Saves figures to disk. By default saves matplotlib figures.

      Can be overridden or extended to make use of other plotting packages.



   .. py:method:: save_figures_mpl(close_figs: bool = True)

      Saves all the matplotlib figures in the :code:`.figs_mpl` dict.

      :param close_figs: If True, closes matplotlib figures after saving.



   .. py:method:: display_figs_mpl()

      Displays figures in :code:`.figs_mpl` in all frontends.



   .. py:method:: adjust_ylim(ymin: float = None, ymax: float = None, ax_ids: list[str] = None) -> None

      Adjust the ylim of matplotlib figures generated by analysis object.

      :param ymin: The bottom ylim in data coordinates. Passing :code:`None` leaves the
                   limit unchanged.
      :param ymax: The top ylim in data coordinates. Passing None leaves the limit unchanged.
      :param ax_ids: A list of ax_ids specifying what axes to adjust. Passing None results in
                     all axes of an analysis object being adjusted.



   .. py:method:: adjust_xlim(xmin: float = None, xmax: float = None, ax_ids: list[str] = None) -> None

      Adjust the xlim of matplotlib figures generated by analysis object.

      :param xmin: The bottom xlim in data coordinates. Passing :code:`None` leaves the limit
                   unchanged.
      :param xmax: The top xlim in data coordinates. Passing None leaves the limit unchanged.
      :param ax_ids: A list of ax_ids specifying what axes to adjust. Passing None results in
                     all axes of an analysis object being adjusted.



   .. py:method:: adjust_clim(vmin: float, vmax: float, ax_ids: list[str] = None) -> None

      Adjust the clim of matplotlib figures generated by analysis object.

      :param vmin: The bottom vlim in data coordinates. Passing :code:`None` leaves the limit
                   unchanged.
      :param vmax: The top vlim in data coordinates. Passing None leaves the limit unchanged.
      :param ax_ids: A list of ax_ids specifying what axes to adjust. Passing None results in
                     all axes of an analysis object being adjusted.



   .. py:method:: adjust_cmap(cmap: matplotlib.colors.Colormap | str | None, ax_ids: list[str] = None)

      Adjust the cmap of matplotlib figures generated by analysis object.

      :param cmap: The colormap to set for the axis
      :param ax_ids: A list of ax_ids specifying what axes to adjust. Passing None results in
                     all axes of an analysis object being adjusted.



.. py:class:: BasicAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`BaseAnalysis`


   A basic analysis that extracts the data from the latest file matching the label
   and plots and stores the data in the experiment container.


   .. py:method:: create_figures()

      Creates a line plot x vs y for every data variable yi and coordinate xi in the
      dataset.



.. py:class:: Basic1DAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`BasicAnalysis`


   Deprecated. Alias of :class:`~qblox_scheduler.analysis.base_analysis.BasicAnalysis`
   for backwards compatibility.


   .. py:method:: run() -> BaseAnalysis

      Execute analysis.

      This function is at the core of all analysis. It calls
      :meth:`~qblox_scheduler.analysis.base_analysis.BaseAnalysis.execute_analysis_steps`
      which executes all the methods defined in the.

      First step of any analysis is always extracting data, that is not configurable.
      Errors in `extract_data()` are considered fatal for analysis.
      Later steps are configurable by overriding
      :attr:`~qblox_scheduler.analysis.base_analysis.BaseAnalysis.analysis_steps`.
      Exceptions in these steps are logged and suppressed and analysis is considered
      partially successful.

      This function is typically called right after instantiating an analysis class.

      .. admonition:: Implementing a custom analysis that requires user input
          :class: dropdown, note

          When implementing your own custom analysis you might need to pass in a few
          configuration arguments. That should be achieved by overriding this
          function as show below.

          .. code-block:: python

              from qblox_scheduler.analysis.base_analysis import BaseAnalysis
              from typing_extensions import Self

              class MyAnalysis(BaseAnalysis):
                  def run(self, optional_argument_one: float = 3.5e9) -> Self:
                      # Save the value to be used in some step of the analysis
                      self.optional_argument_one = optional_argument_one

                      # Execute the analysis steps
                      self.execute_analysis_steps()
                      # Return the analysis object
                      return self

                  # ... other relevant methods ...

      :returns: :
                    The instance of the analysis object so that
                    :meth:`~qblox_scheduler.analysis.base_analysis.BaseAnalysis.run()`
                    returns an analysis object.
                    You can initialize, run and assign it to a variable on a
                    single line:, e.g. :code:`a_obj = MyAnalysis().run()`.




.. py:class:: Basic2DAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`BaseAnalysis`


   A basic analysis that extracts the data from the latest file matching the label
   and plots and stores the data in the experiment container.


   .. py:method:: create_figures()

      To be implemented by subclasses.

      Should generate figures of interest. matplolib figures and axes objects should
      be added to the :code:`.figs_mpl` and :code:`axs_mpl` dictionaries.,
      respectively.



.. py:function:: flatten_lmfit_modelresult(model)

   Flatten an lmfit model result to a dictionary in order to be able to save
   it to disk.

   .. rubric:: Notes

   We use this method as opposed to :func:`~lmfit.model.save_modelresult` as the
   corresponding :func:`~lmfit.model.load_modelresult` cannot handle loading data with
   a custom fit function.


.. py:function:: lmfit_par_to_ufloat(param: lmfit.parameter.Parameter)

   Safe conversion of an :class:`lmfit.parameter.Parameter` to
   :code:`uncertainties.ufloat(value, std_dev)`.

   This function is intended to be used in custom analyses to avoid errors when an
   `lmfit` fails and the `stderr` is :code:`None`.

   :param param: The :class:`~lmfit.parameter.Parameter` to be converted

   :returns: :class:`!uncertainties.UFloat` :
                 An object representing the value and the uncertainty of the parameter.



.. py:function:: check_lmfit(fit_res: lmfit.model.ModelResult) -> str

   Check that `lmfit` was able to successfully return a valid fit, and give
   a warning if not.

   The function looks at `lmfit`'s success parameter, and also checks whether
   the fit was able to obtain valid error bars on the fitted parameters.

   :param fit_res: The :class:`~lmfit.model.ModelResult` object output by `lmfit`

   :returns: :
                 A warning message if there is a problem with the fit.



.. py:function:: wrap_text(text: str, width: int = 35, replace_whitespace: bool = True, **kwargs) -> str
                 wrap_text(text: None, width: int = 35, replace_whitespace: bool = True, **kwargs) -> None

   A text wrapping (braking over multiple lines) utility.

   Intended to be used with
   :func:`~quantify_core.visualization.mpl_plotting.plot_textbox` in order to avoid
   too wide figure when, e.g.,
   :func:`~qblox_scheduler.analysis.base_analysis.check_lmfit` fails and
   a warning message is generated.

   For usage see, for example, source code of
   :meth:`~qblox_scheduler.analysis.single_qubit_timedomain.T1Analysis.create_figures`.

   :param text: The text string to be wrapped over several lines.
   :param width: Maximum line width in characters.
   :param replace_whitespace: Passed to :func:`textwrap.wrap` and documented
                              `here <https://docs.python.org/3/library/textwrap.html#textwrap.TextWrapper.replace_whitespace>`_.
   :param kwargs: Any other keyword arguments to be passed to :func:`textwrap.wrap`.

   :returns: :
                 The wrapped text (or :code:`None` if text is :code:`None`).



.. py:function:: analysis_steps_to_str(analysis_steps: enum.Enum, class_name: str = BaseAnalysis.__name__) -> str

   A utility for generating the docstring for the analysis steps.

   :param analysis_steps: An :class:`~enum.Enum` similar to
                          :class:`qblox_scheduler.analysis.base_analysis.AnalysisSteps`.
   :param class_name: The class name that has the `analysis_steps` methods and for which the
                      `analysis_steps` are intended.

   :returns: :
                 A formatted string version of the `analysis_steps` and corresponding methods.



