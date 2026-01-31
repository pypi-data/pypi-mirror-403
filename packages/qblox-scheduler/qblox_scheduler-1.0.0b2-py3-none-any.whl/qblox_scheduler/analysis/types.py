# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Module containing the types for use with the analysis classes."""

from collections import UserDict
from typing import Any, ClassVar

from jsonschema import validate

from quantify_core.utilities.general import load_json_schema


# WARNING! Do not inherit from dict! if you do, `AnalysisSettings.update will skip the
# validation done in `__setitem__`.
class AnalysisSettings(UserDict):
    """
    Analysis settings with built-in schema validations.

    .. jsonschema:: ../../../../../../src/qblox_scheduler/analysis/schemas/analysis_settings.json#/configurations
    """  # noqa: E501

    schema = load_json_schema(__file__, "analysis_settings.json")["configurations"]
    schema_individual: ClassVar[dict[str, Any]] = dict(schema)
    schema_individual.pop("required")

    def __init__(self, settings: dict = None):
        """Initializes and validates the passed settings."""
        super().__init__()
        if settings:
            validate(settings, self.schema)
            for key, value in settings.items():
                super().__setitem__(key, value)

    def __setitem__(self, key, value):
        """Items are validated before assigning."""
        validate({key: value}, self.schema_individual)
        super().__setitem__(key, value)
