diagnostics_report
==================

.. py:module:: qblox_scheduler.helpers.diagnostics_report 

.. autoapi-nested-parse::

   Helper functions for debugging experiments.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.helpers.diagnostics_report._generate_diagnostics_report



.. py:function:: _generate_diagnostics_report(quantum_device: qblox_scheduler.device_under_test.quantum_device.QuantumDevice, gettable_config: dict[str, Any], schedule: qblox_scheduler.schedule.Schedule | qblox_scheduler.schedules.schedule.TimeableSchedule, instrument_coordinator: qblox_scheduler.instrument_coordinator.instrument_coordinator.InstrumentCoordinator, initialized: bool, compiled_schedule: qblox_scheduler.schedules.schedule.CompiledSchedule | None, acquisition_data: tuple[numpy.ndarray, Ellipsis] | None, experiment_exception: tuple[type[BaseException], BaseException, types.TracebackType] | tuple[None, None, None] | None) -> str

   Generate a report with the current state of an experiment for debugging.

   :returns: :
                 A path to the generated zipfile report.



