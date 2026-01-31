# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""
Validated and serializable data structures using :mod:`pydantic`.

In this module we provide :class:`pre-configured Pydantic model <.DataStructure>` and
:mod:`custom field types <.types>` that allow serialization of typical data objects
that we frequently use in ``qblox-scheduler``, like functions and arrays.
"""

from .model import DataStructure
from .types import Graph, NDArray

__all__ = ["DataStructure", "Graph", "NDArray"]
