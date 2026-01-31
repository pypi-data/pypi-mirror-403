# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2025, Qblox B.V.
"""Classes that represent expressions, which produce a value when compiled and executed."""

from __future__ import annotations

import operator
from abc import ABC, abstractmethod
from collections import UserDict
from typing import TYPE_CHECKING, Any, ClassVar

from qblox_scheduler.enums import StrEnum
from qblox_scheduler.helpers.collections import make_hash
from qblox_scheduler.helpers.importers import export_python_object_to_path_string

if TYPE_CHECKING:
    from collections.abc import Callable

    from qblox_scheduler.experiments.experiment import Experiment, Step
    from qblox_scheduler.operations.operation import Operation
    from qblox_scheduler.schedules.schedule import TimeableScheduleBase


class DType(StrEnum):
    """Data type of a variable or expression."""

    NUMBER = "number"
    """A number, corresponding to 1, 2, 3, etc."""

    AMPLITUDE = "amplitude"
    """
    An amplitude, corresponding to 0.1, 0.2, 0.3, etc. in dimensionless units
    ranging from -1 to 1.
    """

    TIME = "time"
    """A time, corresponding to 20e-9, 40e-9, 60e-9, etc. in seconds."""

    FREQUENCY = "frequency"
    """A frequency, corresponding to 1e9, 2e9, 3e9, etc. in Hz."""

    PHASE = "phase"
    """A phase, corresponding to e.g. 0, 30, 60, 90, etc. in degrees ranging from 0 to 360."""

    def is_timing_sensitive(self) -> bool:
        """Whether an expression of this type affects timing."""
        return self == DType.TIME


class Expression(UserDict, ABC):
    """Expression that produces a value when compiled."""

    @property
    @abstractmethod
    def dtype(self) -> DType:
        """Data type of the expression."""
        pass

    @abstractmethod
    def substitute(
        self, substitutions: dict[Expression, Expression | int | float | complex]
    ) -> Expression | int | float | complex:
        """Substitute matching parts of expression, possibly evaluating a result."""
        return self

    def reduce(self) -> Expression | int | float | complex:
        """Reduce complex ASTs if they can be simplified due to the presence of constants."""
        return self

    def __eq__(self, other: object) -> bool:
        """
        Returns the equality of two instances based on its hash.

        Parameters
        ----------
        other
            The other operation to compare to.

        Returns
        -------
        :

        """
        return hash(self) == hash(other)

    def __getstate__(self) -> dict[str, object]:
        return {
            "deserialization_type": export_python_object_to_path_string(self.__class__),
            "data": self.data,
        }

    def __setstate__(self, state: dict[str, dict]) -> None:
        self.data = state["data"]

    def __hash__(self) -> int:
        return make_hash(self.data)

    def __add__(self, rhs: Expression | complex) -> BinaryExpression:
        if isinstance(rhs, Expression) and self.dtype != rhs.dtype:
            return NotImplemented
        return BinaryExpression(self, "+", rhs)

    __radd__ = __add__

    def __sub__(self, rhs: Expression | complex) -> BinaryExpression:
        if isinstance(rhs, Expression) and self.dtype != rhs.dtype:
            return NotImplemented
        return BinaryExpression(self, "-", rhs)

    def __rsub__(self, lhs: Expression | complex) -> BinaryExpression:
        if isinstance(lhs, Expression) and self.dtype != lhs.dtype:
            return NotImplemented
        return BinaryExpression(lhs, "-", self)

    def __neg__(self) -> UnaryExpression:
        return UnaryExpression("-", self)

    def __mul__(self, rhs: Expression | complex) -> BinaryExpression:
        return BinaryExpression(self, "*", rhs)

    __rmul__ = __mul__

    def __truediv__(self, rhs: Expression | complex) -> BinaryExpression:
        return BinaryExpression(self, "/", rhs)

    def __floordiv__(self, rhs: Expression | complex) -> BinaryExpression:
        return BinaryExpression(self, "//", rhs)

    def __lshift__(self, rhs: Expression | complex) -> BinaryExpression:
        if isinstance(rhs, Expression) and self.dtype != rhs.dtype:
            return NotImplemented
        return BinaryExpression(self, "<<", rhs)

    def __rshift__(self, rhs: Expression | complex) -> BinaryExpression:
        if isinstance(rhs, Expression) and self.dtype != rhs.dtype:
            return NotImplemented
        return BinaryExpression(self, ">>", rhs)

    def __and__(self, rhs: Expression | complex) -> BinaryExpression:
        if isinstance(rhs, Expression) and self.dtype != rhs.dtype:
            return NotImplemented
        return BinaryExpression(self, "&", rhs)

    def __rand__(self, lhs: Expression | complex) -> BinaryExpression:
        if isinstance(lhs, Expression) and self.dtype != lhs.dtype:
            return NotImplemented
        return BinaryExpression(lhs, "&", self)

    def __or__(self, rhs: Expression | complex) -> BinaryExpression:  # type: ignore[reportIncompatibleMethodOverride]
        if isinstance(rhs, Expression) and self.dtype != rhs.dtype:
            return NotImplemented
        return BinaryExpression(self, "|", rhs)

    def __ror__(self, lhs: Expression | complex) -> BinaryExpression:  # type: ignore[reportIncompatibleMethodOverride]
        if isinstance(lhs, Expression) and self.dtype != lhs.dtype:
            return NotImplemented
        return BinaryExpression(lhs, "|", self)

    def __xor__(self, rhs: Expression | complex) -> BinaryExpression:
        if isinstance(rhs, Expression) and self.dtype != rhs.dtype:
            return NotImplemented
        return BinaryExpression(self, "^", rhs)

    def __rxor__(self, lhs: Expression | complex) -> BinaryExpression:
        if isinstance(lhs, Expression) and self.dtype != lhs.dtype:
            return NotImplemented
        return BinaryExpression(lhs, "^", self)

    def __invert__(self) -> UnaryExpression:
        return UnaryExpression("~", self)

    @abstractmethod
    def __contains__(self, item: object) -> bool:
        pass


class UnaryExpression(Expression):
    """
    An expression with one operand and one operator.

    Parameters
    ----------
    operator
        The operator that acts on the operand.
    operand
        The expression or variable that is acted on.

    """

    EVALUATORS: ClassVar[dict[str, Callable]] = {
        "+": operator.pos,
        "-": operator.neg,
        "~": operator.invert,
    }

    def __init__(self, operator: str, operand: Expression) -> None:
        super().__init__(name=f"UnaryOperator{operator}")
        self.data["expression_info"] = {"operator": operator, "operand": operand}
        self._dtype = operand.dtype

    @property
    def operator(self) -> str:
        """The operator that acts on the operand."""
        return self.data["expression_info"]["operator"]

    @property
    def operand(self) -> Expression:
        """The expression or variable that is acted on."""
        return self.data["expression_info"]["operand"]

    @property
    def dtype(self) -> DType:
        """Data type of this expression."""
        return self._dtype

    def _update(self) -> None:
        self._dtype = self.operand.dtype

    def substitute(
        self, substitutions: dict[Expression, Expression | int | float | complex]
    ) -> Expression | int | float | complex:
        """Substitute matching operand, possibly evaluating a result."""
        if isinstance(self.operand, Expression):
            operand_sub = self.operand.substitute(substitutions)
            # Only return new instance if anything changed
            if operand_sub is not self.operand:
                # Only return expression if something is still not known.
                if isinstance(operand_sub, Expression):
                    return self.__class__(operator=self.operator, operand=operand_sub)
                else:
                    evaluator = self.EVALUATORS[self.operator]
                    return evaluator(operand_sub)
        return self

    def reduce(self) -> Expression | int | float | complex:
        """
        Reduce complex ASTs if they can be simplified due to the presence of constants.

        Currently only handles a few cases (``a`` is a constant value in these examples):

        - ``-(-expr) -> expr``
        - ``+(expr * a) -> expr * a`` (same for ``/``)
        - ``-(expr * a) -> expr * (-a)`` (same for ``/``)

        Returns
        -------
        Expression | int | float | complex
            The simplified expression.

        """
        if isinstance(self.operand, Expression):
            operand_sub = self.operand.reduce()
        else:
            operand_sub = self.operand

        if not isinstance(operand_sub, Expression):
            evaluator = self.EVALUATORS[self.operator]
            # Early return: we have only constants in this expression
            return evaluator(operand_sub)

        if operand_sub is not self.operand:
            expr_sub = self.__class__(
                operator=self.operator,
                operand=operand_sub,
            )
        else:
            expr_sub = self

        match expr_sub:
            case UnaryExpression(
                operator=("+" | "-") as o,
                operand=UnaryExpression(operator=("+" | "-") as inner_o, operand=Expression() as e),
            ):
                ev1 = self.EVALUATORS[o]
                ev2 = self.EVALUATORS[inner_o]
                res = ev1(1) * ev2(1)
                if res == 1:
                    return e
                else:
                    return BinaryExpression(e, "*", -1)
            case UnaryExpression(
                operator=("+" | "-") as o,
                operand=BinaryExpression(
                    lhs=Expression() as e,
                    operator=("*" | "/") as inner_o,
                    rhs=(float() | int()) as a,
                ),
            ):
                evaluator = self.EVALUATORS[self.operator]
                return BinaryExpression(e, inner_o, evaluator(a)).reduce()

        return expr_sub

    def __repr__(self) -> str:
        return f"({self.operator}{self.operand})"

    def __contains__(self, item: object) -> bool:
        return (item == self.operand) or (
            isinstance(self.operand, Expression) and item in self.operand
        )


class BinaryExpression(Expression):
    """
    An expression with two operands and one operator.

    Parameters
    ----------
    lhs
        The left-hand side of the expression.
    operator
        The operator that acts on the operands.
    rhs
        The right-hand side of the expression.

    """

    EVALUATORS: ClassVar[dict[str, Callable]] = {
        "&": operator.and_,
        "|": operator.or_,
        "^": operator.xor,
        "<<": operator.lshift,
        ">>": operator.rshift,
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
        "//": operator.floordiv,
    }

    def __init__(self, lhs: Expression | complex, operator: str, rhs: Expression | complex) -> None:
        super().__init__(name=f"BinaryOperator{operator}")
        self.data["expression_info"] = {"lhs": lhs, "operator": operator, "rhs": rhs}

        if isinstance(lhs, Expression):
            self._dtype = lhs.dtype
        elif isinstance(rhs, Expression):
            self._dtype = rhs.dtype
        else:
            raise ValueError(
                "Cannot create instance of class BinaryExpression with neither rhs nor lhs of "
                f"class Expression.\n{rhs=}\n{rhs=}"
            )

    @property
    def lhs(self) -> Expression:
        """The left-hand side of the expression."""
        return self.data["expression_info"]["lhs"]

    @property
    def operator(self) -> str:
        """The operator that acts on the operands."""
        return self.data["expression_info"]["operator"]

    @property
    def rhs(self) -> Expression | complex:
        """The right-hand side of the expression."""
        return self.data["expression_info"]["rhs"]

    @property
    def dtype(self) -> DType:
        """Data type of this expression."""
        return self._dtype

    def _update(self) -> None:
        if isinstance(self.lhs, Expression):
            self._dtype = self.lhs.dtype
        elif isinstance(self.rhs, Expression):
            self._dtype = self.rhs.dtype
        else:
            raise ValueError(
                "Cannot create instance of class BinaryExpression with neither rhs nor lhs of "
                f"class Expression.\n{self.lhs=}\n{self.rhs=}"
            )

    def substitute(
        self, substitutions: dict[Expression, Expression | int | float | complex]
    ) -> Expression | int | float | complex:
        """Substitute matching operands, possibly evaluating a result."""
        if isinstance(self.lhs, Expression):
            lhs_sub = self.lhs.substitute(substitutions)
        else:
            lhs_sub = self.lhs
        if isinstance(self.rhs, Expression):
            rhs_sub = self.rhs.substitute(substitutions)
        else:
            rhs_sub = self.rhs
        # Only return new instance if anything changed
        if lhs_sub is not self.lhs or rhs_sub is not self.rhs:
            # Only return expression if something is still not known.
            if isinstance(lhs_sub, Expression) or isinstance(rhs_sub, Expression):
                return self.__class__(
                    lhs=lhs_sub,
                    operator=self.operator,
                    rhs=rhs_sub,
                )
            else:
                evaluator = self.EVALUATORS[self.operator]
                return evaluator(lhs_sub, rhs_sub)
        return self

    def reduce(self) -> Expression | int | float | complex:  # noqa: PLR0911  (too many returns)
        """
        Reduce complex ASTs if they can be simplified due to the presence of constants.

        Currently only handles a few cases (``a`` and ``b`` are constant values in these examples):

        - ``expr * 1 -> expr`` (same for ``/`` and ``//``)
        - ``expr + 0 -> expr`` (same for other applicable operators)
        - ``(expr * a) * b -> expr * (a * b)``
        - ``(expr * a) / b -> expr * (a / b)``
        - ``(expr / a) * b -> expr * (b / a)``
        - ``(expr / a) / b -> expr / (a * b)``
        - ``(-expr) * b -> expr * (-b)`` (same for ``/``)

        Returns
        -------
        Expression | int | float | complex
            The simplified expression.

        """
        lhs_sub = self.lhs.reduce() if isinstance(self.lhs, Expression) else self.lhs
        rhs_sub = self.rhs.reduce() if isinstance(self.rhs, Expression) else self.rhs

        if not (isinstance(lhs_sub, Expression) or isinstance(rhs_sub, Expression)):
            evaluator = self.EVALUATORS[self.operator]
            # Early return: we have only constants in this expression
            return evaluator(lhs_sub, rhs_sub)

        if lhs_sub is not self.lhs or rhs_sub is not self.rhs:
            expr_sub = self.__class__(
                lhs=lhs_sub,
                operator=self.operator,
                rhs=rhs_sub,
            )
        else:
            expr_sub = self

        match expr_sub:
            case BinaryExpression(lhs=Expression() as e, operator="*", rhs=0):
                return 0
            case BinaryExpression(lhs=Expression() as e, operator="*" | "/" | "//", rhs=1):
                return e
            case BinaryExpression(
                lhs=Expression() as e, operator="|" | "^" | "<<" | ">>" | "+" | "-", rhs=0
            ):
                return e
            case BinaryExpression(
                lhs=BinaryExpression(
                    lhs=Expression() as e, operator="*", rhs=(int() | float()) as a
                ),
                operator=("*" | "/") as o,
                rhs=(int() | float()) as b,
            ):
                evaluator = self.EVALUATORS[o]
                return BinaryExpression(e, "*", evaluator(a, b)).reduce()
            case BinaryExpression(
                lhs=BinaryExpression(
                    lhs=Expression() as e, operator="/", rhs=(int() | float()) as a
                ),
                operator="*",
                rhs=(int() | float()) as b,
            ):
                return BinaryExpression(e, "*", b / a).reduce()
            case BinaryExpression(
                lhs=BinaryExpression(
                    lhs=Expression() as e, operator="/", rhs=(int() | float()) as a
                ),
                operator="/",
                rhs=(int() | float()) as b,
            ):
                return BinaryExpression(e, "/", a * b).reduce()
            case BinaryExpression(
                lhs=UnaryExpression(operator=("+" | "-") as inner_o, operand=operand),
                operator=("*" | "/") as o,
                rhs=(int() | float()) as b,
            ):
                evaluator = self.EVALUATORS[inner_o]
                return BinaryExpression(operand, o, evaluator(0, b)).reduce()

        return expr_sub

    def __repr__(self) -> str:
        return f"({self.lhs} {self.operator} {self.rhs})"

    def __contains__(self, item: object) -> bool:
        return (
            item in (self.lhs, self.rhs)
            or (isinstance(self.lhs, Expression) and item in self.lhs)
            or (isinstance(self.rhs, Expression) and item in self.rhs)
        )


if TYPE_CHECKING:
    ContainsExpressionType = (
        Expression | Operation | TimeableScheduleBase | Step | Experiment | dict | UserDict | list
    )


def substitute_value_in_arbitrary_container(
    val: ContainsExpressionType, substitutions: dict[Expression, Expression | int | float | complex]
) -> tuple[Any, bool]:
    """Make the defined substitutions in the container type `val`."""
    from qblox_scheduler.experiments.experiment import Experiment, Step
    from qblox_scheduler.operations.operation import Operation
    from qblox_scheduler.schedules.schedule import TimeableScheduleBase

    changed = False
    if isinstance(val, (Expression, Operation, TimeableScheduleBase, Step, Experiment)):
        sub_val = val.substitute(substitutions)
        if sub_val is not val:
            changed = True
        return sub_val, changed
    elif isinstance(val, (dict, UserDict)):
        dict_changed = False
        sub_dict = {}
        for k, v in val.items():
            sub_dict[k], changed = substitute_value_in_arbitrary_container(v, substitutions)
            if sub_dict[k] is not v:
                dict_changed = True
        if dict_changed:
            changed = True
            return sub_dict, changed
        else:
            return val, changed
    elif isinstance(val, (list, tuple)):
        list_changed = False
        sub_list = []
        for x in val:
            sub_x, changed = substitute_value_in_arbitrary_container(x, substitutions)
            sub_list.append(sub_x)
            if sub_x is not x:
                list_changed = True
        if list_changed:
            changed = True
            return sub_list, changed
        else:
            return val, changed
    else:
        return val, changed
