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
from qblox_scheduler.operations.pulse_factories import (
    composite_square_pulse,
    non_implemented_pulse,
)
from qblox_scheduler.structure.model import Numbers, Parameter, SchedulerSubmodule

if TYPE_CHECKING:
    from qblox_scheduler.device_under_test.spin_element import BasicSpinElement


class PortSpinEdge(SchedulerSubmodule):
    """Submodule containing the ports."""

    _parent: SpinEdge | None = PrivateAttr(default=None)  # type: ignore[reportIncompatibleVariableOverride]

    gate: str = ""
    """Name of the element's gate port."""

    def _fill_defaults(self) -> None:
        if self.parent and not self.gate:
            self.gate = f"{self.parent.parent_element_name}_{self.parent.child_element_name}:gt"  # type: ignore[reportAttributeAccessIssue]


class SpinInit(SchedulerSubmodule):
    """Submodule containing parameters for performing a SpinInit operation."""


class CZ(SchedulerSubmodule):
    """Submodule containing parameters for performing a CZ operation."""

    square_amp: float = Parameter(
        docstring=r"""Amplitude of the square envelope.""",
        unit="V",
        initial_value=0.0,
        vals=Numbers(min_value=0, allow_nan=True),
    )

    square_duration: float = Parameter(
        docstring=r"""The square pulse duration in seconds.""",
        unit="s",
        initial_value=2e-8,
        vals=Numbers(min_value=0, allow_nan=True),
    )

    parent_phase_correction: float = Parameter(
        docstring=r"""The phase correction for the parent qubit after the """
        r"""square pulse operation has been performed.""",
        unit="degrees",
        initial_value=0.0,
        vals=Numbers(min_value=-1e12, max_value=1e12, allow_nan=True),
    )

    child_phase_correction: float = Parameter(
        docstring=r"""The phase correction for the child qubit after the """
        r"""square pulse operation has been performed.""",
        unit="degrees",
        initial_value=0.0,
        vals=Numbers(min_value=-1e12, max_value=1e12, allow_nan=True),
    )


class CNOT(SchedulerSubmodule):
    """Submodule containing parameters for performing a CNOT operation."""


class SpinEdge(Edge):
    """
    Spin edge implementation which connects two BasicSpinElements.

    This edge implements some operations between the two BasicSpinElements.
    """

    edge_type: Literal["SpinEdge"] = "SpinEdge"  # type: ignore[reportIncompatibleVariableOverride]

    _parent_device_element: BasicSpinElement | None = PrivateAttr(default=None)  # type: ignore[reportIncompatibleVariableOverride]
    _child_device_element: BasicSpinElement | None = PrivateAttr(default=None)  # type: ignore[reportIncompatibleVariableOverride]

    spin_init: SpinInit
    cz: CZ
    cnot: CNOT
    ports: PortSpinEdge

    def generate_edge_config(self) -> dict[str, dict[str, OperationCompilationConfig]]:
        """
        Generate valid device config.

        Fills in the edges information to produce a valid device config for the
        qblox-scheduler making use of the
        :func:`~.circuit_to_device.compile_circuit_to_device_with_config_validation` function.
        """
        edge_op_config = {
            self.name: {
                "SpinInit": OperationCompilationConfig(
                    factory_func=non_implemented_pulse,
                    factory_kwargs={},
                ),
                "CZ": OperationCompilationConfig(
                    factory_func=composite_square_pulse,
                    factory_kwargs={
                        "square_port": self.ports.gate,
                        "square_clock": "cl0.baseband",
                        "square_amp": self.cz.square_amp,
                        "square_duration": self.cz.square_duration,
                        "virt_z_parent_qubit_phase": self.cz.parent_phase_correction,
                        "virt_z_parent_qubit_clock": f"{self.parent_element_name}.f_larmor",
                        "virt_z_child_qubit_phase": self.cz.child_phase_correction,
                        "virt_z_child_qubit_clock": f"{self.child_element_name}.f_larmor",
                    },
                ),
                "CNOT": OperationCompilationConfig(
                    factory_func=non_implemented_pulse,
                    factory_kwargs={},
                ),
            }
        }

        return edge_op_config
