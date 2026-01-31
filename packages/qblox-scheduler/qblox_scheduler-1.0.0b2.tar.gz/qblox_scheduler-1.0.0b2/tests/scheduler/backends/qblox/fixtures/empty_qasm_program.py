"""Empty QASM program fixture."""

import pytest

from qblox_scheduler.backends.qblox.instrument_compilers import QCMCompiler
from qblox_scheduler.backends.qblox.qasm_program import QASMProgram


@pytest.fixture
def empty_qasm_program_qcm():
    """Empty QASMProgram object configured for Quantum Control Module (QCM) testing."""
    """Empty QASMProgram object."""
    yield QASMProgram(
        static_hw_properties=QCMCompiler.static_hw_properties,  # type: ignore # "property" is incompatible with "StaticHardwareProperties"
    )
