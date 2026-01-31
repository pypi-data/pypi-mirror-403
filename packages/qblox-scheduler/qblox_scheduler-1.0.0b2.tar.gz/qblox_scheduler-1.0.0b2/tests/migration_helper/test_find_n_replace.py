from collections.abc import Generator
from pathlib import Path
from textwrap import dedent

import pytest

from migration_helper.utils import find_and_replace_in_file

# Each test will populate this dictionary before running.
_MOCK_READ_CONTENTS = {}
# A dictionary to capture the content that would be "written"
_MOCK_WRITTEN_CONTENTS = {}


@pytest.fixture
def mock_open_fixture(monkeypatch) -> Generator[dict[Path, str], None, None]:
    """
    A pytest fixture to mock the built-in 'open' function for testing.
    This fixture is used to control the file I/O for the mock-based tests.
    """

    def mock_open(file_path, mode="r"):
        class MockFile:
            def __init__(self, path, mode):
                self.path = path
                self.mode = mode
                self._content_buffer = []

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

            def read(self):
                if self.mode == "r":
                    return _MOCK_READ_CONTENTS[self.path]
                return ""

            def write(self, content):
                if self.mode in ("w", "wb"):
                    self._content_buffer.append(content)
                    _MOCK_WRITTEN_CONTENTS[self.path] = "".join(self._content_buffer)

        return MockFile(file_path, mode)

    # Apply the mock to the built-in `open` function.
    monkeypatch.setattr("builtins.open", mock_open)

    # Yield the dictionary that captures written content for assertions.
    yield _MOCK_WRITTEN_CONTENTS

    # Clean up the dictionaries after the test runs
    _MOCK_READ_CONTENTS.clear()
    _MOCK_WRITTEN_CONTENTS.clear()


def test_all_files_migrated_with_mocks(mock_open_fixture) -> None:
    """
    Test case where all files contain the string and should be migrated, using mocks.
    The mock is provided by the `mock_open_fixture`.
    """
    # Populate the dictionary for this specific test
    _MOCK_READ_CONTENTS.update(
        {
            Path("config1.json"): dedent("""
                {
                    "deserialization_type": "quantify_scheduler.device_under_test.quantum_device.QuantumDevice",
                    "data": {
                        "name": "device_2q"
                    }
                }
            """).strip(),  # noqa: E501
            Path(
                "config2.json"
            ): '{"config_type": "quantify_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig"}',  # noqa: E501
        }
    )

    list_of_files = list(_MOCK_READ_CONTENTS.keys())
    migrated, non_migrated = find_and_replace_in_file(list_of_files)

    if migrated and non_migrated:
        assert len(migrated) == 3
        assert len(non_migrated) == 0
    assert "config1.json" in migrated
    assert "config2.json" in migrated

    # Verify that the correct content would have been "written"
    expected_config1 = dedent("""
        {
            "name": "device_2q"
        }
    """).strip()
    expected_config2 = dedent("""
        {
            "config_type": "QbloxHardwareCompilationConfig"
        }
    """).strip()

    assert mock_open_fixture[Path("config1.json")] == expected_config1
    assert mock_open_fixture[Path("config2.json")] == expected_config2


def test_no_files_migrated_with_mocks(mock_open_fixture) -> None:
    """
    Test case where no files contain the string, using mocks.
    """
    _MOCK_READ_CONTENTS.update(
        {
            Path("config_a.json"): '{"backend": "some_other_backend"}',
            Path("config_b.json"): '{"instrument": "my_device"}',
        }
    )

    list_of_files = list(_MOCK_READ_CONTENTS.keys())
    migrated, non_migrated = find_and_replace_in_file(list_of_files)

    if migrated:
        assert len(migrated) == 0

    if non_migrated:
        assert len(non_migrated) == 2
        assert "config_a.json" in non_migrated
        assert "config_b.json" in non_migrated

    # Verify no content was "written" by checking the fixture's dictionary
    assert not mock_open_fixture


def test_mixed_migration_with_mocks(mock_open_fixture) -> None:
    """
    Test case with a mix of files to be migrated and not, using mocks.
    """
    _MOCK_READ_CONTENTS.update(
        {
            Path(
                "config_1.json"
            ): '{"config_type": "quantify_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig"}',  # noqa: E501
            Path("config_2.json"): '{"instrument": "my_device"}',
        }
    )

    list_of_files = list(_MOCK_READ_CONTENTS.keys())
    migrated, non_migrated = find_and_replace_in_file(list_of_files)

    assert len(migrated) == 1

    if migrated:
        assert "config_1.json" in migrated

    if non_migrated:
        assert len(non_migrated) == 1
        assert "config_2.json" in non_migrated

    # Verify the correct content was "written" and the other was not touched
    expected_config1 = dedent("""
        {
            "config_type": "QbloxHardwareCompilationConfig"
        }
    """).strip()
    assert mock_open_fixture[Path("config_1.json")] == expected_config1
    assert Path("config_2.json") not in mock_open_fixture
