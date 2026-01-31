from pytest import raises

from qblox_scheduler.operations.expressions import DType
from qblox_scheduler.operations.loop_domains import LinearDomain, arange, linspace


def test_float_linspace():
    start = 1.0
    stop = 5.5
    nsteps = 10
    domain = linspace(start, stop, nsteps, dtype=DType.AMPLITUDE)
    assert isinstance(domain, LinearDomain)

    assert domain.start == start
    assert domain.stop == stop
    assert domain.num_steps == nsteps
    assert len(domain) == nsteps
    assert domain.step_size == 0.5
    assert domain[1] == 1.5
    assert list(domain.values()) == [
        1.0,
        1.5,
        2.0,
        2.5,
        3.0,
        3.5,
        4.0,
        4.5,
        5.0,
        5.5,
    ]


def test_complex_linspace():
    start = 1.0 + 2j
    stop = 5.5 + 11j
    nsteps = 10
    domain = linspace(start, stop, nsteps, dtype=DType.AMPLITUDE)
    assert isinstance(domain, LinearDomain)

    assert domain.start == start
    assert domain.stop == stop
    assert domain.num_steps == nsteps
    assert len(domain) == nsteps
    assert domain.step_size == 0.5 + 1j
    assert domain[1] == 1.5 + 3j
    assert list(domain.values()) == [
        1.0 + 2j,
        1.5 + 3j,
        2.0 + 4j,
        2.5 + 5j,
        3.0 + 6j,
        3.5 + 7j,
        4.0 + 8j,
        4.5 + 9j,
        5.0 + 10j,
        5.5 + 11j,
    ]


def test_float_arange():
    # only stop
    domain = arange(5, dtype=DType.AMPLITUDE)
    assert isinstance(domain, LinearDomain)
    assert domain.start == 0.0
    assert domain.stop == 4.0
    assert domain.num_steps == 5

    # start-stop
    domain = arange(1, 5, dtype=DType.AMPLITUDE)
    assert isinstance(domain, LinearDomain)
    assert domain.start == 1.0
    assert domain.stop == 4.0
    assert domain.num_steps == 4

    # start-stop-step
    domain = arange(1, 5, 0.5, dtype=DType.AMPLITUDE)
    assert isinstance(domain, LinearDomain)
    assert domain.start == 1.0
    assert domain.stop == 4.5
    assert domain.num_steps == 8

    # start (keyword)-stop
    domain = arange(5, start=1, dtype=DType.AMPLITUDE)  # type: ignore
    assert isinstance(domain, LinearDomain)
    assert domain.start == 1.0
    assert domain.stop == 4.0
    assert domain.num_steps == 4

    # start-stop (keyword)-step
    domain = arange(1, 0.5, stop=5, dtype=DType.AMPLITUDE)  # type: ignore
    assert isinstance(domain, LinearDomain)
    assert domain.start == 1.0
    assert domain.stop == 4.5
    assert domain.num_steps == 8

    # start
    with raises(TypeError):
        _ = arange(start=1, dtype=DType.AMPLITUDE)  # type: ignore

    # start-step
    with raises(TypeError):
        _ = arange(start=1, step=0.5, dtype=DType.AMPLITUDE)  # type: ignore

    # stop-step
    with raises(TypeError):
        _ = arange(stop=5, step=0.5, dtype=DType.AMPLITUDE)  # type: ignore
