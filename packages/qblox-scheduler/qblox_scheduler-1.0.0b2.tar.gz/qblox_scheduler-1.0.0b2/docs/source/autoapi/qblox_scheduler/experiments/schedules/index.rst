schedules
=========

.. py:module:: qblox_scheduler.experiments.schedules 

.. autoapi-nested-parse::

   Module containing the the step to execute a schedule.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.experiments.schedules.ExecuteSchedule




.. py:class:: ExecuteSchedule(schedule: qblox_scheduler.schedules.schedule.TimeableScheduleBase)

   Bases: :py:obj:`qblox_scheduler.experiments.experiment.Step`


   Experiment step that runs a schedule.


   .. py:attribute:: compiled_schedule
      :type:  qblox_scheduler.schedules.schedule.CompiledSchedule | None
      :value: None



   .. py:property:: schedule
      :type: qblox_scheduler.schedules.schedule.TimeableScheduleBase


      The schedule to run.


   .. py:method:: run(device: qblox_scheduler.device_under_test.QuantumDevice, timeout: int = 10) -> xarray.Dataset

      Run a schedule on the quantum device.



