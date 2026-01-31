# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""
.. list-table::
    :header-rows: 1
    :widths: auto

    * - Import alias
      - Target
    * - :class:`.QuantumDevice`
      - :class:`!qblox_scheduler.QuantumDevice`
    * - :class:`.TimeableSchedule`
      - :class:`!qblox_scheduler.TimeableSchedule`
    * - :class:`.Resource`
      - :class:`!qblox_scheduler.Resource`
    * - :class:`.ClockResource`
      - :class:`!qblox_scheduler.ClockResource`
    * - :class:`.BasebandClockResource`
      - :class:`!qblox_scheduler.BasebandClockResource`
    * - :class:`.DigitalClockResource`
      - :class:`!qblox_scheduler.DigitalClockResource`
    * - :class:`.Operation`
      - :class:`!qblox_scheduler.Operation`
    * - :obj:`.structure`
      - :obj:`!qblox_scheduler.structure`
    * - :class:`.ScheduleGettable`
      - :class:`!qblox_scheduler.ScheduleGettable`
    * - :class:`.BasicElectronicNVElement`
      - :class:`!qblox_scheduler.BasicElectronicNVElement`
    * - :class:`.BasicSpinElement`
      - :class:`!qblox_scheduler.BasicSpinElement`
    * - :class:`.BasicTransmonElement`
      - :class:`!qblox_scheduler.BasicTransmonElement`
    * - :class:`.CompositeSquareEdge`
      - :class:`!qblox_scheduler.CompositeSquareEdge`
    * - :class:`.InstrumentCoordinator`
      - :class:`!qblox_scheduler.InstrumentCoordinator`
    * - :class:`.GenericInstrumentCoordinatorComponent`
      - :class:`!qblox_scheduler.GenericInstrumentCoordinatorComponent`
    * - :class:`.SerialCompiler`
      - :class:`!qblox_scheduler.SerialCompiler`
    * - :class:`.MockLocalOscillator`
      - :class:`!qblox_scheduler.MockLocalOscillator`
    * - :class:`.SpinEdge`
      - :class:`!qblox_scheduler.SpinEdge`
"""

import warnings

from qblox_scheduler.qblox.hardware_agent import HardwareAgent

from . import structure
from ._version import __version__
from .backends import SerialCompiler
from .device_under_test import (
    BasicElectronicNVElement,
    BasicSpinElement,
    BasicTransmonElement,
    ChargeSensor,
    CompositeSquareEdge,
    QuantumDevice,
    SpinEdge,
)
from .experiments.experiment import Step
from .gettables import ScheduleGettable
from .helpers.mock_instruments import MockLocalOscillator
from .instrument_coordinator import InstrumentCoordinator
from .instrument_coordinator.components.generic import (
    GenericInstrumentCoordinatorComponent,
)
from .operations.operation import Operation
from .resources import (
    BasebandClockResource,
    ClockResource,
    DigitalClockResource,
    Resource,
)
from .schedule import Schedule
from .schedules import TimeableSchedule

warnings.filterwarnings(
    "ignore",
    category=RuntimeWarning,
    module="quantify_core.utilities.general",
    message=".*qcodes\\.utils\\.helpers.*",
)

__all__ = [
    "BasebandClockResource",
    "BasicElectronicNVElement",
    "BasicSpinElement",
    "BasicTransmonElement",
    "ChargeSensor",
    "ClockResource",
    "CompositeSquareEdge",
    "DigitalClockResource",
    "GenericInstrumentCoordinatorComponent",
    "HardwareAgent",
    "InstrumentCoordinator",
    "MockLocalOscillator",
    "Operation",
    "QuantumDevice",
    "Resource",
    "Schedule",
    "ScheduleGettable",
    "SerialCompiler",
    "SpinEdge",
    "Step",
    "TimeableSchedule",
    "__version__",
    "structure",
]
