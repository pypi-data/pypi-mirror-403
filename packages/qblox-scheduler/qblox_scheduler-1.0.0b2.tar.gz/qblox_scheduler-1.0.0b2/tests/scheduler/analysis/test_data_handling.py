import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from qblox_scheduler.analysis.data_handling import OutputDirectoryManager, _get_default_datadir


@pytest.fixture
def temp_directory():
    """Fixture providing a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_home_directory(tmp_path):
    """Fixture to mock Path.home() for testing."""
    with patch("pathlib.Path.home", return_value=tmp_path):
        yield tmp_path


@pytest.mark.parametrize("verbose,should_print", [(True, True), (False, False)])
@patch("rich.print")
def test_get_default_datadir_verbose_behavior(
    mock_rich_print, mock_home_directory, verbose, should_print
) -> None:
    """Test _get_default_datadir verbose parameter controls printing behavior."""
    result = _get_default_datadir(verbose=verbose)

    expected_path = (mock_home_directory / "qblox_data").resolve()
    assert result == expected_path

    if should_print:
        # Check that rich.print was called with the expected message
        mock_rich_print.assert_called_once_with(f"Data will be saved in:\n{expected_path}")
    else:
        # Check that rich.print was not called
        mock_rich_print.assert_not_called()


def test_get_default_datadir_returns_path_object(mock_home_directory) -> None:
    """Test that _get_default_datadir returns a Path object."""
    result = _get_default_datadir(verbose=False)

    assert isinstance(result, Path)
    assert result.name == "qblox_data"
    assert result.parent == mock_home_directory


def test_set_datadir_with_valid_path(temp_directory) -> None:
    """Test setting datadir with a valid existing directory."""
    OutputDirectoryManager.set_datadir(temp_directory)
    assert OutputDirectoryManager.get_datadir() == temp_directory


def test_set_datadir_creates_directory_if_not_exists(temp_directory) -> None:
    """Test that set_datadir creates directory if it doesn't exist."""
    new_dir = temp_directory / "new_directory"

    OutputDirectoryManager.set_datadir(new_dir)

    assert new_dir.exists()
    assert OutputDirectoryManager.get_datadir() == new_dir


@patch("qblox_scheduler.analysis.data_handling._get_default_datadir")
@patch("os.path.isdir")
def test_set_datadir_none_resets_to_default(mock_isdir, mock_get_default, temp_directory) -> None:
    """Test that setting datadir to None resets to default."""
    mock_get_default.return_value = temp_directory / "default_path"
    mock_isdir.return_value = True  # Mock that the directory exists

    OutputDirectoryManager.set_datadir(None)

    mock_get_default.assert_called_once()
    assert OutputDirectoryManager.get_datadir() == temp_directory / "default_path"


def test_set_datadir_raises_permission_error_if_mkdir_fails(tmp_path) -> None:
    """Test that set_datadir raises PermissionError if mkdir fails."""
    # Mock Path.mkdir to raise PermissionError
    with patch("pathlib.Path.mkdir") as mock_mkdir:
        mock_mkdir.side_effect = PermissionError("Permission denied")

        # Mock the directory to which we don't have permissions
        with pytest.raises(PermissionError) as exc_info:
            OutputDirectoryManager.set_datadir(Path("/some/protected/directory"))
        assert "Permission error while setting datadir" in str(exc_info.value)

    OutputDirectoryManager.set_datadir(tmp_path)
    assert OutputDirectoryManager.get_datadir() == tmp_path


@patch("pathlib.Path.is_dir")
def test_get_datadir_invalid_directory_raises_error(mock_isdir, temp_directory) -> None:
    """Test get_datadir raises NotADirectoryError for invalid directory states."""
    OutputDirectoryManager.set_datadir(temp_directory)

    # Mock that the directory doesn't exist
    mock_isdir.return_value = False

    # Then test that get_datadir raises the error
    with pytest.raises(NotADirectoryError) as exc_info:
        OutputDirectoryManager.get_datadir()

    assert "The datadir is not valid." in str(exc_info.value)


def test_get_datadir_returns_current_directory(temp_directory) -> None:
    """Test that get_datadir returns the current datadir."""
    OutputDirectoryManager.set_datadir(temp_directory)
    result = OutputDirectoryManager.get_datadir()
    assert result == temp_directory
