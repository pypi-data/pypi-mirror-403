backends
========

.. py:module:: qblox_scheduler.backends 


Subpackages
-----------
.. toctree::
   :titlesonly:
   :maxdepth: 3

   qblox/index.rst
   types/index.rst


Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   circuit_to_device/index.rst
   corrections/index.rst
   graph_compilation/index.rst
   qblox_backend/index.rst


Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.SerialCompiler




.. py:class:: SerialCompiler(name: str = 'compiler', quantum_device: qblox_scheduler.device_under_test.quantum_device.QuantumDevice | None = None)

   Bases: :py:obj:`ScheduleCompiler`


   A compiler that executes compilation passes sequentially.


   .. py:method:: construct_graph(config: SerialCompilationConfig) -> None

      Construct the compilation graph based on a provided config.

      For a serial backend, it is just a list of compilation passes.



   .. py:method:: _compilation_func(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, config: SerialCompilationConfig) -> qblox_scheduler.schedules.schedule.CompiledSchedule

      Compile a schedule using the backend and the information provided in the config.

      :param schedule: The schedule to compile.
      :param config: A dictionary containing the information needed to compile the schedule.
                     Nodes in this compiler specify what key they need information from in this
                     dictionary.



