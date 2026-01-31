import pytest

from qblox_scheduler.schemas.examples import utils


@pytest.mark.parametrize(
    "filename",
    [
        "qblox_hardware_config_transmon.json",
    ],
)
def test_load_json_example_scheme(filename: str) -> None:
    utils.load_json_example_scheme(filename)
