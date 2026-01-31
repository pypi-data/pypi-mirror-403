# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2025, Qblox B.V.
from qblox_scheduler.operations.control_flow_library import LoopStrategy
from qblox_scheduler.operations.expressions import Expression


def check_unsupported_expression(*args_to_check: object, operation_name: str) -> None:
    if any(isinstance(arg, Expression) for arg in args_to_check):
        raise NotImplementedError(
            f"Using expressions in {operation_name} is not fully supported yet.\n"
            "If the expression contains a loop variable, the loop method can be called with "
            f"strategy={LoopStrategy.UNROLLED!r} to solve this error."
        )
