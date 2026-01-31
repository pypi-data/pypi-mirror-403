gettables
=========

.. py:module:: qblox_scheduler.gettables 

.. autoapi-nested-parse::

   Module containing :class:`quantify_core.measurement.types.Gettable`\s for use with
   qblox-scheduler.

   .. warning::

       The gettable module is expected to change significantly as the
       acquisition protocols (#36 and #80) get fully supported by the scheduler.
       Currently different Gettables are required for different acquisition modes.
       The intent is to have one generic ``ScheduleGettable``.
       Expect breaking changes.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.gettables.ScheduleGettable



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.gettables._evaluate_parameter_dict



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.gettables.logger


.. py:data:: logger

.. py:class:: ScheduleGettable(quantum_device: qblox_scheduler.device_under_test.quantum_device.QuantumDevice, schedule_function: collections.abc.Callable[Ellipsis, qblox_scheduler.schedule.Schedule | qblox_scheduler.schedule.TimeableSchedule], schedule_kwargs: dict[str, Any], num_channels: int = 1, data_labels: list[str] | None = None, real_imag: bool = True, batched: bool = False, max_batch_size: int = 1024, always_initialize: bool = True, return_xarray: bool = False)

   Generic gettable for a quantify schedule using vector (I,Q) acquisition.

   The gettable evaluates the parameters passed as ``schedule_kwargs``, then generates
   the :class:`qblox_scheduler.schedules.schedule.TimeableSchedule` using the
   ``schedule_function``, this is then compiled and finally executed by the
   :class:`~.InstrumentCoordinator`.

   ``ScheduleGettable`` can be set to return either static (demodulated) I and Q
   values or magnitude and phase.

   :param quantum_device: The qcodes instrument representing the quantum device under test (DUT)
                          containing quantum device properties and setup configuration information.
   :param schedule_function: A function which returns a :class:`qblox_scheduler.schedule.Schedule` or
                             :class:`qblox_scheduler.schedules.schedule.TimeableSchedule`. The
                             function is required to have the ``repetitions`` keyword argument.
   :param schedule_kwargs: The schedule function keyword arguments, when a value in this dictionary is
                           a :class:`~qcodes.parameters.parameter.Parameter`, this parameter will be
                           evaluated every time :code:`.get()` is called before being passed to the
                           :code:`schedule_function`.
   :param num_channels: The number of channels to expect in the acquisition data.
   :param data_labels: Allows to specify custom labels. Needs to be precisely 2*num_channels if
                       specified. The order is [Voltage I 0, Voltage Q 0, Voltage I 1, Voltage Q 1,
                       ...], in case real_imag==True, otherwise [Magnitude 0, Phase 0, Magnitude 1,
                       Phase 1, ...].
   :param real_imag: If true, the gettable returns I, Q values. Otherwise, magnitude and phase
                     (degrees) are returned.
   :param batched: Used to indicate if the experiment is performed in batches or in an
                   iterative fashion.
   :param max_batch_size: Determines the maximum number of points to acquire when acquiring in batched
                          mode. Can be used to split up a program in parts if required due to hardware
                          constraints.
   :param always_initialize: If True, then reinitialize the schedule on each invocation of ``get``. If
                             False, then only initialize the first invocation of ``get``.


   .. py:attribute:: _data_labels_specified


   .. py:attribute:: always_initialize
      :value: True



   .. py:attribute:: is_initialized
      :value: False



   .. py:attribute:: _compiled_schedule
      :type:  qblox_scheduler.schedules.schedule.CompiledSchedule | None
      :value: None



   .. py:attribute:: real_imag
      :value: True



   .. py:attribute:: batched
      :value: False



   .. py:attribute:: batch_size
      :value: 1024



   .. py:attribute:: _return_xarray
      :value: False



   .. py:attribute:: schedule_function


   .. py:attribute:: schedule_kwargs


   .. py:attribute:: _evaluated_sched_kwargs


   .. py:attribute:: quantum_device


   .. py:attribute:: _backend
      :value: None



   .. py:attribute:: _debug_mode
      :type:  bool
      :value: False



   .. py:method:: compile() -> qblox_scheduler.schedules.schedule.CompiledSchedule

      Compile the schedule without preparing and running it.
      The returned compiled schedule can be used to
      plot the circuit or pulse diagrams for example.

      :returns: :
                    The compiled schedule.




   .. py:method:: initialize() -> None

      Generates the schedule and uploads the compiled instructions to the
      hardware using the instrument coordinator.



   .. py:property:: compiled_schedule
      :type: qblox_scheduler.schedules.schedule.CompiledSchedule | None


      Get the latest compiled schedule, or None if nothing has been compiled yet.


   .. py:method:: get() -> tuple[numpy.ndarray, Ellipsis]

      Start the experimental sequence and retrieve acquisition data.

      The data format returned is dependent on the type of acquisitions used
      in the schedule. These data formats can be found in the :ref:`user guide
      <sec-user-guide-acquisition-data-schedulegettable>`.

      :returns: :
                    A tuple of acquisition data per acquisition channel as specified above.




   .. py:method:: initialize_and_get_with_report() -> str

      Create a report that saves all information from this experiment in a zipfile.

      Run :meth:`~.ScheduleGettable.initialize` and :meth:`~.ScheduleGettable.get`
      and capture all information from the experiment in a zipfile in the quantify
      datadir.
      The basic information in the report includes the schedule, device config and
      hardware config. The method attempts to compile the schedule, and if it
      succeeds, it runs the experiment and adds the compiled schedule, a snapshot of
      the instruments, and logs from the actual hardware (only Qblox instruments
      supported currently) to the zipfile.
      A full error trace is also included if any of these steps fail.

      :returns: :
                    A path to the generated report. Directory name includes a flag indicating at
                    which state the experiment and report retrieval stopped.

                    Flags (defined in :func: `~._generate_diagnostics_report`):

                    - ``failed_initialization``: The experiment failed during             :meth:`~.ScheduleGettable.initialize`.
                    - ``failed_exp``: The experiment initialized failed during             :meth:`~.ScheduleGettable.get`.
                    - ``failed_connection_to_hw``: The experiment initialized but both             :meth:`~.ScheduleGettable.get` and             :meth:`~.InstrumentCoordinator.retrieve_hardware_logs` failed. Connection             to hardware was likely interrupted during runtime.
                    - ``failed_hw_log_retrieval``: The experiment succeeded but             :meth:`~.InstrumentCoordinator.retrieve_hardware_logs` failed.
                    - ``completed_exp``: The experiment succeeded.




.. py:function:: _evaluate_parameter_dict(parameters: dict[str, Any]) -> dict[str, Any]

   Loop over the keys and values in a dict and replaces parameters with their current
   value.

   :param parameters: A dictionary containing a mix of
                      :class:`~qcodes.parameters.parameter.Parameter`\s and normal values.

   :returns: :
                 The ``parameters`` dictionary, but with the parameters replaced by their current
                 value.

   :raises TypeError: If a parameter returns None


