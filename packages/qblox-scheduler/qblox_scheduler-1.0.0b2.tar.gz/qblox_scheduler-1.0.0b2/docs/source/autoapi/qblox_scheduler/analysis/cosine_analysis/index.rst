cosine_analysis
===============

.. py:module:: qblox_scheduler.analysis.cosine_analysis 

.. autoapi-nested-parse::

   Module containing an education example of an analysis subclass.

   See :ref:`analysis-framework-tutorial` that guides you through the process of building
   this analysis.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.cosine_analysis.CosineAnalysis




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



