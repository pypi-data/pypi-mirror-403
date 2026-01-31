# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Helper functions to perform the version check for qblox_instruments."""

from __future__ import annotations

import logging

from packaging.requirements import Requirement

logger = logging.getLogger(__name__)

try:
    from qblox_instruments.build import __version__ as driver_version
except ImportError:
    driver_version = None  # Prior to v0.3.2 __version__ was not there

SUPPORTED_DRIVER_VERSIONS = Requirement("qblox-instruments>=0.17.0,<2")
"""Tuple containing all the version supported by this version of the backend."""
raise_on_version_mismatch: bool = True
"""Can be set to false to override version check."""


class DriverVersionError(Exception):
    """Raise when the installed driver version is not supported."""


def verify_qblox_instruments_version(
    version: str | None = driver_version,
    match_versions: Requirement = SUPPORTED_DRIVER_VERSIONS,
) -> None:
    """
    Verifies whether the installed version is supported by the qblox_backend.

    Parameters
    ----------
    version
        The Qblox driver versions (``qblox-instruments`` python package).
    match_versions
        A tuple of version strings (can be `major`, `major.minor`, and/or `major.minor.patch`).

    Raises
    ------
    DriverVersionError
        When an incorrect or no installation of qblox-instruments was found.

    """
    if not raise_on_version_mismatch:
        logger.warning(
            "Qblox driver version check skipped with %s.raise_on_version_mismatch=%s.",
            __name__,
            raise_on_version_mismatch,
        )
        return

    if version is None:
        raise DriverVersionError(
            "Version check for Qblox driver (qblox-instruments) could not be "
            "performed. Either the package is not installed correctly or a version "
            "<0.3.2 was found."
        )
    if not match_versions.specifier.contains(version):
        raise DriverVersionError(
            f"The installed Qblox driver (qblox-instruments) version {version} is not "
            f"supported by backend. Please install one of the supported versions "
            f"({match_versions}) in order to use this backend."
        )
