# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
"""Tests for the InstrumentCompiler subclasses."""

from typing import TYPE_CHECKING

import pytest

from qblox_scheduler.backends.qblox import constants
from qblox_scheduler.backends.qblox.qblox_acq_index_manager import (
    AcquisitionMemoryError,
    QbloxAcquisitionHardwareMapping,
    QbloxAcquisitionHardwareMappingNonFullyAppend,
    QbloxAcquisitionIndexBin,
    QbloxAcquisitionIndexManager,
    QbloxAcquisitionModuleResourceManager,
)

if TYPE_CHECKING:
    from collections.abc import Hashable


def test_allocate_mixed_acquisitions():
    qblox_acq_module_resource_manager = QbloxAcquisitionModuleResourceManager(
        constants.MAX_NUMBER_OF_BINS
    )
    qblox_acq_index_manager = QbloxAcquisitionIndexManager(qblox_acq_module_resource_manager)

    qblox_acq_index, qblox_acq_bin = qblox_acq_index_manager.allocate_bins("ch0", 2, None, None)
    assert (qblox_acq_index, qblox_acq_bin) == (0, 0)
    qblox_acq_index = qblox_acq_index_manager.allocate_trace("ch_trace")
    assert qblox_acq_index == (1, 0)
    qblox_acq_index, qblox_acq_bin = qblox_acq_index_manager.allocate_bins("ch1", 6, None, 2)
    assert (qblox_acq_index, qblox_acq_bin) == (2, 0)

    qblox_acq_index, qblox_acq_bin = qblox_acq_index_manager.allocate_bins(
        "ch0", [5, 6, 7, 8], None, None
    )
    assert (qblox_acq_index, qblox_acq_bin) == (0, 1)

    qblox_acq_index, qblox_acq_bin = qblox_acq_index_manager.allocate_bins(
        "ch1", [7, 8, 9], None, 2
    )
    assert (qblox_acq_index, qblox_acq_bin) == (2, 2)

    qblox_acq_index, qblox_acq_bin = qblox_acq_index_manager.allocate_bins("ch1", 10, None, 2)
    assert (qblox_acq_index, qblox_acq_bin) == (2, 8)

    qblox_acq_index, qblox_acq_bin = qblox_acq_index_manager.allocate_bins(
        "ch2", list(range(constants.MAX_NUMBER_OF_RUNTIME_ALLOCATED_QBLOX_ACQ_BINS - 3)), None, None
    )
    assert (qblox_acq_index, qblox_acq_bin) == (3, 0)

    qblox_acq_index, qblox_acq_bin = qblox_acq_index_manager.allocate_bins("ch0", 9, None, None)
    assert (qblox_acq_index, qblox_acq_bin) == (0, 5)

    qblox_acq_index = qblox_acq_index_manager.allocate_qblox_index("ch3")
    assert qblox_acq_index == 4

    expected_acq_declaration_dict = {
        "0": {"num_bins": 6, "index": 0},
        "1": {"num_bins": 1, "index": 1},
        "2": {"num_bins": 10, "index": 2},
        "3": {"num_bins": 4093, "index": 3},
        "4": {"num_bins": 4096, "index": 4},
    }
    assert qblox_acq_index_manager.acq_declaration_dict() == expected_acq_declaration_dict

    expected_acq_hardware_mapping: dict[Hashable, QbloxAcquisitionHardwareMappingNonFullyAppend] = {
        "ch0": {
            2: QbloxAcquisitionIndexBin(0, 0, 1, None),
            5: QbloxAcquisitionIndexBin(0, 1, 4, None),
            6: QbloxAcquisitionIndexBin(0, 2, 4, None),
            7: QbloxAcquisitionIndexBin(0, 3, 4, None),
            8: QbloxAcquisitionIndexBin(0, 4, 4, None),
            9: QbloxAcquisitionIndexBin(0, 5, 1, None),
        },
        "ch1": {
            6: QbloxAcquisitionIndexBin(2, 0, 1, None),
            7: QbloxAcquisitionIndexBin(2, 2, 3, None),
            8: QbloxAcquisitionIndexBin(2, 3, 3, None),
            9: QbloxAcquisitionIndexBin(2, 4, 3, None),
            10: QbloxAcquisitionIndexBin(2, 8, 1, None),
        },
        "ch2": {
            i: QbloxAcquisitionIndexBin(
                3, i, constants.MAX_NUMBER_OF_RUNTIME_ALLOCATED_QBLOX_ACQ_BINS - 3, None
            )
            for i in range(constants.MAX_NUMBER_OF_RUNTIME_ALLOCATED_QBLOX_ACQ_BINS - 3)
        },
        "ch3": 4,
        "ch_trace": 1,
    }
    assert qblox_acq_index_manager.acq_hardware_mapping() == QbloxAcquisitionHardwareMapping(
        non_fully_append=expected_acq_hardware_mapping, fully_append=[]
    )


def test_out_of_bins():
    max_bins = constants.MAX_NUMBER_OF_BINS

    qblox_acq_module_resource_manager = QbloxAcquisitionModuleResourceManager(max_bins)
    qblox_acq_index_manager = QbloxAcquisitionIndexManager(qblox_acq_module_resource_manager)

    with pytest.raises(AcquisitionMemoryError, match="Out of Qblox acquisition bins."):
        qblox_acq_index_manager.allocate_bins("ch1", list(range(max_bins + 1)), None, None)


def test_out_of_all_bins():
    max_bins = constants.MAX_NUMBER_OF_BINS

    qblox_acq_module_resource_manager = QbloxAcquisitionModuleResourceManager(max_bins)
    qblox_acq_index_manager = QbloxAcquisitionIndexManager(qblox_acq_module_resource_manager)

    qblox_acq_index_manager.allocate_bins("ch0", list(range(max_bins)), None, None)

    with pytest.raises(AcquisitionMemoryError, match="Out of Qblox acquisition bins."):
        qblox_acq_index_manager.allocate_bins("ch1", 1, None, None)


def test_out_of_all_shared_bins():
    max_bins = constants.MAX_NUMBER_OF_BINS

    qblox_acq_module_resource_manager = QbloxAcquisitionModuleResourceManager(max_bins)
    qblox_acq_index_manager_a = QbloxAcquisitionIndexManager(qblox_acq_module_resource_manager)
    qblox_acq_index_manager_b = QbloxAcquisitionIndexManager(qblox_acq_module_resource_manager)

    qblox_acq_index_manager_a.allocate_bins("ch0", list(range(max_bins)), None, None)

    with pytest.raises(AcquisitionMemoryError, match="Out of Qblox acquisition bins."):
        qblox_acq_index_manager_b.allocate_bins("ch1", 1, None, None)


def test_out_of_qblox_acq_indices():
    qblox_acq_module_resource_manager = QbloxAcquisitionModuleResourceManager(
        constants.MAX_NUMBER_OF_BINS
    )
    qblox_acq_index_manager = QbloxAcquisitionIndexManager(qblox_acq_module_resource_manager)

    max_qblox_acq_indices = constants.NUMBER_OF_QBLOX_ACQ_INDICES

    for i in range(max_qblox_acq_indices):
        qblox_acq_index_manager.allocate_bins(f"ch{i}", 0, None, None)

    with pytest.raises(AcquisitionMemoryError, match="Out of Qblox acquisition indices."):
        qblox_acq_index_manager.allocate_bins("ch_extra", 1, None, None)


def test_out_of_qblox_acq_indices_qblox_index_trace():
    qblox_acq_module_resource_manager = QbloxAcquisitionModuleResourceManager(
        constants.MAX_NUMBER_OF_BINS
    )
    qblox_acq_index_manager = QbloxAcquisitionIndexManager(qblox_acq_module_resource_manager)

    max_qblox_acq_indices = constants.NUMBER_OF_QBLOX_ACQ_INDICES

    for i in range(max_qblox_acq_indices):
        qblox_acq_index_manager.allocate_qblox_index(i)

    with pytest.raises(AcquisitionMemoryError, match="Out of Qblox acquisition indices."):
        qblox_acq_index_manager.allocate_qblox_index("ch1")


def test_multiple_trace_raises():
    qblox_acq_module_resource_manager = QbloxAcquisitionModuleResourceManager(
        constants.MAX_NUMBER_OF_BINS
    )
    qblox_acq_index_manager = QbloxAcquisitionIndexManager(qblox_acq_module_resource_manager)

    qblox_acq_index_manager.allocate_trace(0)
    qblox_acq_index_manager.allocate_trace(0)

    with pytest.raises(
        AcquisitionMemoryError,
        match="Only one acquisition channel per port-clock can be specified, "
        "if the 'Trace' acquisition protocol is used. "
        "Attempted to compile for acquisition channel '1'.",
    ):
        qblox_acq_index_manager.allocate_trace(1)
