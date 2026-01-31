# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""
Types that support validation in Pydantic.

Pydantic recognizes magic method ``__get_validators__`` to receive additional
validators, that can be used, i.e., for custom serialization and deserialization.
We implement several custom types here to tune behavior of our models.

See `Pydantic documentation`_ for more information about implementing new types.

.. _Pydantic documentation: https://docs.pydantic.dev/latest/usage/types/custom/
"""

from __future__ import annotations

import base64
import math
from typing import TYPE_CHECKING, Annotated, Any, TypedDict

import networkx as nx
import numpy as np
from annotated_types import Ge
from pydantic import AfterValidator, AllowInfNan, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic_core import core_schema

if TYPE_CHECKING:
    from collections.abc import Callable

    from pydantic.json_schema import JsonSchemaValue


def validate_non_negative_or_nan(value: float) -> float:
    """Validator that allows NaN or numbers greater than or equal to 0."""
    if not math.isnan(value) and value < 0:
        raise ValueError("input should be non-negative or NaN.")
    return value


Amplitude = Annotated[float, AllowInfNan(True)]
"""Type alias for a float that can be NaN."""
Delay = Annotated[float, AllowInfNan(False)]
"""Type alias for a float that can't be NaN."""
Duration = Annotated[float, Ge(0)]
"""Type alias for a float that must be >= 0 and not NaN."""
Frequency = Annotated[float, AllowInfNan(True), AfterValidator(validate_non_negative_or_nan)]
"""Type alias for a float that must be >= 0 but can be NaN."""


class _SerializedNDArray(TypedDict):
    data: str
    shape: tuple[int, ...]
    dtype: str


class _NDArrayPydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,  # noqa: ANN401
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        """
        Pydantic-compatible version of :class:`numpy.ndarray`.

        Serialization is implemented using custom methods :meth:`.ndarray_to_dict` and
        :meth:`.validate_from_any`. Data array is encoded in Base64.
        """
        return core_schema.json_or_python_schema(
            json_schema=core_schema.chain_schema(
                [
                    core_schema.dict_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate_from_any),
                ]
            ),
            python_schema=core_schema.union_schema(
                [
                    # check if it's an instance first before doing any further work
                    core_schema.is_instance_schema(np.ndarray),
                    core_schema.no_info_plain_validator_function(cls.validate_from_any),
                ],
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls.ndarray_to_dict,
                when_used="json",
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `dict`
        return handler(core_schema.dict_schema())

    @staticmethod
    def ndarray_to_dict(v: np.ndarray) -> _SerializedNDArray:
        """Convert the given array to JSON-compatible dictionary."""
        return {
            "data": base64.b64encode(v.tobytes()).decode("ascii"),
            "shape": v.shape,
            "dtype": str(v.dtype),
        }

    @staticmethod
    def validate_from_any(v: _SerializedNDArray | list[Any] | np.ndarray) -> np.ndarray:
        match v:
            case dict():
                return np.frombuffer(base64.b64decode(v["data"]), dtype=v["dtype"]).reshape(
                    v["shape"]
                )
            case list():
                return np.array(v)
            case np.ndarray():
                return v
            case _:
                raise TypeError(f"Unsupported NumPy array: {v}")


# We now create an `Annotated` wrapper that we'll use as the annotation for fields.
NDArray = Annotated[np.ndarray, _NDArrayPydanticAnnotation]


class Graph(nx.Graph):
    """Pydantic-compatible version of :class:`networkx.Graph`."""

    # Avoid showing inherited init docstring (which leads to cross-reference issues)
    def __init__(self, incoming_graph_data=None, **attr) -> None:  # noqa: ANN001
        """Create a new graph instance."""
        super().__init__(incoming_graph_data, **attr)

    @classmethod
    def __get_pydantic_core_schema__(
        cls: type[Graph],
        _source_type: Any,  # noqa: ANN401
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda g: nx.node_link_data(g, edges="links"), when_used="always"
            ),
        )

    @classmethod
    def validate(cls: type[Graph], v: Any) -> Graph:  # noqa: ANN401
        """Validate the data and cast from all known representations."""
        if isinstance(v, dict):
            return cls(nx.node_link_graph(v, edges="links"))
        return cls(v)


__all__ = [
    "Amplitude",
    "Delay",
    "Duration",
    "Frequency",
    "Graph",
    "NDArray",
]
