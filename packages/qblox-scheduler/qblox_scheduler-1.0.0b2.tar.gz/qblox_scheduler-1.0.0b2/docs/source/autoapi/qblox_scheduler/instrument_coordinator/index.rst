instrument_coordinator
======================

.. py:module:: qblox_scheduler.instrument_coordinator 

.. autoapi-nested-parse::

   .. list-table::
       :header-rows: 1
       :widths: auto

       * - Import alias
         - Target
       * - :class:`.InstrumentCoordinator`
         - :class:`!qblox_scheduler.instrument_coordinator.InstrumentCoordinator`



Subpackages
-----------
.. toctree::
   :titlesonly:
   :maxdepth: 3

   components/index.rst


Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   instrument_coordinator/index.rst
   utility/index.rst


Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.instrument_coordinator.InstrumentCoordinator




.. py:class:: InstrumentCoordinator(name: str, add_default_generic_icc: bool = True)

   Bases: :py:obj:`qcodes.instrument.instrument.Instrument`


   The :class:`~.InstrumentCoordinator` serves as
   the central interface of the hardware abstraction layer.

   It provides a standardized interface to execute Schedules on
   control hardware.

   The :class:`~.InstrumentCoordinator` has two main functionalities exposed to the
   user, the ability to configure its
   :mod:`~.instrument_coordinator.components`
   representing physical instruments, and the ability to execute experiments.


   .. admonition:: Executing a schedule using the instrument coordinator
       :class: dropdown

       To execute a :class:`~.TimeableSchedule` , one needs to first
       compile a schedule and then configure all the instrument coordinator components
       using :meth:`~.InstrumentCoordinator.prepare`.
       After starting the experiment, the results can be retrieved using
       :meth:`~.InstrumentCoordinator.retrieve_acquisition`.

       .. code-block::

           from qblox_scheduler.backends.graph_compilation import SerialCompiler

           my_sched: TimeableSchedule = ...  # a schedule describing the experiment to perform
           quantum_device: QuantumDevice = ...  # the device under test
           hardware_config: dict = ...  # a config file describing the connection to the hardware

           quantum_device.hardware_config = hardware_config

           compiler = SerialCompiler(name="compiler")
           compiled_sched = compiler.compile(
               schedule=sched, config=quantum_device.generate_compilation_config()
           )

           instrument_coordinator.prepare(compiled_sched)
           instrument_coordinator.start()
           dataset = instrument_coordinator.retrieve_acquisition()

   .. admonition:: Adding components to the instrument coordinator
       :class: dropdown

       In order to distribute compiled instructions and execute an experiment,
       the instrument coordinator needs to have references to the individual
       instrument coordinator components. They can be added using
       :meth:`~.InstrumentCoordinator.add_component`.

       .. code-block::

           instrument_coordinator.add_component(qcm_component)

   :param name: The name for the instrument coordinator instance.
   :param add_default_generic_icc: If True, automatically adds a GenericInstrumentCoordinatorComponent to this
                                   instrument coordinator with the default name.


   .. py:attribute:: components


   .. py:attribute:: timeout


   .. py:attribute:: _last_schedule
      :value: None



   .. py:attribute:: _compiled_schedule
      :value: None



   .. py:property:: last_schedule
      :type: qblox_scheduler.schedules.schedule.CompiledSchedule


      Returns the last schedule used to prepare the instrument coordinator.

      This feature is intended to aid users in debugging.


   .. py:property:: is_running
      :type: bool


      Returns if any of the :class:`.InstrumentCoordinator` components is running.

      :returns: :
                    The :class:`.InstrumentCoordinator`'s running state.


   .. py:method:: get_component(full_name: str) -> qblox_scheduler.instrument_coordinator.components.base.InstrumentCoordinatorComponentBase

      Returns the InstrumentCoordinator component by name.

      :param full_name: The component name.

      :returns: :
                    The component.

      :raises KeyError: If key ``name`` is not present in ``self.components``.



   .. py:method:: add_component(component: qblox_scheduler.instrument_coordinator.components.base.InstrumentCoordinatorComponentBase) -> None

      Adds a component to the components collection.

      :param component: The component to add.

      :raises ValueError: If a component with a duplicated name is added to the collection.
      :raises TypeError: If :code:`component` is not an instance of the base component.



   .. py:method:: remove_component(name: str) -> None

      Removes a component by name.

      :param name: The component name.



   .. py:method:: prepare(compiled_schedule: qblox_scheduler.schedules.schedule.CompiledSchedule) -> None

      Prepares each component for execution of a schedule.

      It attempts to configure all instrument coordinator components for which
      compiled instructions, typically consisting of a combination of sequence
      programs, waveforms and other instrument settings, are available in the
      compiled schedule.


      :param compiled_schedule: A schedule containing the information required to execute the program.

      :raises KeyError: If the compiled schedule contains instructions for a component
          absent in the instrument coordinator.
      :raises TypeError: If the schedule provided is not a valid :class:`.CompiledSchedule`.



   .. py:method:: start() -> None

      Start all of the components that appear in the compiled instructions.

      The instruments will be started in the order in which they were added to the
      instrument coordinator.



   .. py:method:: stop(allow_failure: bool = False) -> None

      Stops all components.

      The components are stopped in the order in which they were added.

      :param allow_failure: By default it is set to `False`. When set to `True`, the AttributeErrors
                            raised by a component are demoted to warnings to allow other
                            components to stop.



   .. py:method:: retrieve_acquisition() -> xarray.Dataset

      Retrieves the latest acquisition results of the components with acquisition capabilities.

      :returns: :
                    The acquisition data in an :code:`xarray.Dataset`.
                    For each acquisition channel it contains an :code:`xarray.DataArray`.




   .. py:method:: wait_done(timeout_sec: int = 10) -> None

      Awaits each component until it is done.

      The timeout in seconds specifies the allowed amount of time to run before
      it times out.

      :param timeout_sec: The maximum amount of time in seconds before a timeout.



   .. py:method:: retrieve_hardware_logs() -> dict[str, dict]

      Return the hardware logs of the instruments of each component.

      The instruments must be referenced in the :class:`.CompiledSchedule`.

      :returns: :
                    A nested dict containing the components hardware logs




