qblox
=====

.. py:module:: qblox_scheduler.qblox 

.. autoapi-nested-parse::

   Module containing commonly used qblox specific classes.



Subpackages
-----------
.. toctree::
   :titlesonly:
   :maxdepth: 3

   operations/index.rst


Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   hardware_agent/index.rst


Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.qblox.ClusterComponent



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.qblox.save_to_experiment
   qblox_scheduler.qblox.start_dummy_cluster_armed_sequencers



.. py:function:: save_to_experiment(tuid: str, dataset: xarray.Dataset | None, save_snapshot: bool = True, save_dataset: bool = True) -> None

   Save a dataset or a snapshot to an experiment folder.

   .. rubric:: Examples

   .. code-block:: python

       dataset = instrument_coordinator.run()
       save_to_experiment(dataset)

   :param dataset: The dataset to save
   :param save_snapshot: Whether to save a snapshot of the experiment
   :param tuid: The time-based unique identifier (TUID) of the form YYYYmmDD-HHMMSS-sss-****** for the
                dataset. Used also for the directory creation where the snapshot is saved
   :param save_dataset: Whether to save the dataset of the experiment


.. py:function:: start_dummy_cluster_armed_sequencers(cluster_component: qblox_scheduler.instrument_coordinator.components.qblox.ClusterComponent) -> None

   Starting all armed sequencers in a dummy cluster.

   Starting all armed sequencers via Cluster.start_sequencer() doesn't yet
   work with dummy acquisition data (verified it does work on hardware).
   Hence, we need still need to call start_sequencer() for all sequencers separately.
   TODO: qblox_instruments.ieee488_2.cluster_dummy_transport.ClusterDummyTransport
   See SE-441.


.. py:class:: ClusterComponent(instrument: qblox_instruments.Cluster)

   Bases: :py:obj:`qblox_scheduler.instrument_coordinator.components.base.InstrumentCoordinatorComponentBase`


   Class that represents an instrument coordinator component for a Qblox cluster.

   New instances of the ClusterComponent will automatically add installed
   modules using name `"<cluster_name>_module<slot>"`.

   :param instrument: Reference to the cluster driver object.


   .. py:class:: _Program

      .. py:attribute:: module_programs
         :type:  dict[str, Any]


      .. py:attribute:: settings
         :type:  qblox_scheduler.backends.types.qblox.ClusterSettings



   .. py:attribute:: _cluster_modules
      :type:  dict[str, qblox_scheduler.instrument_coordinator.components.base.InstrumentCoordinatorComponentBase]


   .. py:attribute:: _program
      :type:  ClusterComponent | None
      :value: None



   .. py:attribute:: cluster


   .. py:property:: is_running
      :type: bool


      Returns true if any of the modules are currently running.


   .. py:method:: _set_parameter(instrument: qcodes.instrument.instrument_base.InstrumentBase, parameter_name: str, val: Any) -> None

      Set the parameter directly or using the lazy set.

      :param instrument: The instrument or instrument channel that holds the parameter to set,
                         e.g. `self.instrument` or `self.instrument[f"sequencer{idx}"]`.
      :param parameter_name: The name of the parameter to set.
      :param val: The new value of the parameter.



   .. py:method:: start() -> None

      Starts all the modules in the cluster.



   .. py:method:: _sync_on_external_trigger(settings: qblox_scheduler.backends.types.qblox.ExternalTriggerSyncSettings) -> None


   .. py:method:: stop() -> None

      Stops all the modules in the cluster.



   .. py:method:: prepare(program: dict[str, dict | qblox_scheduler.backends.types.qblox.ClusterSettings]) -> None

      Prepares the cluster component for execution of a schedule.

      :param program: The compiled instructions to configure the cluster to.
      :param acq_channels_data: Acquisition channels data for acquisition mapping.
      :param repetitions: Repetitions of the schedule.



   .. py:method:: retrieve_acquisition() -> xarray.Dataset | None

      Retrieves all the data from the instruments.

      :returns: :
                    The acquired data or ``None`` if no acquisitions have been performed.




   .. py:method:: wait_done(timeout_sec: int = 10) -> None

      Blocks until all the components are done executing their programs.

      :param timeout_sec: The time in seconds until the instrument is considered to have timed out.



   .. py:method:: get_hardware_log(compiled_schedule: qblox_scheduler.schedules.schedule.CompiledSchedule) -> dict | None

      Retrieve the hardware log of the Cluster Management Module and associated modules.

      This log includes the module serial numbers and
      firmware version.

      :param compiled_schedule: Compiled schedule to check if this cluster is referenced in (and if so,
                                which specific modules are referenced in).

      :returns: :
                    A dict containing the hardware log of the cluster, in case the
                    component was referenced; else None.




   .. py:method:: get_module_descriptions() -> dict[int, qblox_scheduler.backends.types.qblox.ClusterModuleDescription]

      Get the module types of this cluster, indexed by their position in the cluster.


      :returns: :
                    A dictionary containing the module types in this cluster,
                    indexed by their position in the cluster.




