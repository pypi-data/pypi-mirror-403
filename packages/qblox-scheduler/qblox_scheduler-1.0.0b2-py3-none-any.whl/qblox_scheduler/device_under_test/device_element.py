# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""The module contains definitions for device elements."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Annotated, Any, ClassVar
from typing_extensions import Self

from pydantic import AfterValidator, Field, ModelWrapValidatorHandler, model_validator

from qblox_scheduler.structure.model import SchedulerBaseModel, is_identifier

if TYPE_CHECKING:
    from qblox_scheduler.backends.graph_compilation import DeviceCompilationConfig


def is_identifier_without_underscore(value: str) -> str:
    """Pydantic validator for names that are valid identifiers but without underscore."""
    value = is_identifier(value)
    if "_" in value:
        raise ValueError(f"{value} may not contain underscores")
    return value


class DeviceElement(abc.ABC, SchedulerBaseModel):
    """
    Create a device element for managing parameters.

    The :class:`~DeviceElement` is responsible for compiling operations applied to that
    specific device element from the quantum-circuit to the quantum-device layer.
    """

    __model_registry__: ClassVar[dict[str, type[DeviceElement]]] = {}

    element_type: str
    name: Annotated[str, AfterValidator(is_identifier_without_underscore)] = Field(kw_only=False)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:  # noqa: ANN401
        """Store new subclasses of :class:`~DeviceElement` into a class-level registry."""
        super().__pydantic_init_subclass__(**kwargs)
        DeviceElement.__model_registry__[cls.__name__] = cls

    def __getstate__(self) -> dict[str, Any]:
        """Get the state of :class:`~DeviceElement` (used for YAML serialization)."""
        return self.model_dump(exclude={"element_type"})

    @model_validator(mode="before")
    @classmethod
    def include_submodule_names(cls, data: Any) -> Any:  # noqa: ANN401
        """
        Fill in the ``name`` attribute of :class:`~DeviceElement` submodules when missing
        (used for YAML deserialization, they are omitted at serialization).
        """
        if isinstance(data, dict):
            for submodule_name, submodule_data in data.items():
                if submodule_name in ("name", "element_type"):
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
        When deserializing a dict representation of a concrete :class:`~DeviceElement`,
        infer the matching class by looking its `element_type` into the model registry
        and return a validated instance of the concrete device element.
        """
        if cls is DeviceElement and isinstance(data, dict):
            element_type = data.get("element_type")
            if element_type in cls.__model_registry__:
                return cls.__model_registry__[element_type].model_validate(data)  # type: ignore[reportReturnType]
            else:
                raise ValueError(f"unknown element type '{element_type}'")

        return handler(data)

    @abc.abstractmethod
    def generate_device_config(self) -> DeviceCompilationConfig:
        """Generate the device configuration."""
        raise NotImplementedError
