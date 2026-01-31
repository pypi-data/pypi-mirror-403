from typing import Union

from qblox_scheduler.operations.expressions import DType, Expression
from qblox_scheduler.operations.pulse_library import SquarePulse
from qblox_scheduler.operations.variables import Variable


def test_pulse_substitution():
    x = Variable(dtype=DType.AMPLITUDE)
    substitutions: dict[Expression, Union[Expression, int, float, complex]] = {x: 20e-9}

    pulse = SquarePulse(amp=0.7, duration=x, port="q0:f1")
    subst_pulse = pulse.substitute(substitutions)

    assert pulse.data["pulse_info"]["duration"] == x
    assert subst_pulse.data["pulse_info"]["duration"] == 20e-9
