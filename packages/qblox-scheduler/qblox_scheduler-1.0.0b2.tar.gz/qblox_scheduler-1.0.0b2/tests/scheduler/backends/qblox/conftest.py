# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch

import pytest

from qblox_scheduler.backends.qblox.instrument_compilers import (
    QCMCompiler,
    QCMRFCompiler,
    QRMCompiler,
    QRMRFCompiler,
    QTMCompiler,
)
from qblox_scheduler.backends.qblox.qasm_program import QASMProgram
from qblox_scheduler.backends.qblox.register_manager import RegisterManager


@pytest.fixture()
def empty_qasm_program_qcm():
    """Empty QASMProgram object."""
    yield QASMProgram(
        static_hw_properties=QCMCompiler.static_hw_properties,
        register_manager=RegisterManager(),
        align_fields=True,
    )


@pytest.fixture()
def empty_qasm_program_qrm():
    yield QASMProgram(
        static_hw_properties=QRMCompiler.static_hw_properties,
        register_manager=RegisterManager(),
        align_fields=True,
    )


@pytest.fixture()
def empty_qasm_program_qrm_rf():
    yield QASMProgram(
        static_hw_properties=QRMRFCompiler.static_hw_properties,
        register_manager=RegisterManager(),
        align_fields=True,
    )


@pytest.fixture()
def empty_qasm_program_qcm_rf():
    yield QASMProgram(
        static_hw_properties=QCMRFCompiler.static_hw_properties,
        register_manager=RegisterManager(),
        align_fields=True,
    )


@pytest.fixture()
def empty_qasm_program_qtm():
    yield QASMProgram(
        static_hw_properties=QTMCompiler.static_hw_properties,
        register_manager=RegisterManager(),
        align_fields=True,
    )
