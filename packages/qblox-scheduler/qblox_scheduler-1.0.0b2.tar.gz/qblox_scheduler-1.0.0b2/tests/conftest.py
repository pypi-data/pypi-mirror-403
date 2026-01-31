from tests.fixtures.cluster import *
from tests.fixtures.generic import *
from tests.fixtures.mock_setup import *
from tests.fixtures.schedule import *
from tests.fixtures.static import *
from tests.scheduler.backends.qblox.fixtures.assembly import *
from tests.scheduler.backends.qblox.fixtures.hardware_config import *
from tests.scheduler.backends.qblox.fixtures.mock_api import *


def pytest_addoption(parser):
    parser.addoption(
        "--skip_qblox_driver_version_check",
        action="store_true",
        default=False,
        help="Skip the Qblox driver version check",
    )


def pytest_configure(config):
    if config.getoption("skip_qblox_driver_version_check"):
        from qblox_scheduler.backends.qblox import driver_version_check

        driver_version_check.raise_on_version_mismatch = False
