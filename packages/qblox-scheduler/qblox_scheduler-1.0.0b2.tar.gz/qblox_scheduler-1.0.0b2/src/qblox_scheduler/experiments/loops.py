# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2025, Qblox B.V.
"""Module containing the step to a set a parameter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tqdm.autonotebook import trange

from qblox_scheduler.experiments.experiment import Step
from qblox_scheduler.instrument_coordinator.utility import merge_acquisition_sets

if TYPE_CHECKING:
    from xarray import Dataset

    from qblox_scheduler.device_under_test import QuantumDevice
    from qblox_scheduler.operations.expressions import Expression
    from qblox_scheduler.operations.loop_domains import LinearDomain
    from qblox_scheduler.operations.variables import Variable


class Loop(Step):
    """Experiment step that loops other steps over some values."""

    def __init__(self, domains: dict[Variable, LinearDomain], steps: list[Step]) -> None:
        super().__init__(f"loop steps over {domains}")
        self.data["loop_info"] = {
            "domains": domains,
            "steps": steps,
        }

    @property
    def domains(self) -> dict[Variable, LinearDomain]:
        """Domains to loop over."""
        return self.data["loop_info"]["domains"]

    @property
    def steps(self) -> list[Step]:
        """Steps to execute."""
        return self.data["loop_info"]["steps"]

    def run(self, device: QuantumDevice, timeout: int = 10) -> Dataset | None:
        """Execute step on quantum device."""
        if not self.domains:
            return

        data_set = None
        nsteps = len(next(iter(self.domains.values())))
        values = {var: iter(dom.values()) for var, dom in self.domains.items()}
        for _ in trange(nsteps, unit="step"):
            substitutions: dict[Expression, Expression | int | float | complex] = {
                var: next(values) for var, values in values.items()
            }
            for step in self.steps:
                sub_step = step.substitute(substitutions)
                sub_data_set = sub_step.run(device, timeout=timeout)
                if sub_data_set is not None:
                    if data_set is None:
                        data_set = sub_data_set
                    else:
                        data_set = merge_acquisition_sets(data_set, sub_data_set)

        return data_set
