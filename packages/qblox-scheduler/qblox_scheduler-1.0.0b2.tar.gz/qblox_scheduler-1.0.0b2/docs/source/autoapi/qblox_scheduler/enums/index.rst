enums
=====

.. py:module:: qblox_scheduler.enums 

.. autoapi-nested-parse::

   Enums for qblox-scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.enums.StrEnum
   qblox_scheduler.enums.BinMode
   qblox_scheduler.enums.TimeSource
   qblox_scheduler.enums.TimeRef
   qblox_scheduler.enums.TriggerCondition
   qblox_scheduler.enums.DualThresholdedTriggerCountLabels
   qblox_scheduler.enums.SchedulingStrategy




.. py:class:: StrEnum

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Enum that can be directly serialized to string.


.. py:class:: BinMode

   Bases: :py:obj:`StrEnum`


   Describes how to handle `Acquisitions` that write to the same `AcquisitionIndex`.

   A BinMode is a property of an `AcquisitionChannel` that describes how to
   handle multiple
   :class:`~qblox_scheduler.operations.acquisition_library.Acquisition` s
   that write data to the same `AcquisitionIndex` on a channel.

   The most common use-case for this is when iterating over multiple
   repetitions of a :class:`~qblox_scheduler.schedules.schedule.TimeableSchedule`
   When the BinMode is set to `APPEND` new entries will be added as a list
   along the `repetitions` dimension.

   When the BinMode is set to `AVERAGE` the outcomes are averaged together
   into one value.

   Note that not all `AcquisitionProtocols` and backends support all possible
   BinModes. For more information, please see the :ref:`sec-acquisition-protocols`
   reference guide and some of the Qblox-specific :ref:`acquisition details
   <sec-qblox-acquisition-details>`.


   .. py:attribute:: APPEND
      :value: 'append'



   .. py:attribute:: AVERAGE
      :value: 'average'



   .. py:attribute:: AVERAGE_APPEND
      :value: 'average_append'


      Averages over the schedule's repetition, appends over loops.


   .. py:attribute:: FIRST
      :value: 'first'



   .. py:attribute:: DISTRIBUTION
      :value: 'distribution'



   .. py:attribute:: SUM
      :value: 'sum'



.. py:class:: TimeSource

   Bases: :py:obj:`StrEnum`


   Selects the timetag data source for timetag (trace) acquisitions.

   See :class:`~qblox_scheduler.operations.acquisition_library.Timetag` and
   :class:`~qblox_scheduler.operations.acquisition_library.TimetagTrace`.


   .. py:attribute:: FIRST
      :value: 'first'



   .. py:attribute:: SECOND
      :value: 'second'



   .. py:attribute:: LAST
      :value: 'last'



.. py:class:: TimeRef

   Bases: :py:obj:`StrEnum`


   Selects the event that counts as a time reference (i.e. t=0) for timetags.

   See :class:`~qblox_scheduler.operations.acquisition_library.Timetag` and
   :class:`~qblox_scheduler.operations.acquisition_library.TimetagTrace`.


   .. py:attribute:: START
      :value: 'start'



   .. py:attribute:: END
      :value: 'end'



   .. py:attribute:: FIRST
      :value: 'first'



   .. py:attribute:: TIMESTAMP
      :value: 'timestamp'



   .. py:attribute:: PORT
      :value: 'port'



.. py:class:: TriggerCondition

   Bases: :py:obj:`StrEnum`


   Comparison condition for the thresholded trigger count acquisition.


   .. py:attribute:: LESS_THAN
      :value: 'less_than'



   .. py:attribute:: GREATER_THAN_EQUAL_TO
      :value: 'greater_than_equal_to'



.. py:class:: DualThresholdedTriggerCountLabels

   Bases: :py:obj:`StrEnum`


   All suffixes for the feedback trigger labels that can be used by
   DualThresholdedTriggerCount.


   .. py:attribute:: LOW
      :value: 'low'



   .. py:attribute:: MID
      :value: 'mid'



   .. py:attribute:: HIGH
      :value: 'high'



   .. py:attribute:: INVALID
      :value: 'invalid'



.. py:class:: SchedulingStrategy

   Bases: :py:obj:`StrEnum`


   Default scheduling strategy to use when no timing constraints are defined.


   .. py:attribute:: ASAP
      :value: 'asap'



   .. py:attribute:: ALAP
      :value: 'alap'



