qblox_acq_index_manager
=======================

.. py:module:: qblox_scheduler.backends.qblox.qblox_acq_index_manager 

.. autoapi-nested-parse::

   Utility class for dynamically allocating
   Qblox acquisition indices and bins and for Qblox sequencers.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionIndexBin
   qblox_scheduler.backends.qblox.qblox_acq_index_manager.FullyAppendAcqInfo
   qblox_scheduler.backends.qblox.qblox_acq_index_manager.AcqFullyAppendLoopNode
   qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionBinMappingFullyAppend
   qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMapping
   qblox_scheduler.backends.qblox.qblox_acq_index_manager._SequencerAcquisitionModel
   qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionIndexManager




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionIndex
   qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionBinMapping
   qblox_scheduler.backends.qblox.qblox_acq_index_manager.QbloxAcquisitionHardwareMappingNonFullyAppend


.. py:data:: QbloxAcquisitionIndex

.. py:class:: QbloxAcquisitionIndexBin

   Qblox acquisition index and QBlox acquisition bin.


   .. py:attribute:: index
      :type:  QbloxAcquisitionIndex

      Qblox acquisition index.


   .. py:attribute:: bin
      :type:  int

      Qblox acquisition bin.
      For average bin mode, this is the bin where the data is stored.
      For append bin mode, this is first bin where data is stored,
      for each loop and repetition cycle, the data is consecutively stored.


   .. py:attribute:: stride
      :type:  int

      Stride.
      Only used for acquisitions within a loop (not schedule repetitions).
      Defines what's the stride between each repetitions of the schedule for the data.

      The assumption is that for an append bin mode operation
      with loops and schedule repetitions there is only one register;
      the register's inner iteration first goes through the loop,
      and then the schedule repetitions.


   .. py:attribute:: thresholded_trigger_count_metadata
      :type:  qblox_scheduler.backends.types.common.ThresholdedTriggerCountMetadata | None

      Thresholded trigger count metadata.
      Only applicable for ThresholdedTriggerCount,
      and only on QRM, QRM-RF, QRC.
      On QTM, this is unused, threshold calculations are on the hardware.


.. py:data:: QbloxAcquisitionBinMapping

   Binned type acquisition hardware mapping.

   Each value maps the acquisition index to a hardware bin,
   which is specified by the Qblox acquisition index, and the Qblox acquisition bin.

.. py:data:: QbloxAcquisitionHardwareMappingNonFullyAppend

   Type for all non-fully append type acquisition hardware mapping.

   This is a union of types, because the exact mapping type depends on the protocol.

.. py:class:: FullyAppendAcqInfo

   Acquisition info for fully append acquisition.


   .. py:attribute:: acq_channel
      :type:  collections.abc.Hashable


   .. py:attribute:: acq_index
      :type:  qblox_scheduler.helpers.generate_acq_channels_data.AcquisitionIndices


   .. py:attribute:: thresholded_trigger_count_metadata
      :type:  qblox_scheduler.backends.types.common.ThresholdedTriggerCountMetadata | None


.. py:class:: AcqFullyAppendLoopNode

   Node to represent all acquisitions which are within the same loop tree structure.


   .. py:attribute:: parent
      :type:  AcqFullyAppendLoopNode | None


   .. py:attribute:: children
      :type:  list[AcqFullyAppendLoopNode | FullyAppendAcqInfo]


   .. py:attribute:: repetitions
      :type:  int | None


   .. py:attribute:: bin_mode
      :type:  qblox_scheduler.enums.BinMode | None


   .. py:method:: add_control_flow_child(child_repetitions: int | None, bin_mode: qblox_scheduler.enums.BinMode | None) -> AcqFullyAppendLoopNode

      Adds a new control flow as a child to the current node,
      and returns it.



   .. py:method:: return_control_flow_child() -> AcqFullyAppendLoopNode

      Returns the parent, and
      if the current node is empty, it will remove it from the tree.
      Only call this function after any add_control_flow_child was called.



.. py:class:: QbloxAcquisitionBinMappingFullyAppend

   Binned type acquisition hardware mapping for acquisitions
   that are fully appended for all loop levels.


   .. py:attribute:: qblox_acq_index
      :type:  QbloxAcquisitionIndex


   .. py:attribute:: qblox_acq_bin_offset
      :type:  int

      The starting bin where all acquisition data is stored for this mapping.


   .. py:attribute:: tree
      :type:  AcqFullyAppendLoopNode

      Root node for the whole tree of the loop and acquisition tree.


.. py:class:: QbloxAcquisitionHardwareMapping

   Acquisition hardware mapping for all acquisitions.


   .. py:attribute:: non_fully_append
      :type:  dict[collections.abc.Hashable, QbloxAcquisitionHardwareMappingNonFullyAppend]


   .. py:attribute:: fully_append
      :type:  list[QbloxAcquisitionBinMappingFullyAppend]


.. py:exception:: AcquisitionMemoryError

   Bases: :py:obj:`ValueError`


   Raised when there is an error in allocating acquisition memory.


.. py:class:: _SequencerAcquisitionModel(maximum_qblox_acq_indices: int = constants.NUMBER_OF_QBLOX_ACQ_INDICES, maximum_bins: int = constants.MAX_NUMBER_OF_BINS)

   .. py:attribute:: _num_bins
      :type:  list[int]
      :value: []



   .. py:attribute:: _maximum_qblox_acq_indices
      :value: 32



   .. py:attribute:: _maximum_bins
      :value: 131072



   .. py:property:: total_remaining_free_bins
      :type: int



   .. py:method:: reserve_new_qblox_acq_index(num_bins: int = 0) -> int


   .. py:method:: reserve_bins(qblox_acq_index: int, num_bins: int) -> None


   .. py:method:: next_free_bin_index(qblox_acq_index: int) -> int

      The next free bin for this Qblox acquisition index. Equal to the total amount of
      reserved bins for this Qblox acquisition index.



   .. py:method:: to_acq_declaration_dict() -> dict[str, Any]

      Acquisition declaration dictionary.

      This data is used in :class:`qblox_instruments.qcodes_drivers.Sequencer`
      `sequence` parameter's `"acquisitions"`.



.. py:class:: QbloxAcquisitionIndexManager

   Utility class that keeps track of all the reserved indices, bins for a sequencer.

   Each acquisition channel is mapped to a unique Qblox acquisition index.
   For binned acquisitions, each new allocation request reserves
   the Qblox acquisition bins in order (incrementing the bin index by one).
   For trace and ttl and other acquisitions, the whole Qblox acquisition index is reserved,
   there, the bin index has no relevance.


   .. py:attribute:: _acq_hardware_mapping_binned
      :type:  dict[collections.abc.Hashable, QbloxAcquisitionBinMapping]

      Acquisition hardware mapping for binned acquisitions.


   .. py:attribute:: _acq_hardware_mapping_not_binned
      :type:  dict[collections.abc.Hashable, QbloxAcquisitionIndex]

      Acquisition hardware mapping for not binned acquisitions.


   .. py:attribute:: _sequencer_acquisition_model

      Data model of sequencer acquisition memory, which keeps track of the allocated
      amount of bins for each Qblox acquisition index.


   .. py:attribute:: _acq_channel_to_qblox_acq_index
      :type:  dict[collections.abc.Hashable, int]

      Maps each acquisition channel to the
      Qblox acquisition index it uses.


   .. py:attribute:: _fully_append_qblox_acq_index
      :type:  int | None
      :value: None


      Qblox acquisition index used by the fully append mode acquisitions.


   .. py:attribute:: _trace_allocated
      :type:  bool
      :value: False


      Specifying whether a Trace or TimetagTrace have already been allocated.


   .. py:attribute:: _acq_hardware_mapping_fully_append
      :type:  list[QbloxAcquisitionBinMappingFullyAppend]
      :value: []



   .. py:method:: _number_of_free_qblox_bins() -> int


   .. py:method:: _next_qblox_acq_index_with_all_free_bins() -> int


   .. py:method:: _reserve_qblox_acq_bins_fully_append(number_of_acq_indices: int, qblox_acq_index: int, tree: AcqFullyAppendLoopNode, repetitions: int) -> int


   .. py:method:: allocate_bins_fully_append(number_of_acq_indices: int, tree: AcqFullyAppendLoopNode, repetitions: int | None) -> tuple[int, int]

      Allocates Qblox acquisition bins for acquisitions
      which needs to be fully appended for all loop levels.

      :param number_of_acq_indices: Number of acquisition indices to allocate.
      :param tree: The loop tree structure for all of the acquisitions.
      :param repetitions: Repetitions of the schedule when using append bin mode.

      :returns: The Qblox acquisition index, and the Qblox acquisition bin offset as integers.

      :raises AcquisitionMemoryError: When the QbloxAcquisitionBinManager runs out of bins to allocate.



   .. py:method:: _reserve_qblox_acq_bins(number_of_acq_indices: int, qblox_acq_index: int, acq_channel: collections.abc.Hashable, acq_indices: list[int] | None, thresholded_trigger_count_metadata: qblox_scheduler.backends.types.common.ThresholdedTriggerCountMetadata | None, repetitions: int) -> int

      Reserves the Qblox acquisition bin with the parameters.
      This function already assumes that the bin is free, not yet used.

      Note, `number_of_acq_indices` must be equal to the length of `acq_indices` if not `None`.

      :param number_of_acq_indices: Number of acquisition indices to reserve.
      :param qblox_acq_index: Qblox acquisition index to be used.
      :param acq_channel: Acquisition channel.
      :param acq_indices: Acquisition index.
                          If `None`, it has no corresponding acquisition index (for example Trace acquisition).
      :param thresholded_trigger_count_metadata: Thresholded trigger count metadata. If not applicable, `None`.
      :param repetitions: Repetitions of the schedule for append bin mode; otherwise 1.

      :returns: The starting Qblox acquisition bin.




   .. py:method:: allocate_bins(acq_channel: collections.abc.Hashable, acq_indices: list[int] | int, thresholded_trigger_count_metadata: qblox_scheduler.backends.types.common.ThresholdedTriggerCountMetadata | None, repetitions: int | None) -> tuple[int, int]

      Allocates len(acq_indices) number of Qblox acquisition bins.

      :param acq_channel: Acquisition channel.
      :param acq_indices: Acquisition index.
                          If `None`, it has no corresponding acquisition index (for example Trace acquisition).
      :param thresholded_trigger_count_metadata: Thresholded trigger count metadata. If not applicable, `None`.
      :param repetitions: Repetitions of the schedule when using append bin mode.

      :returns: The Qblox acquisition index, and the Qblox acquisition bin offset as integers.

      :raises AcquisitionMemoryError: When the QbloxAcquisitionBinManager runs out of bins to allocate.



   .. py:method:: allocate_qblox_index(acq_channel: collections.abc.Hashable) -> int

      Allocates a whole Qblox acquisition index for ttl, other acquisition
      for the given acquisition channel.

      :param acq_channel: Acquisition channel.

      :returns: The Qblox acquisition index.

      :raises AcquisitionMemoryError: When the QbloxAcquisitionBinManager runs out of acquisition indices to allocate.



   .. py:method:: allocate_trace(acq_channel: collections.abc.Hashable) -> tuple[int, int]

      Allocates a whole Qblox acquisition index for trace
      for the given acquisition channel.

      :param acq_channel: Acquisition channel.

      :returns: The Qblox acquisition index, and the Qblox acquisition bin offset as integers.

      :raises AcquisitionMemoryError: When the QbloxAcquisitionBinManager runs out of acquisition indices to allocate.



   .. py:method:: allocate_timetagtrace(acq_channel: collections.abc.Hashable, acq_indices: list[int], repetitions: int) -> tuple[int, int]

      Allocates a whole Qblox acquisition index for TimetagTrace
      for the given acquisition channel.

      :param acq_channel: Acquisition channel.
      :param acq_indices: Acquisition index.
      :param repetitions: Repetitions of the schedule.

      :returns: The Qblox acquisition index, and the Qblox acquisition bin offset as integers.

      :raises AcquisitionMemoryError: When the QbloxAcquisitionBinManager runs out of acquisition indices to allocate.
      :raises AcquisitionMemoryError: When there have already been an other trace acquisition allocated.



   .. py:method:: acq_declaration_dict() -> dict[str, Any]

      Returns the acquisition declaration dict, which is needed for the qblox-instruments.
      This data is used in :class:`qblox_instruments.qcodes_drivers.Sequencer`
      `sequence` parameter's `"acquisitions"`.

      :returns: The acquisition declaration dict.




   .. py:method:: acq_hardware_mapping() -> QbloxAcquisitionHardwareMapping

      Returns the acquisition hardware mapping, which is needed for
      qblox-scheduler instrument coordinator to figure out which hardware index, bin needs
      to be mapped to which output acquisition data.

      :returns: The acquisition hardware mapping.




