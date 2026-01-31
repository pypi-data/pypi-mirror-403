time_of_flight_analysis
=======================

.. py:module:: qblox_scheduler.analysis.time_of_flight_analysis 

.. autoapi-nested-parse::

   Module containing analysis class for time of flight measurement.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.time_of_flight_analysis.TimeOfFlightAnalysis




.. py:class:: TimeOfFlightAnalysis(dataset: xarray.Dataset | None = None, tuid: quantify_core.data.types.TUID | str | None = None, label: str = '', settings_overwrite: dict | None = None, plot_figures: bool = True)

   Bases: :py:obj:`qblox_scheduler.analysis.base_analysis.BaseAnalysis`


   Analysis for time of flight measurement.


   .. py:method:: run(acquisition_delay: float = 4e-09, playback_delay: float = 1.46e-07) -> qblox_scheduler.analysis.base_analysis.BaseAnalysis

      Execute analysis steps and let user specify `acquisition_delay`.

      Assumes that the sample time is always 1 ns.

      :param acquisition_delay: Time from the start of the pulse to the start of the measurement in seconds.
                                By default 4 ns.
      :param playback_delay: Time from the start of playback to appearance of pulse at the output
                             of the instrument in seconds. By default 146 ns, which is the playback
                             delay for Qblox instruments.

      :returns: :
                    The instance of the analysis object.




   .. py:method:: process_data() -> None

      Populate the :code:`.dataset_processed`.



   .. py:method:: analyze_fit_results() -> None

      Check fit success and populates :code:`.quantities_of_interest`.



   .. py:method:: create_figures() -> None

      Display the Data and the measured time of flight.



