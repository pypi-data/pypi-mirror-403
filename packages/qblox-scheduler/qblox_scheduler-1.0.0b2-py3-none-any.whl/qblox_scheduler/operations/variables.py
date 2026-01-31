# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2025, Qblox B.V.

"""
Variable class and related operations for creating a variable, and dropping a variable
when it goes out of scope.
"""

from __future__ import annotations

import uuid

from qblox_scheduler.operations.expressions import DType, Expression


class Variable(Expression):
    """A variable, representing a location in memory."""

    def __init__(self, dtype: DType) -> None:
        super().__init__(name="Variable")
        self.data["expression_info"] = {"variable": uuid.uuid4(), "dtype": dtype}

    def substitute(
        self, substitutions: dict[Expression, Expression | int | float | complex]
    ) -> Expression | int | float | complex:
        """Substitute matching variable."""
        for expr, sub in substitutions.items():
            if isinstance(expr, Variable) and self.id_ == expr.id_:
                result = sub
                if isinstance(result, Expression):
                    result = result.substitute(substitutions)
                return result
        return self

    @property
    def dtype(self) -> DType:
        """Data type of this variable."""
        return self["expression_info"]["dtype"]

    def _update(self) -> None:
        self._dtype = self.data["expression_info"]["dtype"]

    @property
    def id_(self) -> uuid.UUID:
        """The unique ID of this variable."""
        return self.data["expression_info"]["variable"]

    def __hash__(self) -> int:
        return hash(self.id_)

    def __repr__(self) -> str:
        return f"Var{self.id_.hex}"

    def __contains__(self, item: object) -> bool:
        return False
