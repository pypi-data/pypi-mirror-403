from copy import deepcopy
from typing import Union

import pytest

from qblox_scheduler.backends.types.qblox import OpInfo
from qblox_scheduler.operations import SquarePulse
from qblox_scheduler.operations.expressions import (
    BinaryExpression,
    DType,
    Expression,
    UnaryExpression,
)
from qblox_scheduler.operations.variables import Variable


def test_unary_expression():
    x = Variable(dtype=DType.AMPLITUDE)
    expression = ~x
    assert isinstance(expression, UnaryExpression)
    assert expression.operator == "~"
    assert expression.operand is x


def test_binary_expression():
    x = Variable(dtype=DType.AMPLITUDE)
    expression = x + 0.5
    assert isinstance(expression, BinaryExpression)
    assert expression.operator == "+"
    assert expression.lhs is x
    assert expression.rhs == 0.5

    expression = 0.5 + x
    assert expression.lhs is x
    assert expression.rhs == 0.5

    y = Variable(dtype=DType.AMPLITUDE)
    expression = x + y
    assert isinstance(expression, BinaryExpression)
    assert expression.operator == "+"
    assert expression.lhs is x
    assert expression.rhs is y

    expression = x * y
    assert expression.operator == "*"

    expression = x / y
    assert expression.operator == "/"

    expression = x // y
    assert expression.operator == "//"


def test_operator_precedence():
    a = Variable(dtype=DType.NUMBER)
    b = Variable(dtype=DType.NUMBER)
    c = Variable(dtype=DType.NUMBER)
    d = Variable(dtype=DType.NUMBER)
    e = Variable(dtype=DType.NUMBER)
    expression = a | (b & (c << (d + (~e))))
    assert isinstance(expression, BinaryExpression)
    assert expression.operator == "|"
    assert expression.lhs is a
    assert isinstance(expression.rhs, BinaryExpression)
    assert expression.rhs.operator == "&"
    assert expression.rhs.lhs is b
    assert isinstance(expression.rhs.rhs, BinaryExpression)
    assert expression.rhs.rhs.operator == "<<"
    assert expression.rhs.rhs.lhs is c
    assert isinstance(expression.rhs.rhs.rhs, BinaryExpression)
    assert expression.rhs.rhs.rhs.operator == "+"
    assert expression.rhs.rhs.rhs.lhs is d
    assert isinstance(expression.rhs.rhs.rhs.rhs, UnaryExpression)
    assert expression.rhs.rhs.rhs.rhs.operator == "~"
    assert expression.rhs.rhs.rhs.rhs.operand is e


def test_operator_precedence_parentheses():
    a = Variable(dtype=DType.NUMBER)
    b = Variable(dtype=DType.NUMBER)
    c = Variable(dtype=DType.NUMBER)
    d = Variable(dtype=DType.NUMBER)
    e = Variable(dtype=DType.NUMBER)
    expression = ~((((a | b) & c) << d) + e)
    assert isinstance(expression, UnaryExpression)
    assert expression.operator == "~"
    assert isinstance(expression.operand, BinaryExpression)
    assert expression.operand.operator == "+"
    assert isinstance(expression.operand.lhs, BinaryExpression)
    assert expression.operand.lhs.operator == "<<"
    assert expression.operand.rhs is e
    assert isinstance(expression.operand.lhs.lhs, BinaryExpression)
    assert expression.operand.lhs.lhs.operator == "&"
    assert expression.operand.lhs.rhs is d
    assert isinstance(expression.operand.lhs.lhs.lhs, BinaryExpression)
    assert expression.operand.lhs.lhs.lhs.operator == "|"
    assert expression.operand.lhs.lhs.rhs is c
    assert expression.operand.lhs.lhs.lhs.lhs is a
    assert expression.operand.lhs.lhs.lhs.rhs is b


def test_incompatible_types():
    x = Variable(dtype=DType.AMPLITUDE)
    y = Variable(dtype=DType.FREQUENCY)
    with pytest.raises(TypeError):
        _ = x + y


def test_correct_substitution():
    x = Variable(dtype=DType.AMPLITUDE)
    substitutions: dict[Expression, Union[Expression, int, float, complex]] = {x: 5}

    assert x.substitute(substitutions) == 5

    un_expression = -x
    assert un_expression.substitute(substitutions) == -5

    bin_expression = x + 0.5
    assert bin_expression.substitute(substitutions) == 5.5


def test_substitution_does_not_modify_original_operation():
    x = Variable(dtype=DType.AMPLITUDE)
    substitutions: dict[Expression, Union[Expression, int, float, complex]] = {x: 5}

    op = SquarePulse(amp=x, duration=100e-9, port="port", clock="clock")
    copy_op = deepcopy(op)
    assert op.substitute(substitutions) == SquarePulse(
        amp=5, duration=100e-9, port="port", clock="clock"
    )
    assert op == copy_op

    op = SquarePulse(amp=-x, duration=100e-9, port="port", clock="clock")
    copy_op = deepcopy(op)
    assert op.substitute(substitutions) == SquarePulse(
        amp=-5, duration=100e-9, port="port", clock="clock"
    )
    assert op == copy_op

    op = SquarePulse(amp=x + 0.5, duration=100e-9, port="port", clock="clock")
    copy_op = deepcopy(op)
    assert op.substitute(substitutions) == SquarePulse(
        amp=5.5, duration=100e-9, port="port", clock="clock"
    )
    assert op == copy_op


def test_substitution_does_not_modify_original_op_info():
    x = Variable(dtype=DType.AMPLITUDE)
    substitutions: dict[Expression, Union[Expression, int, float, complex]] = {x: 5}

    op = OpInfo("name", {"foo": x}, 0.0)
    copy_op = deepcopy(op)
    assert op.substitute(substitutions) == OpInfo("name", {"foo": 5}, 0.0)
    assert op == copy_op

    op = OpInfo("name", {"foo": -x}, 0.0)
    copy_op = deepcopy(op)
    assert op.substitute(substitutions) == OpInfo("name", {"foo": -5}, 0.0)
    assert op == copy_op

    op = OpInfo("name", {"foo": x + 0.5}, 0.0)
    copy_op = deepcopy(op)
    assert op.substitute(substitutions) == OpInfo("name", {"foo": 5.5}, 0.0)
    assert op == copy_op


def test_noop_substitution():
    x = Variable(dtype=DType.AMPLITUDE)
    y = Variable(dtype=DType.AMPLITUDE)
    substitutions: dict[Expression, Union[Expression, int, float, complex]] = {y: 5}

    assert x.substitute({}) is x
    assert x.substitute(substitutions) is x

    un_expression = -x
    assert un_expression.substitute(substitutions) is un_expression

    bin_expression = x + 0.5
    assert bin_expression.substitute(substitutions) is bin_expression


def test_algebraic_reduction():
    x = Variable(dtype=DType.AMPLITUDE)
    assert (x * 0).reduce() == 0
    assert (x + 0).reduce() == x
    assert (x - 0).reduce() == x
    assert (x * 1).reduce() == x
    assert (-(-x)).reduce() == x  # noqa: B002
    assert (-(x * 2)).reduce() == x * -2
    assert (x * 2 * 3).reduce() == x * 6
    assert (2 * x * 3).reduce() == x * 6
    assert (4 * x / 2).reduce() == x * 2
    assert (x / 4 / 2 * 2).reduce() == x * 0.25
    assert (4 * -x / 2).reduce() == x * -2
    assert (2 + 2 * (x * 1) * 0 - 2).reduce() == 0
