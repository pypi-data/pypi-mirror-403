# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""
Module containing the standard library of commonly used operations as well as the
:class:`.Operation` class.


.. tip::

    Quantify scheduler can trivially be extended by creating custom operations. Take a
    look at e.g., the pulse library for examples on how to implement custom pulses.

"""

from .acquisition_library import (
    Acquisition,
    DualThresholdedTriggerCount,
    NumericalSeparatedWeightedIntegration,
    NumericalWeightedIntegration,
    SSBIntegrationComplex,
    ThresholdedAcquisition,
    ThresholdedTriggerCount,
    Timetag,
    TimetagTrace,
    Trace,
    TriggerCount,
    WeightedIntegratedSeparated,
    WeightedThresholdedAcquisition,
)
from .conditional_reset import ConditionalReset
from .control_flow_library import (
    ConditionalOperation,
    ControlFlowOperation,
    ControlFlowSpec,
    LoopOperation,
    LoopStrategy,
)
from .expressions import DType
from .gate_library import (
    CNOT,
    CZ,
    X90,
    Y90,
    Z90,
    H,
    Measure,
    Reset,
    Rxy,
    Rz,
    S,
    SDagger,
    T,
    TDagger,
    X,
    Y,
    Z,
)
from .hardware_operations import (
    InlineQ1ASM,
    long_chirp_pulse,
    long_ramp_pulse,
    long_square_pulse,
    staircase_pulse,
)
from .hardware_operations.pulse_library import LatchReset, SimpleNumericalPulse
from .loop_domains import arange, linspace
from .nv_native_library import ChargeReset, CRCount
from .operation import Operation
from .pulse_compensation_library import (
    PulseCompensation,
)
from .pulse_factories import (
    composite_square_pulse,
    non_implemented_pulse,
    nv_spec_pulse_mw,
    phase_shift,
    rxy_drag_pulse,
    rxy_gauss_pulse,
    rxy_pulse,
    spin_init_pulse,
)
from .pulse_library import (
    ChirpPulse,
    DRAGPulse,
    GaussPulse,
    IdlePulse,
    MarkerPulse,
    NumericalPulse,
    RampPulse,
    ReferenceMagnitude,
    ResetClockPhase,
    SetClockFrequency,
    ShiftClockPhase,
    SkewedHermitePulse,
    SoftSquarePulse,
    SquarePulse,
    StaircasePulse,
    SuddenNetZeroPulse,
    Timestamp,
    VoltageOffset,
    WindowOperation,
)

__all__ = [
    "CNOT",
    "CZ",
    "X90",
    "Y90",
    "Z90",
    "Acquisition",
    "CRCount",
    "ChargeReset",
    "ChirpPulse",
    "ConditionalOperation",
    "ConditionalReset",
    "ControlFlowOperation",
    "ControlFlowSpec",
    "DRAGPulse",
    "DType",
    "DualThresholdedTriggerCount",
    "GaussPulse",
    "H",
    "IdlePulse",
    "InlineQ1ASM",
    "LatchReset",
    "LoopOperation",
    "LoopStrategy",
    "MarkerPulse",
    "Measure",
    "NumericalPulse",
    "NumericalSeparatedWeightedIntegration",
    "NumericalSeparatedWeightedIntegration",
    "NumericalSeparatedWeightedIntegration",
    "NumericalWeightedIntegration",
    "NumericalWeightedIntegration",
    "NumericalWeightedIntegration",
    "Operation",
    "PulseCompensation",
    "RampPulse",
    "ReferenceMagnitude",
    "Reset",
    "ResetClockPhase",
    "Rxy",
    "Rz",
    "S",
    "SDagger",
    "SSBIntegrationComplex",
    "SetClockFrequency",
    "ShiftClockPhase",
    "SimpleNumericalPulse",
    "SkewedHermitePulse",
    "SoftSquarePulse",
    "SquarePulse",
    "StaircasePulse",
    "SuddenNetZeroPulse",
    "T",
    "TDagger",
    "ThresholdedAcquisition",
    "ThresholdedTriggerCount",
    "Timestamp",
    "Timetag",
    "TimetagTrace",
    "Trace",
    "TriggerCount",
    "TriggerCount",
    "TriggerCount",
    "VoltageOffset",
    "WeightedIntegratedSeparated",
    "WeightedThresholdedAcquisition",
    "WindowOperation",
    "X",
    "Y",
    "Z",
    "arange",
    "composite_square_pulse",
    "linspace",
    "long_chirp_pulse",
    "long_ramp_pulse",
    "long_square_pulse",
    "non_implemented_pulse",
    "nv_spec_pulse_mw",
    "phase_shift",
    "rxy_drag_pulse",
    "rxy_gauss_pulse",
    "rxy_pulse",
    "spin_init_pulse",
    "staircase_pulse",
]
