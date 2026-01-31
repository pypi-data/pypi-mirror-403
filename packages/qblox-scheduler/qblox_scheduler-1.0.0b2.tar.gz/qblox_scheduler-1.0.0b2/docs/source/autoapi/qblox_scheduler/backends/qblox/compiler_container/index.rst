compiler_container
==================

.. py:module:: qblox_scheduler.backends.qblox.compiler_container 

.. autoapi-nested-parse::

   Contains the compiler container class.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.compiler_container.CompilerContainer



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.compiler_container._extract_all_resources



.. py:class:: CompilerContainer(schedule: qblox_scheduler.TimeableSchedule)

   Container class that holds all the compiler objects for the individual instruments.

   This class serves to allow all the possible compilation steps that involve multiple
   devices at the same time, such as calculating the modulation frequency for a device
   with a separate local oscillator from a clock that is defined at the schedule level.

   It is recommended to construct this object using the ``from_hardware_cfg`` factory
   method.


   :param schedule: The schedule to be compiled.


   .. py:attribute:: total_play_time

      The total duration of a single repetition of the schedule.


   .. py:attribute:: resources

      The resources attribute of the schedule. Used for getting the information
      from the clocks.


   .. py:attribute:: clusters
      :type:  dict[str, qblox_scheduler.backends.qblox.instrument_compilers.ClusterCompiler]

      Cluster compiler instances managed by this container instance.


   .. py:attribute:: local_oscillators
      :type:  dict[str, qblox_scheduler.backends.qblox.instrument_compilers.LocalOscillatorCompiler]

      Local oscillator compiler instances managed by this container instance.


   .. py:method:: prepare() -> None

      Prepares all the instrument compilers contained in the class,
      by running their respective :code:`prepare` methods.



   .. py:property:: instrument_compilers
      :type: dict[str, qblox_scheduler.backends.qblox.compiler_abc.InstrumentCompiler]


      The compilers for the individual instruments.


   .. py:method:: compile(debug_mode: bool, repetitions: int) -> dict[str, Any]

      Performs the compilation for all the individual instruments.

      :param debug_mode: Debug mode can modify the compilation process,
                         so that debugging of the compilation process is easier.
      :param repetitions: Amount of times to perform execution of the schedule.

      :returns: :
                    Dictionary containing all the compiled programs for each instrument. The key
                    refers to the name of the instrument that the program belongs to.




   .. py:method:: _add_cluster(name: str, instrument_cfg: qblox_scheduler.backends.qblox_backend._ClusterCompilationConfig) -> None


   .. py:method:: _add_local_oscillator(name: str, instrument_cfg: qblox_scheduler.backends.qblox_backend._LocalOscillatorCompilationConfig) -> None


   .. py:method:: from_hardware_cfg(schedule: qblox_scheduler.TimeableSchedule, hardware_cfg: qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig) -> CompilerContainer
      :classmethod:


      Factory method for the CompilerContainer. This is the preferred way to use the
      CompilerContainer class.

      :param schedule: The schedule to pass to the constructor.
      :param hardware_cfg: The hardware compilation config.



.. py:function:: _extract_all_resources(operation: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableScheduleBase) -> dict[str, qblox_scheduler.resources.Resource]

