generic
=======

.. py:module:: qblox_scheduler.instrument_coordinator.components.generic 

.. autoapi-nested-parse::

   Module containing a Generic InstrumentCoordinator Component.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.instrument_coordinator.components.generic.GenericInstrumentCoordinatorComponent




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.instrument_coordinator.components.generic.logger
   qblox_scheduler.instrument_coordinator.components.generic.DEFAULT_NAME


.. py:data:: logger

.. py:data:: DEFAULT_NAME
   :value: 'generic'


.. py:class:: GenericInstrumentCoordinatorComponent(instrument_reference: str | qcodes.instrument.instrument_base.InstrumentBase = DEFAULT_NAME)

   Bases: :py:obj:`qblox_scheduler.instrument_coordinator.components.base.InstrumentCoordinatorComponentBase`


   A Generic class which can be used for interaction with the InstrumentCoordinator.

   The GenericInstrumentCoordinatorComponent should be able to accept any type of
   qcodes instrument. The component is meant to serve as an interface for simple
   access to instruments such as the local oscillator, or current source which needs to
   only set parameters. For now this component is not being used in any of the hardware
   backends' compilation step. This will be fixed in the next official release.


   .. py:attribute:: _no_gc_instances
      :type:  ClassVar[dict[str, qcodes.instrument.instrument_base.InstrumentBase]]


   .. py:property:: is_running
      :type: bool


      A state whether an instrument is capable of running in a program.

      Not to be confused with the on/off state of an
      instrument.


   .. py:method:: start() -> None

      Start the instrument.



   .. py:method:: stop() -> None

      Stop the instrument.



   .. py:method:: prepare(params_config: dict[str, Any]) -> None

      Prepare the instrument.

      params_config has keys which should correspond to parameter names of the
      instrument and the corresponding values to be set. Always ensure that the
      key to the params_config is in the format 'instrument_name.parameter_name'
      See example below.

      .. code-block:: python

          params_config = {
                           "lo_mw_q0.frequency": 6e9,
                           "lo_mw_q0.power": 13, "lo_mw_q0.status": True,
                           "lo_ro_q0.frequency": 8.3e9, "lo_ro_q0.power": 16,
                           "lo_ro_q0.status": True,
                           "lo_spec_q0.status": False,
                          }




   .. py:method:: _set_params_to_devices(params_config: dict) -> None

      Set the parameters in the params_config dict
      to the generic devices set in the hardware_config.

      The bool force_set_parameters is used to
      change the lazy_set behavior.



   .. py:method:: retrieve_acquisition() -> xarray.Dataset | None

      Retrieve acquisition.



   .. py:method:: get_hardware_log(compiled_schedule: qblox_scheduler.schedules.schedule.CompiledSchedule) -> dict | None

      Get the hardware log.



   .. py:method:: wait_done(timeout_sec: int = 10) -> None

      Wait till done.



