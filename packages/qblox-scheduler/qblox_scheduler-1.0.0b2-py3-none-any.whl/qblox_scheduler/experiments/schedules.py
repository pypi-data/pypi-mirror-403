# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2025, Qblox B.V.
"""Module containing the the step to execute a schedule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qblox_scheduler.backends.graph_compilation import SerialCompiler
from qblox_scheduler.experiments.experiment import Step
from qblox_scheduler.schedules.schedule import (
    CompiledSchedule,
    TimeableSchedule,
)

if TYPE_CHECKING:
    from xarray import Dataset

    from qblox_scheduler.device_under_test import QuantumDevice
    from qblox_scheduler.schedules.schedule import TimeableScheduleBase


class ExecuteSchedule(Step):
    """Experiment step that runs a schedule."""

    def __init__(self, schedule: TimeableScheduleBase) -> None:
        super().__init__(f"run schedule {schedule.name}")
        self.data["schedule_info"] = {
            "schedule": schedule,
        }
        self.compiled_schedule: CompiledSchedule | None = None

    @property
    def schedule(self) -> TimeableScheduleBase:
        """The schedule to run."""
        return self.data["schedule_info"]["schedule"]

    def run(self, device: QuantumDevice, timeout: int = 10) -> Dataset:
        """Run a schedule on the quantum device."""
        schedule = self.schedule
        if isinstance(schedule, CompiledSchedule):
            self.compiled_schedule = schedule
        elif isinstance(schedule, TimeableSchedule):
            compiler = SerialCompiler(name="compiler")
            self.compiled_schedule = compiler.compile(
                schedule=schedule,
                config=device.generate_compilation_config(),
            )
        else:
            raise RuntimeError(f"uncompileable schedule {schedule}")

        inst_coord = device.instr_instrument_coordinator
        if not inst_coord:
            raise RuntimeError(
                "QuantumDevice needs to have an active instrument coordinator to run a schedule"
            )
        inst_coord.stop(allow_failure=True)
        inst_coord.prepare(self.compiled_schedule)
        inst_coord.start()
        inst_coord.wait_done(timeout_sec=timeout)

        return inst_coord.retrieve_acquisition()
