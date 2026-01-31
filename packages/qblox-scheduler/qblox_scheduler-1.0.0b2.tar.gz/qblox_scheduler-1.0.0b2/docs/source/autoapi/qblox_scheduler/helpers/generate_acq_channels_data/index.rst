generate_acq_channels_data
==========================

.. py:module:: qblox_scheduler.helpers.generate_acq_channels_data 

.. autoapi-nested-parse::

   Helper functions to generate acq_indices.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.helpers.generate_acq_channels_data.AcquisitionIndices
   qblox_scheduler.helpers.generate_acq_channels_data.LoopData



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.helpers.generate_acq_channels_data._evaluate_coords_recursively
   qblox_scheduler.helpers.generate_acq_channels_data._evaluate_coords
   qblox_scheduler.helpers.generate_acq_channels_data._get_loops_with_append_bin_mode_and_all_loop_bin_modes
   qblox_scheduler.helpers.generate_acq_channels_data._generate_acq_channels_data_binned_average
   qblox_scheduler.helpers.generate_acq_channels_data._generate_acq_channels_data_binned_append
   qblox_scheduler.helpers.generate_acq_channels_data._validate_trace_protocol
   qblox_scheduler.helpers.generate_acq_channels_data._generate_acq_channels_data_for_protocol
   qblox_scheduler.helpers.generate_acq_channels_data._generate_acq_channels_data
   qblox_scheduler.helpers.generate_acq_channels_data._verify_shared_coords_key
   qblox_scheduler.helpers.generate_acq_channels_data.generate_acq_channels_data



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.helpers.generate_acq_channels_data.SchedulableLabel
   qblox_scheduler.helpers.generate_acq_channels_data.FullSchedulableLabel
   qblox_scheduler.helpers.generate_acq_channels_data.SchedulableLabelToAcquisitionIndex


.. py:data:: SchedulableLabel

.. py:data:: FullSchedulableLabel

.. py:class:: AcquisitionIndices

   The AcquisitionIndices is just
   (acq_index_offset, loop_bin_modes=None, number_of_acq_indices=1)
   for acquisitions outside of loops,
   but if the acquisition is inside a nested loop,
   the `loop_bin_modes` lists whether the acquisition is averaged or looped for each loop level.
   For example, if you have a multi-dimensional with 2, 3 and 4 repetitions,
   and you average over the last nested level,
   `loop_bin_modes=[APPEND, APPEND, AVERAGE]`, and `number_of_acq_indices=2*3`.


   .. py:attribute:: acq_index_offset
      :type:  int


   .. py:attribute:: loop_bin_modes
      :type:  list[qblox_scheduler.enums.BinMode] | None


   .. py:attribute:: number_of_acq_indices
      :type:  int


   .. py:property:: acq_index
      :type: list[int] | int


      Acquisition index as a number if there are no loops,
      otherwise the list of all the acquisition indices.


.. py:data:: SchedulableLabelToAcquisitionIndex

   A mapping from schedulables to an acquisition index.

   This mapping helps the backend to figure out which
   binned acquisition corresponds to which acquisition index.
   Note, it maps the full schedulable label to acquisition indices,
   Only defined for binned acquisitions, and backend independent.

   For control flows, the `None` in the schedulable label refers to the `body`
   of the control flow. This is for future proofing, if control flows were extended
   to include maybe multiple suboperations.

.. py:class:: LoopData

   Data to contain relevant information from LoopOperation.


   .. py:attribute:: repetitions
      :type:  int


   .. py:attribute:: domain
      :type:  dict[qblox_scheduler.operations.variables.Variable, qblox_scheduler.operations.loop_domains.Domain] | None


.. py:function:: _evaluate_coords_recursively(loops: list[LoopData], evaluated_coords: list[dict]) -> list[dict]

   Evaluate coords even if there are variables in it.
   The accumulator is stored in evaluated_coords, which is returned.


.. py:function:: _evaluate_coords(coords: dict, loops: list[LoopData]) -> list[dict]

   Evaluate coords even if there are variables in it.


.. py:function:: _get_loops_with_append_bin_mode_and_all_loop_bin_modes(coords: dict, loops: list[LoopData], append_all_loops: bool) -> tuple[list[LoopData], list[qblox_scheduler.enums.BinMode]]

.. py:function:: _generate_acq_channels_data_binned_average(acq_channel_data: qblox_scheduler.schedules.schedule.AcquisitionChannelData, schedulable_label_to_acq_index: SchedulableLabelToAcquisitionIndex, full_schedulable_label: FullSchedulableLabel, coords: dict, acq_channel: collections.abc.Hashable, acq_index: int | None) -> None

   Generates the acquisition channel data, and updates acq_channel_data,
   and updates schedulable_label_to_acq_index for average bin mode.


.. py:function:: _generate_acq_channels_data_binned_append(acq_channel_data: qblox_scheduler.schedules.schedule.AcquisitionChannelData, schedulable_label_to_acq_index: SchedulableLabelToAcquisitionIndex, full_schedulable_label: FullSchedulableLabel, loops: list[LoopData], coords: dict, acq_channel: collections.abc.Hashable, acq_index: int | None, append_all_loops: bool) -> None

   Generates the acquisition channel data, and updates acq_channel_data,
   and updates schedulable_label_to_acq_index for average bin mode.


.. py:function:: _validate_trace_protocol(acq_channel: collections.abc.Hashable, acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, loops: list[LoopData]) -> None

.. py:function:: _generate_acq_channels_data_for_protocol(acq_info: dict, acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, schedulable_label_to_acq_index: SchedulableLabelToAcquisitionIndex, full_schedulable_label: FullSchedulableLabel, loops: list[LoopData], is_explicit_acq_index: bool) -> None

   Generates the acquisition channel data, and updates acq_channel_data,
   and updates schedulable_label_to_acq_index.


.. py:function:: _generate_acq_channels_data(operation: qblox_scheduler.schedules.schedule.TimeableScheduleBase | qblox_scheduler.operations.operation.Operation, acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData, schedulable_label_to_acq_index: SchedulableLabelToAcquisitionIndex, is_explicit_acq_index: bool, full_schedulable_label: FullSchedulableLabel, loops: list[LoopData]) -> None

   Adds mappings to acq_channels_data and schedulable_label_to_acq_index;
   these are the output arguments; the others are input arguments.
   If explicit_acq_indices is True,
   then it only adds Schedulables where acq_index is not None,
   otherwise only adds Schedulables where acq_index is None.
   In this latter case, it will generate the acq_index.


.. py:function:: _verify_shared_coords_key(acq_channels_data: qblox_scheduler.schedules.schedule.AcquisitionChannelsData) -> None

   Checks if any two acquisition channels share the same coords keys.
   This is unsupported currently, see https://gitlab.com/quantify-os/quantify-scheduler/-/issues/497.


.. py:function:: generate_acq_channels_data(schedule: qblox_scheduler.schedules.schedule.TimeableScheduleBase) -> tuple[qblox_scheduler.schedules.schedule.AcquisitionChannelsData, SchedulableLabelToAcquisitionIndex]

   Generate acq_index for every schedulable,
   and validate schedule regarding the acquisitions.

   This function generates the ``AcquisitionChannelData`` for every ``acq_channel``,
   and the ``SchedulableLabelToAcquisitionIndex``. It assumes the schedule is device-level.


