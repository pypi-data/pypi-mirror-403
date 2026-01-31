# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""
Utility class for dynamically allocating
Qblox acquisition indices and bins and for Qblox sequencers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Union

from qblox_scheduler.backends.qblox import constants

if TYPE_CHECKING:
    from collections.abc import Hashable

    from qblox_scheduler.backends.types.common import ThresholdedTriggerCountMetadata
    from qblox_scheduler.enums import BinMode
    from qblox_scheduler.helpers.generate_acq_channels_data import AcquisitionIndices

QbloxAcquisitionIndex = int


@dataclass
class QbloxAcquisitionIndexBin:
    """Qblox acquisition index and QBlox acquisition bin."""

    index: QbloxAcquisitionIndex
    """Qblox acquisition index."""
    bin: int
    """
    Qblox acquisition bin.
    For average bin mode, this is the bin where the data is stored.
    For append bin mode, this is first bin where data is stored,
    for each loop and repetition cycle, the data is consecutively stored.
    """
    stride: int
    """
    Stride.
    Only used for acquisitions within a loop (not schedule repetitions).
    Defines what's the stride between each repetitions of the schedule for the data.

    The assumption is that for an append bin mode operation
    with loops and schedule repetitions there is only one register;
    the register's inner iteration first goes through the loop,
    and then the schedule repetitions.
    """
    thresholded_trigger_count_metadata: ThresholdedTriggerCountMetadata | None
    """
    Thresholded trigger count metadata.
    Only applicable for ThresholdedTriggerCount,
    and only on QRM, QRM-RF, QRC.
    On QTM, this is unused, threshold calculations are on the hardware.
    """


QbloxAcquisitionBinMapping = dict[int, QbloxAcquisitionIndexBin]
"""
Binned type acquisition hardware mapping.

Each value maps the acquisition index to a hardware bin,
which is specified by the Qblox acquisition index, and the Qblox acquisition bin.
"""


QbloxAcquisitionHardwareMappingNonFullyAppend = Union[
    QbloxAcquisitionBinMapping,
    QbloxAcquisitionIndex,
]
"""
Type for all non-fully append type acquisition hardware mapping.

This is a union of types, because the exact mapping type depends on the protocol.
"""


@dataclass
class FullyAppendAcqInfo:
    """Acquisition info for fully append acquisition."""

    acq_channel: Hashable
    acq_index: AcquisitionIndices
    thresholded_trigger_count_metadata: ThresholdedTriggerCountMetadata | None


@dataclass
class AcqFullyAppendLoopNode:
    """Node to represent all acquisitions which are within the same loop tree structure."""

    parent: AcqFullyAppendLoopNode | None
    children: list[AcqFullyAppendLoopNode | FullyAppendAcqInfo]
    repetitions: int | None
    bin_mode: BinMode | None

    def add_control_flow_child(
        self, child_repetitions: int | None, bin_mode: BinMode | None
    ) -> AcqFullyAppendLoopNode:
        """
        Adds a new control flow as a child to the current node,
        and returns it.
        """
        new_child = AcqFullyAppendLoopNode(
            parent=self, children=[], repetitions=child_repetitions, bin_mode=bin_mode
        )
        self.children.append(new_child)
        return new_child

    def return_control_flow_child(self) -> AcqFullyAppendLoopNode:
        """
        Returns the parent, and
        if the current node is empty, it will remove it from the tree.
        Only call this function after any add_control_flow_child was called.
        """
        if self.parent is None:
            # While iterating the control flow tree,
            # this can only be called after we return from a control flow,
            # which means that the parent cannot be None.
            raise RuntimeError("Compilation error: add_control_flow_child was not called before.")
        if len(self.children) == 0:
            # Removing the current branch of the tree
            # if there are no children in it.
            self.parent.children.pop()
        return self.parent


@dataclass
class QbloxAcquisitionBinMappingFullyAppend:
    """
    Binned type acquisition hardware mapping for acquisitions
    that are fully appended for all loop levels.
    """

    qblox_acq_index: QbloxAcquisitionIndex
    qblox_acq_bin_offset: int
    """
    The starting bin where all acquisition data is stored for this mapping.
    """
    tree: AcqFullyAppendLoopNode
    """
    Root node for the whole tree of the loop and acquisition tree.
    """


@dataclass
class QbloxAcquisitionHardwareMapping:
    """Acquisition hardware mapping for all acquisitions."""

    non_fully_append: dict[Hashable, QbloxAcquisitionHardwareMappingNonFullyAppend]
    fully_append: list[QbloxAcquisitionBinMappingFullyAppend]


class AcquisitionMemoryError(ValueError):
    """Raised when there is an error in allocating acquisition memory."""


class QbloxAcquisitionModuleResourceManager:
    """Utility class that keeps track of all the reserved acquisition resources for a module."""

    def __init__(self, maximum_bins: int) -> None:
        self._used_bins = 0
        self._maximum_bins = maximum_bins

    @property
    def total_used_bins(self) -> int:
        """Total amount of in-use bins in module."""
        return self._used_bins

    @total_used_bins.setter
    def total_used_bins(self, value: int) -> None:
        self._used_bins = value

    @property
    def total_remaining_free_bins(self) -> int:
        """Total amount of remaining available bins in module."""
        return self._maximum_bins - self._used_bins


class _SequencerAcquisitionModel:
    def __init__(
        self,
        module_resource_manager: QbloxAcquisitionModuleResourceManager,
        maximum_qblox_acq_indices: int = constants.NUMBER_OF_QBLOX_ACQ_INDICES,
    ) -> None:
        self._num_bins: list[int] = []
        self._module_resource_manager = module_resource_manager
        self._maximum_qblox_acq_indices = maximum_qblox_acq_indices

    @property
    def total_remaining_free_bins(self) -> int:
        return self._module_resource_manager.total_remaining_free_bins

    def reserve_new_qblox_acq_index(self, num_bins: int = 0) -> int:
        if len(self._num_bins) >= self._maximum_qblox_acq_indices:
            raise AcquisitionMemoryError("Out of Qblox acquisition indices.")
        self._num_bins.append(0)
        acq_index = len(self._num_bins) - 1
        if num_bins:
            self.reserve_bins(acq_index, num_bins)
        return acq_index

    def reserve_bins(self, qblox_acq_index: int, num_bins: int) -> None:
        if num_bins > self.total_remaining_free_bins:
            raise AcquisitionMemoryError("Out of Qblox acquisition bins.")
        self._num_bins[qblox_acq_index] += num_bins
        self._module_resource_manager.total_used_bins += num_bins

    def next_free_bin_index(self, qblox_acq_index: int) -> int:
        """
        The next free bin for this Qblox acquisition index. Equal to the total amount of
        reserved bins for this Qblox acquisition index.
        """
        return self._num_bins[qblox_acq_index]

    def to_acq_declaration_dict(self) -> dict[str, Any]:
        """
        Acquisition declaration dictionary.

        This data is used in :class:`qblox_instruments.qcodes_drivers.Sequencer`
        `sequence` parameter's `"acquisitions"`.
        """
        return {
            str(qblox_acq_index): {"num_bins": num_bins, "index": qblox_acq_index}
            for qblox_acq_index, num_bins in enumerate(self._num_bins)
        }


class QbloxAcquisitionIndexManager:
    """
    Utility class that keeps track of all the reserved indices, bins for a sequencer.

    Each acquisition channel is mapped to a unique Qblox acquisition index.
    For binned acquisitions, each new allocation request reserves
    the Qblox acquisition bins in order (incrementing the bin index by one).
    For trace and ttl and other acquisitions, the whole Qblox acquisition index is reserved,
    there, the bin index has no relevance.
    """

    def __init__(self, module_resource_manager: QbloxAcquisitionModuleResourceManager) -> None:
        self._acq_hardware_mapping_binned: dict[Hashable, QbloxAcquisitionBinMapping] = {}
        """
        Acquisition hardware mapping for binned acquisitions.
        """
        self._acq_hardware_mapping_not_binned: dict[Hashable, QbloxAcquisitionIndex] = {}
        """
        Acquisition hardware mapping for not binned acquisitions.
        """
        self._sequencer_acquisition_model = _SequencerAcquisitionModel(module_resource_manager)
        """
        Data model of sequencer acquisition memory, which keeps track of the allocated
        amount of bins for each Qblox acquisition index.
        """
        self._acq_channel_to_qblox_acq_index: dict[Hashable, int] = {}
        """
        Maps each acquisition channel to the
        Qblox acquisition index it uses.
        """
        self._fully_append_qblox_acq_index: int | None = None
        """
        Qblox acquisition index used by the fully append mode acquisitions.
        """
        self._trace_allocated: bool = False
        """
        Specifying whether a Trace or TimetagTrace have already been allocated.
        """
        self._acq_hardware_mapping_fully_append: list[QbloxAcquisitionBinMappingFullyAppend] = []

    def _number_of_free_qblox_bins(self) -> int:
        return self._sequencer_acquisition_model.total_remaining_free_bins

    def _next_qblox_acq_index_with_all_free_bins(self) -> int:
        return self._sequencer_acquisition_model.reserve_new_qblox_acq_index()

    def _reserve_qblox_acq_bins_fully_append(
        self,
        number_of_acq_indices: int,
        qblox_acq_index: int,
        tree: AcqFullyAppendLoopNode,
        repetitions: int,
    ) -> int:
        next_free_qblox_bin: int = self._sequencer_acquisition_model.next_free_bin_index(
            qblox_acq_index
        )
        self._sequencer_acquisition_model.reserve_bins(
            qblox_acq_index, number_of_acq_indices * repetitions
        )
        self._acq_hardware_mapping_fully_append.append(
            QbloxAcquisitionBinMappingFullyAppend(qblox_acq_index, next_free_qblox_bin, tree)
        )

        return next_free_qblox_bin

    def allocate_bins_fully_append(
        self,
        number_of_acq_indices: int,
        tree: AcqFullyAppendLoopNode,
        repetitions: int | None,
    ) -> tuple[int, int]:
        """
        Allocates Qblox acquisition bins for acquisitions
        which needs to be fully appended for all loop levels.

        Parameters
        ----------
        number_of_acq_indices
            Number of acquisition indices to allocate.
        tree
            The loop tree structure for all of the acquisitions.
        repetitions
            Repetitions of the schedule when using append bin mode.

        Returns
        -------
            The Qblox acquisition index, and the Qblox acquisition bin offset as integers.

        Raises
        ------
        AcquisitionMemoryError
            When the QbloxAcquisitionBinManager runs out of bins to allocate.

        """
        # Currently only repetitions=1 is implemented.
        assert repetitions == 1

        if self._fully_append_qblox_acq_index is None:
            qblox_acq_index = self._next_qblox_acq_index_with_all_free_bins()
        else:
            qblox_acq_index = self._fully_append_qblox_acq_index

        qblox_acq_bin_offset: int = self._reserve_qblox_acq_bins_fully_append(
            number_of_acq_indices,
            qblox_acq_index,
            tree,
            repetitions,
        )

        self._fully_append_qblox_acq_index = qblox_acq_index

        return qblox_acq_index, qblox_acq_bin_offset

    def _reserve_qblox_acq_bins(
        self,
        number_of_acq_indices: int,
        qblox_acq_index: int,
        acq_channel: Hashable,
        acq_indices: list[int] | None,
        thresholded_trigger_count_metadata: ThresholdedTriggerCountMetadata | None,
        repetitions: int,
    ) -> int:
        """
        Reserves the Qblox acquisition bin with the parameters.
        This function already assumes that the bin is free, not yet used.

        Note, `number_of_acq_indices` must be equal to the length of `acq_indices` if not `None`.

        Parameters
        ----------
        number_of_acq_indices
            Number of acquisition indices to reserve.
        qblox_acq_index
            Qblox acquisition index to be used.
        acq_channel
            Acquisition channel.
        acq_indices
            Acquisition index.
            If `None`, it has no corresponding acquisition index (for example Trace acquisition).
        thresholded_trigger_count_metadata
            Thresholded trigger count metadata. If not applicable, `None`.
        repetitions
            Repetitions of the schedule for append bin mode; otherwise 1.

        Returns
        -------
            The starting Qblox acquisition bin.

        """
        next_free_qblox_bin: int = self._sequencer_acquisition_model.next_free_bin_index(
            qblox_acq_index
        )

        if acq_indices is None:
            if acq_channel in self._acq_hardware_mapping_binned:
                raise ValueError(
                    f"QbloxAcquisitionIndexManager conflicting type of acquisitions for "
                    f"{acq_channel=} and {qblox_acq_index=}."
                )
            self._acq_hardware_mapping_not_binned[acq_channel] = qblox_acq_index
        else:
            assert len(acq_indices) == number_of_acq_indices
            if acq_channel in self._acq_hardware_mapping_not_binned:
                raise ValueError(
                    f"QbloxAcquisitionIndexManager conflicting type of acquisitions for "
                    f"{acq_channel=} and {qblox_acq_index=}."
                )
            new_qblox_acq_bins = range(
                next_free_qblox_bin, next_free_qblox_bin + number_of_acq_indices
            )
            new_qblox_bin_mappings: QbloxAcquisitionBinMapping = {
                i: QbloxAcquisitionIndexBin(
                    index=qblox_acq_index,
                    bin=qblox_bin,
                    stride=number_of_acq_indices,
                    thresholded_trigger_count_metadata=thresholded_trigger_count_metadata,
                )
                for (i, qblox_bin) in zip(acq_indices, new_qblox_acq_bins, strict=False)
            }
            if acq_channel not in self._acq_hardware_mapping_binned:
                self._acq_hardware_mapping_binned[acq_channel] = new_qblox_bin_mappings
            else:
                self._acq_hardware_mapping_binned[acq_channel].update(new_qblox_bin_mappings)

        self._sequencer_acquisition_model.reserve_bins(
            qblox_acq_index, number_of_acq_indices * repetitions
        )

        return next_free_qblox_bin

    def allocate_bins(
        self,
        acq_channel: Hashable,
        acq_indices: list[int] | int,
        thresholded_trigger_count_metadata: ThresholdedTriggerCountMetadata | None,
        repetitions: int | None,
    ) -> tuple[int, int]:
        """
        Allocates len(acq_indices) number of Qblox acquisition bins.

        Parameters
        ----------
        acq_channel
            Acquisition channel.
        acq_indices
            Acquisition index.
            If `None`, it has no corresponding acquisition index (for example Trace acquisition).
        thresholded_trigger_count_metadata
            Thresholded trigger count metadata. If not applicable, `None`.
        repetitions
            Repetitions of the schedule when using append bin mode.

        Returns
        -------
            The Qblox acquisition index, and the Qblox acquisition bin offset as integers.

        Raises
        ------
        AcquisitionMemoryError
            When the QbloxAcquisitionBinManager runs out of bins to allocate.

        """
        if isinstance(acq_indices, int):
            acq_indices = [acq_indices]
        if repetitions is None:
            repetitions = 1

        qblox_acq_index: int | None = self._acq_channel_to_qblox_acq_index.get(acq_channel)
        if qblox_acq_index is None:
            qblox_acq_index = self._next_qblox_acq_index_with_all_free_bins()
        else:
            qblox_acq_index = self._acq_channel_to_qblox_acq_index[acq_channel]

        requested_number_of_acq_indices: int = len(acq_indices)

        qblox_acq_bin_offset: int = self._reserve_qblox_acq_bins(
            number_of_acq_indices=requested_number_of_acq_indices,
            qblox_acq_index=qblox_acq_index,
            acq_channel=acq_channel,
            acq_indices=acq_indices,
            thresholded_trigger_count_metadata=thresholded_trigger_count_metadata,
            repetitions=repetitions,
        )
        self._acq_channel_to_qblox_acq_index[acq_channel] = qblox_acq_index

        return qblox_acq_index, qblox_acq_bin_offset

    def allocate_qblox_index(self, acq_channel: Hashable) -> int:
        """
        Allocates a whole Qblox acquisition index for ttl, other acquisition
        for the given acquisition channel.

        Parameters
        ----------
        acq_channel
            Acquisition channel.

        Returns
        -------
            The Qblox acquisition index.

        Raises
        ------
        AcquisitionMemoryError
            When the QbloxAcquisitionBinManager runs out of acquisition indices to allocate.

        """
        if acq_channel in self._acq_channel_to_qblox_acq_index:
            return self._acq_channel_to_qblox_acq_index[acq_channel]

        qblox_acq_index: int = self._next_qblox_acq_index_with_all_free_bins()

        self._reserve_qblox_acq_bins(
            number_of_acq_indices=constants.MAX_NUMBER_OF_RUNTIME_ALLOCATED_QBLOX_ACQ_BINS,
            qblox_acq_index=qblox_acq_index,
            acq_channel=acq_channel,
            acq_indices=None,
            thresholded_trigger_count_metadata=None,
            repetitions=1,
        )
        self._acq_channel_to_qblox_acq_index[acq_channel] = qblox_acq_index

        return qblox_acq_index

    def allocate_trace(self, acq_channel: Hashable) -> tuple[int, int]:
        """
        Allocates a whole Qblox acquisition index for trace
        for the given acquisition channel.

        Parameters
        ----------
        acq_channel
            Acquisition channel.

        Returns
        -------
            The Qblox acquisition index, and the Qblox acquisition bin offset as integers.

        Raises
        ------
        AcquisitionMemoryError
            When the QbloxAcquisitionBinManager runs out of acquisition indices to allocate.

        """
        if acq_channel in self._acq_channel_to_qblox_acq_index:
            return self._acq_channel_to_qblox_acq_index[acq_channel], 0
        elif self._trace_allocated:
            raise AcquisitionMemoryError(
                f"Only one acquisition channel per port-clock can be specified, "
                f"if the 'Trace' acquisition protocol is used. "
                f"Attempted to compile for acquisition channel '{acq_channel}'."
            )

        qblox_acq_index: int = self._next_qblox_acq_index_with_all_free_bins()

        requested_number_of_acq_indices: int = 1

        self._reserve_qblox_acq_bins(
            number_of_acq_indices=requested_number_of_acq_indices,
            qblox_acq_index=qblox_acq_index,
            acq_channel=acq_channel,
            acq_indices=None,
            thresholded_trigger_count_metadata=None,
            repetitions=1,
        )
        self._acq_channel_to_qblox_acq_index[acq_channel] = qblox_acq_index

        self._trace_allocated = True

        return qblox_acq_index, 0

    def allocate_timetagtrace(
        self,
        acq_channel: Hashable,
        acq_indices: list[int],
        repetitions: int,
    ) -> tuple[int, int]:
        """
        Allocates a whole Qblox acquisition index for TimetagTrace
        for the given acquisition channel.

        Parameters
        ----------
        acq_channel
            Acquisition channel.
        acq_indices
            Acquisition index.
        repetitions
            Repetitions of the schedule.

        Returns
        -------
            The Qblox acquisition index, and the Qblox acquisition bin offset as integers.

        Raises
        ------
        AcquisitionMemoryError
            When the QbloxAcquisitionBinManager runs out of acquisition indices to allocate.
        AcquisitionMemoryError
            When there have already been an other trace acquisition allocated.

        """
        if (acq_channel not in self._acq_channel_to_qblox_acq_index) and (
            not self._trace_allocated
        ):
            qblox_acq_index: int = self._next_qblox_acq_index_with_all_free_bins()
        elif acq_channel in self._acq_channel_to_qblox_acq_index:
            qblox_acq_index = self._acq_channel_to_qblox_acq_index[acq_channel]
        else:
            raise AcquisitionMemoryError(
                f"Only one acquisition channel per port-clock can be specified, "
                f"if the 'TimetagTrace' acquisition protocol is used. "
                f"Attempted to compile for acquisition channel '{acq_channel}'."
            )

        requested_number_of_acq_indices: int = len(acq_indices)

        qblox_acq_bin_offset: int = self._reserve_qblox_acq_bins(
            number_of_acq_indices=requested_number_of_acq_indices,
            qblox_acq_index=qblox_acq_index,
            acq_channel=acq_channel,
            acq_indices=acq_indices,
            thresholded_trigger_count_metadata=None,
            repetitions=repetitions,
        )
        self._acq_channel_to_qblox_acq_index[acq_channel] = qblox_acq_index

        self._trace_allocated = True

        return qblox_acq_index, qblox_acq_bin_offset

    def acq_declaration_dict(self) -> dict[str, Any]:
        """
        Returns the acquisition declaration dict, which is needed for the qblox-instruments.
        This data is used in :class:`qblox_instruments.qcodes_drivers.Sequencer`
        `sequence` parameter's `"acquisitions"`.

        Returns
        -------
            The acquisition declaration dict.

        """
        return self._sequencer_acquisition_model.to_acq_declaration_dict()

    def acq_hardware_mapping(
        self,
    ) -> QbloxAcquisitionHardwareMapping:
        """
        Returns the acquisition hardware mapping, which is needed for
        qblox-scheduler instrument coordinator to figure out which hardware index, bin needs
        to be mapped to which output acquisition data.

        Returns
        -------
            The acquisition hardware mapping.

        """
        return QbloxAcquisitionHardwareMapping(
            non_fully_append=self._acq_hardware_mapping_binned
            | self._acq_hardware_mapping_not_binned,
            fully_append=self._acq_hardware_mapping_fully_append,
        )
