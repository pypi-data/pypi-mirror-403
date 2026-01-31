# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2025, Qblox B.V.
"""Domains to loop over with ``Schedule.loop``."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar, Union, overload

from pydantic import field_validator

from qblox_scheduler.helpers.collections import make_hash
from qblox_scheduler.operations.expressions import DType
from qblox_scheduler.structure.model import DataStructure

if TYPE_CHECKING:
    from collections.abc import Iterator


T = TypeVar("T")


class Domain(DataStructure, ABC, Generic[T]):
    """An object representing a range of values to loop over."""

    dtype: DType
    """Data type of the linear domain."""

    def __hash__(self) -> int:
        return make_hash(tuple(Domain.model_fields))

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def __getitem__(self, index: int) -> T: ...

    @abstractmethod
    def values(self) -> Iterator[T]:
        """Return iterator over all values in this domain."""

    @property
    @abstractmethod
    def num_steps(self) -> int:
        """Return the number of steps in this domain."""


class LinearDomain(Domain[Union[complex, float]]):
    """
    Linear range of values to loop over, specified with a start value, an inclusive stop value and
    the number of linearly spaced points to generate.
    """

    start: complex | float
    """The starting value of the sequence."""
    stop: complex | float
    """The end value of the sequence."""
    num: int
    """Number of samples to generate. Must be non-negative."""

    def __len__(self) -> int:
        return self.num

    def __getitem__(self, index: int) -> complex | float:
        return self.start + index * self.step_size

    def values(self) -> Iterator[complex | float]:
        """Return iterator over all values in this domain."""
        return iter(self[idx] for idx in range(len(self)))

    @field_validator("num", mode="before")
    @classmethod
    def _num_is_strictly_positive(cls, num: int) -> int:
        if num < 1:
            raise ValueError("A domain must have at least one point.")
        return num

    @property
    def num_steps(self) -> int:
        """The number of steps in this domain."""
        return self.num

    @property
    def step_size(self) -> complex | float:
        """The step size of the range of values."""
        return (
            self.stop - self.start if self.num == 1 else (self.stop - self.start) / (self.num - 1)
        )


# These functions exists to have more flexibility with positional/keyword arguments,
# since pydantic models only accept keyword arguments.


def linspace(start: complex | float, stop: complex | float, num: int, dtype: DType) -> LinearDomain:
    """
    Linear range of values to loop over, specified with a start value, an inclusive stop value and
    the number of linearly spaced points to generate.

    Parameters
    ----------
    start
        The starting value of the sequence.
    stop
        The end value of the sequence.
    num
        Number of samples to generate. Must be non-negative.
    dtype
        Data type of the linear domain.

    """
    return LinearDomain(start=start, stop=stop, num=num, dtype=dtype)


@overload
def arange(stop: float, dtype: DType) -> LinearDomain: ...
@overload
def arange(start: float, stop: float, dtype: DType) -> LinearDomain: ...
@overload
def arange(start: float, stop: float, step: float, dtype: DType) -> LinearDomain: ...
def arange(*_args: Any, **_kwargs: Any) -> LinearDomain:
    """
    Linear range of values to loop over, specified with a start value, an exclusive stop value and a
    step size.

    Parameters
    ----------
    start
        Start of interval. The interval includes this value.
    stop
        End of interval. The interval does not include this value, except in some cases where step
        is not an integer and floating point round-off affects the length of out.
    step
        Spacing between values. For any output out, this is the distance between two adjacent
        values, out[i+1] - out[i].
    dtype
        Data type of the linear domain.

    """
    args_iter = iter(_args)
    num_args = len(_args) + len(_kwargs)

    # Argument parsing is a little bit weird because the `range` API is a bit weird.
    # We want to preserve being able to pass things as a keyword argument, as well as
    # mixing and matching positionals. Furthermore, we have two required arguments
    # `stop` and `dtype`, in different positions in the nominal order.
    if "start" in _kwargs:
        start = _kwargs.pop("start")
    elif num_args > 2:
        try:
            start = next(args_iter)
        except StopIteration:
            raise TypeError("missing argument: start") from None
    else:
        start = 0.0
    if "stop" in _kwargs:
        stop = _kwargs.pop("stop")
    else:
        try:
            stop = next(args_iter)
        except StopIteration:
            raise TypeError("missing argument: stop") from None
    if "step" in _kwargs:
        step = _kwargs.pop("step")
    elif num_args > 3:
        try:
            step = next(args_iter)
        except StopIteration:
            raise TypeError("missing argument: step") from None
    else:
        step = 1.0
    if "dtype" in _kwargs:
        dtype = _kwargs.pop("dtype")
    else:
        try:
            dtype = next(args_iter)
        except StopIteration:
            raise TypeError("missing argument: dtype") from None

    arg_remainder = list(args_iter)
    if arg_remainder:
        a = ", ".join(repr(x) for x in arg_remainder)
        raise TypeError(f"unexpected arguments: {a}")
    if _kwargs:
        kws = ", ".join(_kwargs)
        raise TypeError(f"unexpected keyword arguments: {kws}")

    num = math.ceil((stop - start) / step)
    return LinearDomain(start=start, stop=start + (num - 1) * step, num=num, dtype=dtype)
