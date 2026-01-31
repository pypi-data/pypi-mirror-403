loops
=====

.. py:module:: qblox_scheduler.experiments.loops 

.. autoapi-nested-parse::

   Module containing the step to a set a parameter.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.experiments.loops.Loop




.. py:class:: Loop(domains: dict[qblox_scheduler.operations.variables.Variable, qblox_scheduler.operations.loop_domains.LinearDomain], steps: list[qblox_scheduler.experiments.experiment.Step])

   Bases: :py:obj:`qblox_scheduler.experiments.experiment.Step`


   Experiment step that loops other steps over some values.


   .. py:property:: domains
      :type: dict[qblox_scheduler.operations.variables.Variable, qblox_scheduler.operations.loop_domains.LinearDomain]


      Domains to loop over.


   .. py:property:: steps
      :type: list[qblox_scheduler.experiments.experiment.Step]


      Steps to execute.


   .. py:method:: run(device: qblox_scheduler.device_under_test.QuantumDevice, timeout: int = 10) -> xarray.Dataset | None

      Execute step on quantum device.



