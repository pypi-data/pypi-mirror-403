# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2025, Qblox B.V.
"""Module containing scheduler YAML utilities."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
import ruamel.yaml as ry

if TYPE_CHECKING:
    from pydantic import BaseModel
    from qcodes.instrument import Instrument


def represent_enum(representer: ry.Representer, data: Enum) -> ry.ScalarNode:
    """Provide a value-based representation for Enum instances in YAML."""
    # An enum value can be any scalar type; if there's no matching representer, default to str.
    repr_method = representer.yaml_representers.get(type(data.value), str)
    return repr_method(representer, data.value)


def represent_ndarray(representer: ry.Representer, data: np.ndarray) -> ry.MappingNode:
    """Represent a NumPy array as a mapping, including its type and shape."""
    node = representer.represent_mapping(
        "!numpy.ndarray",
        {
            "dtype": str(data.dtype),
            "shape": data.shape,
            "data": data.tolist(),
        },
    )
    # Set flow_style for "shape" and "data", so they aren't serialized one element per line.
    for key in node.value:
        if key[0].value in ("shape", "data"):
            key[1].flow_style = True
    return node


def construct_ndarray(constructor: ry.Constructor, node: ry.MappingNode) -> np.ndarray:
    """Restore a NumPy array from a mapping with its proper type and shape."""
    if isinstance(constructor, ry.RoundTripConstructor):
        data = ry.CommentedMap()
        constructor.construct_mapping(node, maptyp=data, deep=True)
    else:
        data = constructor.construct_mapping(node, deep=True)
    return np.array(data["data"], dtype=data["dtype"]).reshape(data["shape"])


def represent_instrument(representer: ry.Representer, data: Instrument) -> ry.ScalarNode:
    """Provide a name-based representation for QCoDeS Instrument instances in YAML."""
    repr_method = representer.yaml_representers.get(str)
    return repr_method(representer, data.name)


def register_model(cls: type[BaseModel], yaml_obj: ry.YAML) -> None:
    """
    Register a Pydantic model to be serialized by `ruamel.yaml`, with a YAML tag corresponding
    to the name of the model class.

    The implementation mirrors the original :meth:`~ruamel.yaml.YAML.register_class`,
    but unlike that it doesn't use `to_yaml/from_yaml` on the target class,
    instead relying solely on `__getstate__` and `__setstate__`.
    """
    tag = "!" + cls.__name__

    def represent_model(representer: ry.Representer, data: BaseModel) -> ry.MappingNode:
        return representer.represent_yaml_object(
            tag,
            data,
            cls,
            flow_style=representer.default_flow_style,
        )

    def construct_model(constructor: ry.Constructor, node: ry.MappingNode) -> BaseModel:
        if isinstance(constructor, ry.RoundTripConstructor):
            data = ry.CommentedMap()
            constructor.construct_mapping(node, maptyp=data, deep=True)
        else:
            data = constructor.construct_mapping(node, deep=True)
        return cls.model_validate(data)

    yaml_obj.representer.add_representer(cls, represent_model)
    yaml_obj.constructor.add_constructor(tag, construct_model)


def register_legacy_instruments(yaml_obj: ry.YAML) -> None:
    """
    Register `MeasurementControl` and `InstrumentCoordinator` with the global YAML object
    to be de/serialized correctly.
    """
    from qblox_scheduler.instrument_coordinator.instrument_coordinator import InstrumentCoordinator
    from quantify_core.measurement.control import MeasurementControl

    # Support QCoDeS instruments (for `MeasurementControl` and `InstrumentCoordinator`)
    yaml_obj.representer.add_representer(MeasurementControl, represent_instrument)
    yaml_obj.representer.add_representer(InstrumentCoordinator, represent_instrument)


# The "rt" (round-trip) loader can be advantageous compared to the "safe" loader,
# particularly when working with complex, nested Python classes:
# - Comments: it retains comments present in the YAML file
# - Key Order: it preserves the order of keys in YAML mappings (dictionaries)
# - Formatting: it attempts to maintain the original indentation and whitespace
# - Anchors and Aliases: it preserves YAML anchors and aliases
# - Tags: it handles tags, including custom tags that are used to represent your custom classes
yaml = ry.YAML(typ="rt")

# Support Enum and its subclasses
yaml.representer.add_multi_representer(Enum, represent_enum)
# Support NumPy arrays
yaml.representer.add_representer(np.ndarray, represent_ndarray)
yaml.constructor.add_constructor("!numpy.ndarray", construct_ndarray)


__all__ = ["register_legacy_instruments", "register_model", "yaml"]
