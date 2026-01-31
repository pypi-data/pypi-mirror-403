# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""The module provides classes related CZ operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import PrivateAttr

from qblox_scheduler.backends.graph_compilation import OperationCompilationConfig
from qblox_scheduler.device_under_test.edge import Edge
from qblox_scheduler.operations.pulse_factories import composite_square_pulse
from qblox_scheduler.resources import BasebandClockResource
from qblox_scheduler.structure.model import Numbers, Parameter, SchedulerSubmodule

if TYPE_CHECKING:
    from qblox_scheduler.device_under_test.transmon_element import BasicTransmonElement


class CZ(SchedulerSubmodule):
    """Submodule containing parameters for performing a CZ operation."""

    square_amp: float = Parameter(
        docstring=r"""Amplitude of the square envelope.""",
        unit="V",
        initial_value=0.5,
        vals=Numbers(min_value=0, max_value=1e12, allow_nan=True),
    )

    square_duration: float = Parameter(
        docstring=r"""The square pulse duration in seconds.""",
        unit="s",
        initial_value=2e-8,
        vals=Numbers(min_value=0, max_value=1e12, allow_nan=True),
    )

    parent_phase_correction: float = Parameter(
        docstring=r"""The phase correction for the parent qubit after the
        square pulse operation has been performed.""",
        unit="degrees",
        initial_value=0.0,
        vals=Numbers(min_value=-1e12, max_value=1e12, allow_nan=True),
    )

    child_phase_correction: float = Parameter(
        docstring=r"""The phase correction for the child qubit after the
        square pulse operation has been performed.""",
        unit="degrees",
        initial_value=0.0,
        vals=Numbers(min_value=-1e12, max_value=1e12, allow_nan=True),
    )


class CompositeSquareEdge(Edge):
    """
    An example Edge implementation which connects two BasicTransmonElements.

    This edge implements a square flux pulse and two virtual z
    phase corrections for the CZ operation between the two BasicTransmonElements.
    """

    edge_type: Literal["CompositeSquareEdge"] = "CompositeSquareEdge"  # type: ignore[reportIncompatibleVariableOverride]

    _parent_device_element: BasicTransmonElement | None = PrivateAttr(default=None)  # type: ignore[reportIncompatibleVariableOverride]
    _child_device_element: BasicTransmonElement | None = PrivateAttr(default=None)  # type: ignore[reportIncompatibleVariableOverride]

    cz: CZ

    def generate_edge_config(self) -> dict[str, dict[str, OperationCompilationConfig]]:
        """
        Generate valid device config.

        Fills in the edges information to produce a valid device config for the
        qblox-scheduler making use of the
        :func:`~.circuit_to_device.compile_circuit_to_device_with_config_validation` function.
        """
        # TODO: It would be better if we didn't depend on `self.parent_element`.
        if self.parent_element is None or self.child_element is None:
            raise ValueError(
                f"Unable to generate edge configuration for {self.name} because it cannot access "
                f"a related DeviceElement. Please add the edge to a QuantumDevice."
            )

        edge_op_config = {
            self.name: {
                "CZ": OperationCompilationConfig(
                    factory_func=composite_square_pulse,
                    factory_kwargs={
                        "square_port": self.parent_element.ports.flux,  # type: ignore[reportAttributeAccessIssue]
                        "square_clock": BasebandClockResource.IDENTITY,
                        "square_amp": self.cz.square_amp,
                        "square_duration": self.cz.square_duration,
                        "virt_z_parent_qubit_phase": self.cz.parent_phase_correction,
                        "virt_z_parent_qubit_clock": f"{self.parent_element_name}.01",
                        "virt_z_child_qubit_phase": self.cz.child_phase_correction,
                        "virt_z_child_qubit_clock": f"{self.child_element_name}.01",
                    },
                ),
            }
        }

        return edge_op_config
