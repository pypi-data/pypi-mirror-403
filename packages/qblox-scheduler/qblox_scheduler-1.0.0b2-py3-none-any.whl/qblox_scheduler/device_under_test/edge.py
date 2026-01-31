# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""The module contains definitions for edges."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, ClassVar
from typing_extensions import Self

from pydantic import ModelWrapValidatorHandler, PrivateAttr, model_validator

from qblox_scheduler.device_under_test.device_element import DeviceElement
from qblox_scheduler.structure.model import SchedulerBaseModel, SchedulerSubmodule

if TYPE_CHECKING:
    from qblox_scheduler.backends.graph_compilation import OperationCompilationConfig


class Edge(abc.ABC, SchedulerBaseModel):
    """
    Create an Edge.

    This class encapsulates the connection information between DeviceElements in the
    QuantumDevice. It provides an interface for the QuantumDevice to generate the
    edge information for use in the device compilation step. See
    :class:`qblox_scheduler.device_under_test.composite_square_edge` for an example
    edge implementation.
    """

    __model_registry__: ClassVar[dict[str, type[Edge]]] = {}

    edge_type: str
    parent_element_name: str
    child_element_name: str

    _parent_device_element: DeviceElement | None = PrivateAttr(default=None)
    _child_device_element: DeviceElement | None = PrivateAttr(default=None)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:  # noqa: ANN401
        """Store new subclasses of :class:`~Edge` into a class-level registry."""
        super().__pydantic_init_subclass__(**kwargs)
        Edge.__model_registry__[cls.__name__] = cls

    def __init__(
        self,
        parent_element: DeviceElement | str | None = None,
        child_element: DeviceElement | str | None = None,
        **data: Any,  # noqa: ANN401
    ) -> None:
        if not data.get("parent_element_name"):
            data["parent_element_name"] = self._get_element_name(parent_element)
        if not data.get("child_element_name"):
            data["child_element_name"] = self._get_element_name(child_element)

        if not data.get("name"):
            data["name"] = f"{data['parent_element_name']}_{data['child_element_name']}"

        super().__init__(**data)

        if isinstance(parent_element, DeviceElement):
            self._parent_device_element = parent_element
        if isinstance(child_element, DeviceElement):
            self._child_device_element = child_element

    def __getstate__(self) -> dict[str, Any]:
        """Get the state of :class:`~Edge` (used for YAML serialization)."""
        return self.model_dump(exclude={"edge_type"})

    @model_validator(mode="before")
    @classmethod
    def include_submodule_names(cls, data: Any) -> Any:  # noqa: ANN401
        """
        Fill in the ``name`` attribute of :class:`~Edge` submodules when missing
        (used for YAML deserialization, they are omitted at serialization).
        """
        if isinstance(data, dict):
            for submodule_name, submodule_data in data.items():
                if submodule_name in (
                    "name",
                    "edge_type",
                    "parent_element_name",
                    "child_element_name",
                ):
                    continue
                if "name" not in submodule_data:
                    submodule_data["name"] = submodule_name
        return data

    @model_validator(mode="wrap")
    @classmethod
    def dispatch_concrete_model(
        cls,
        data: Any,  # noqa: ANN401
        handler: ModelWrapValidatorHandler[Self],
    ) -> Self:
        """
        When deserializing a dict representation of a concrete :class:`~Edge`,
        infer the matching class by looking its `edge_type` into the model registry
        and return a validated instance of the concrete edge.
        """
        if cls is Edge and isinstance(data, dict):
            edge_type = data.get("edge_type")
            if edge_type in cls.__model_registry__:
                return cls.__model_registry__[edge_type].model_validate(data)  # type: ignore[reportReturnType]
            else:
                raise ValueError(f"unknown edge type '{edge_type}'")

        return handler(data)

    @property
    def parent_element(self) -> DeviceElement | None:
        """Getter for the internal parent device element."""
        return self._parent_device_element

    @property
    def child_element(self) -> DeviceElement | None:
        """Getter for the internal child device element."""
        return self._child_device_element

    @property
    def submodules(self) -> dict[str, Any]:
        """Mapping of submodules of this edge."""
        return {
            field_name: field_value
            for field_name, field_value in self
            if isinstance(field_value, SchedulerSubmodule)
        }

    @staticmethod
    def _get_element_name(element: DeviceElement | dict | str | None) -> str:
        """
        Get the name of an element represented as a `DeviceElement` instance,
        dictionary or string.
        """
        match element:
            case DeviceElement():
                return element.name
            case dict():
                return element["name"]
            case str():
                return element
            case _:
                raise TypeError(f"Invalid type for device element {element}")

    @abc.abstractmethod
    def generate_edge_config(self) -> dict[str, dict[str, OperationCompilationConfig]]:
        """
        Generate the device configuration for an edge.

        This method is intended to be used when this object is part of a
        device object containing multiple elements.
        """
        raise NotImplementedError
