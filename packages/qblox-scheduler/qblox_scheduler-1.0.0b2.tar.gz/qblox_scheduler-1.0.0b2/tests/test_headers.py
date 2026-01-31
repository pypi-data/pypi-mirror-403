import os
import pprint
from pathlib import Path

import pytest


def test_header() -> None:
    skipfiles = {
        "__init__.py",
        "conftest.py",
        "setup.py",
        "_version.py",
        "_static_version.py",
        "mock_setup.py",
    }
    skipdirs = {"docs", ".", "tests", "__pycache__", "venv"}
    failures = []
    qblox_scheduler_path = Path(__file__).resolve().parent.parent.resolve()
    header_lines = [
        "# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler",
        "# Licensed according to the LICENSE file on the main branch",
    ]
    for root, _, files in os.walk(qblox_scheduler_path):
        # skip hidden folders, etc
        if any(part.startswith(name) for part in Path(root).parts for name in skipdirs):
            continue
        for file_name in files:
            if file_name[-3:] == ".py" and file_name not in skipfiles:
                file_path = Path(root) / file_name
                with open(file_path) as file:
                    lines_iter = (line.strip() for line in file)
                    line_matches = [
                        expected_line == line
                        for expected_line, line in zip(header_lines, lines_iter, strict=False)
                    ]
                    if not all(line_matches):
                        failures.append(str(file_path))
    if failures:
        pytest.fail(f"Bad headers:\n{pprint.pformat(failures)}")
