# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Python dataclasses for compilation to Qblox hardware."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from dataclasses_json import DataClassJsonMixin

from qblox_scheduler.backends.qblox.enums import FilterConfig, FilterMarkerDelay


@dataclass
class QbloxRealTimeFilter(DataClassJsonMixin):
    """An individual real time filter on Qblox hardware."""

    coeffs: Optional[Union[float, list[float]]] = None
    """Coefficient(s) of the filter.
       Can be None if there is no filter
       or if it is inactive."""
    config: FilterConfig = FilterConfig.BYPASSED
    """Configuration of the filter.
       One of 'BYPASSED', 'ENABLED',
       or 'DELAY_COMP'."""
    marker_delay: FilterMarkerDelay = FilterMarkerDelay.BYPASSED
    """State of the marker delay.
       One of 'BYPASSED' or 'ENABLED'."""


__all__ = ["QbloxRealTimeFilter"]
