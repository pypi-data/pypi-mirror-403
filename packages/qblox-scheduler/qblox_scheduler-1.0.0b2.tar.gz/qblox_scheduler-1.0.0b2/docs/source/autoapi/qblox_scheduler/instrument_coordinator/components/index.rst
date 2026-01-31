components
==========

.. py:module:: qblox_scheduler.instrument_coordinator.components 

.. autoapi-nested-parse::

   .. list-table::
       :header-rows: 1
       :widths: auto

       * - Import alias
         - Maps to
       * - :class:`!qblox_scheduler.instrument_coordinator.components.InstrumentCoordinatorComponentBase`
         - :class:`.InstrumentCoordinatorComponentBase`



Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   base/index.rst
   generic/index.rst
   qblox/index.rst


Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.instrument_coordinator.components.InstrumentCoordinatorComponentBase




.. py:class:: InstrumentCoordinatorComponentBase(instrument: qcodes.instrument.InstrumentBase, **kwargs: Any)

   Bases: :py:obj:`qcodes.instrument.Instrument`


   The InstrumentCoordinator component abstract interface.


   .. py:attribute:: _no_gc_instances
      :type:  ClassVar[dict[str, qcodes.instrument.InstrumentBase]]


   .. py:method:: close() -> None

      Release instances so that garbage collector can claim the objects.

      NB We don't close the instrument because it might be referenced elsewhere.



   .. py:attribute:: instrument_ref


   .. py:attribute:: force_set_parameters


   .. py:property:: instrument
      :type: qcodes.instrument.InstrumentBase


      Returns the instrument referenced by `instrument_ref`.


   .. py:property:: is_running
      :type: bool

      :abstractmethod:


      Returns if the InstrumentCoordinator component is running.

      The property ``is_running`` is evaluated each time it is accessed. Example:

      .. code-block::

          while my_instrument_coordinator_component.is_running:
              print('running')

      :returns: :
                    The components' running state.


   .. py:method:: start() -> None
      :abstractmethod:


      Starts the InstrumentCoordinator Component.



   .. py:method:: stop() -> None
      :abstractmethod:


      Stops the InstrumentCoordinator Component.



   .. py:method:: prepare(program: Any) -> None
      :abstractmethod:


      Initializes the InstrumentCoordinator Component with parameters.



   .. py:method:: retrieve_acquisition() -> xarray.Dataset | None
      :abstractmethod:


      Gets and returns acquisition data.



   .. py:method:: wait_done(timeout_sec: int = 10) -> None
      :abstractmethod:


      Wait until the InstrumentCoordinator is done.

      The coordinator is ready when it has stopped running or until it
      has exceeded the amount of time to run.

      The maximum amount of time, in seconds, before it times out is set via the
      timeout_sec parameter.

      :param timeout_sec: The maximum amount of time in seconds before a timeout.



   .. py:method:: get_hardware_log(compiled_schedule: qblox_scheduler.schedules.schedule.CompiledSchedule) -> dict | None
      :abstractmethod:


      Retrieve the hardware logs of the instrument associated to this component.



