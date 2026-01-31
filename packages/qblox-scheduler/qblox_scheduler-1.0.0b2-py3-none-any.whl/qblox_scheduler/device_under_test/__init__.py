"""
Module containing instruments that represent quantum devices and elements.

The elements and their components are intended to generate valid
:ref:`device configuration <sec-device-config>` files for compilation from the
:ref:`quantum-circuit layer <sec-user-guide-quantum-circuit>` to the
:ref:`quantum-device layer description<sec-user-guide-quantum-device>`.
"""

from qblox_scheduler.yaml_utils import register_legacy_instruments, yaml

from .composite_square_edge import CompositeSquareEdge
from .nv_element import BasicElectronicNVElement
from .quantum_device import QuantumDevice
from .spin_edge import SpinEdge
from .spin_element import BasicSpinElement, ChargeSensor
from .transmon_element import BasicTransmonElement

# This call must be performed here, once all the elements and edges have been imported
register_legacy_instruments(yaml)


__all__ = [
    "BasicElectronicNVElement",
    "BasicSpinElement",
    "BasicTransmonElement",
    "ChargeSensor",
    "CompositeSquareEdge",
    "QuantumDevice",
    "SpinEdge",
]
