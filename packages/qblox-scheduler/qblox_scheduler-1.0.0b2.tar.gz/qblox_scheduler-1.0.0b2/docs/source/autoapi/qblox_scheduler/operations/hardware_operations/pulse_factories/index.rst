pulse_factories
===============

.. py:module:: qblox_scheduler.operations.hardware_operations.pulse_factories 

.. autoapi-nested-parse::

   Module containing factory functions for pulses on the quantum-device layer.

   These factories take a parametrized representation of an operation and create an
   instance of the operation itself. The created operations make use of Qblox-specific
   hardware features.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.hardware_operations.pulse_factories.long_square_pulse
   qblox_scheduler.operations.hardware_operations.pulse_factories.long_chirp_pulse
   qblox_scheduler.operations.hardware_operations.pulse_factories.staircase_pulse
   qblox_scheduler.operations.hardware_operations.pulse_factories.long_ramp_pulse



.. py:function:: long_square_pulse(amp: complex | qblox_scheduler.operations.variables.Variable | collections.abc.Sequence[float | qblox_scheduler.operations.variables.Variable], duration: float, port: str, clock: str = BasebandClockResource.IDENTITY, t0: float = 0, reference_magnitude: qblox_scheduler.operations.pulse_library.ReferenceMagnitude | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Create a long square pulse using DC voltage offsets.

   .. warning::

       This function creates a
       :class:`~qblox_scheduler.schedules.schedule.TimeableSchedule`
       object, containing a combination of voltage offsets and waveforms. Overlapping
       Schedules with VoltageOffsets in time on the same port and clock may lead to unexpected
       results.

   :param amp: Amplitude of the envelope.
   :type amp: float
   :param duration: The pulse duration in seconds.
   :type duration: float
   :param port: Port of the pulse, must be capable of playing a complex waveform.
   :type port: str
   :param clock: Clock used to modulate the pulse. By default the baseband clock.
   :type clock: str, Optional
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule. By default 0.
   :type t0: float, Optional
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :type reference_magnitude: Optional

   :returns: TimeableSchedule
                 A Schedule object containing an offset instruction with the specified
                 amplitude.

   :raises ValueError: When the duration of the pulse is not a multiple of ``grid_time_ns``.


.. py:function:: long_chirp_pulse(amp: float, duration: float, port: str, start_freq: float, end_freq: float, clock: str = BasebandClockResource.IDENTITY, t0: float = 0, part_duration_ns: int = constants.STITCHED_PULSE_PART_DURATION_NS, reference_magnitude: qblox_scheduler.operations.pulse_library.ReferenceMagnitude | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Create a long chirp pulse using SetClockFrequency.

   :param amp: Amplitude of the envelope.
   :type amp: float
   :param duration: The pulse duration in seconds.
   :type duration: float
   :param port: Port of the pulse, must be capable of playing a complex waveform.
   :type port: str
   :param start_freq: Start frequency of the Chirp. Note that this is the frequency at which the
                      waveform is calculated, this may differ from the clock frequency.
   :type start_freq: float
   :param end_freq: End frequency of the Chirp.
   :type end_freq: float
   :param clock: Clock used to modulate the pulse. By default the baseband clock.
   :type clock: str, Optional
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule. By default 0.
   :type t0: float, Optional
   :param part_duration_ns: Chunk size in nanoseconds.
   :type part_duration_ns: int, Optional
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :type reference_magnitude: Optional

   :returns: TimeableSchedule
                 A TimeableSchedule object describing a chirp pulse.

   :raises ValueError: When the duration of the pulse is not a multiple of ``grid_time_ns``.


.. py:function:: staircase_pulse(start_amp: float, final_amp: float, num_steps: int, duration: float, port: str, clock: str = BasebandClockResource.IDENTITY, t0: float = 0, min_operation_time_ns: int = constants.MIN_TIME_BETWEEN_OPERATIONS, reference_magnitude: qblox_scheduler.operations.pulse_library.ReferenceMagnitude | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Create a staircase-shaped pulse using DC voltage offsets.

   This function generates a real valued staircase pulse, which reaches its final
   amplitude in discrete steps. In between it will maintain a plateau.

   .. warning::

       This function creates a
       :class:`~qblox_scheduler.schedules.schedule.TimeableSchedule`
       object, containing a combination of voltage offsets and waveforms. Overlapping
       Schedules with VoltageOffsets in time on the same port and clock may lead to unexpected
       results.

   :param start_amp: Starting amplitude of the staircase envelope function.
   :type start_amp: float
   :param final_amp: Final amplitude of the staircase envelope function.
   :type final_amp: float
   :param num_steps: The number of plateaus.
   :type num_steps: int
   :param duration: Duration of the pulse in seconds.
   :type duration: float
   :param port: Port of the pulse.
   :type port: str
   :param clock: Clock used to modulate the pulse. By default the baseband clock.
   :type clock: str, Optional
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule. By default 0.
   :type t0: float, Optional
   :param min_operation_time_ns: Min operation time in ns. The duration of the long_square_pulse must be a multiple
                                 of this. By default equal to the min operation time time of Qblox modules.
   :type min_operation_time_ns: int, Optional
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :type reference_magnitude: Optional

   :returns: TimeableSchedule
                 A Schedule object containing incrementing or decrementing offset
                 instructions.

   :raises ValueError: When the duration of a step is not a multiple of ``grid_time_ns``.


.. py:function:: long_ramp_pulse(amp: float, duration: float, port: str, offset: float = 0, clock: str = BasebandClockResource.IDENTITY, t0: float = 0, part_duration_ns: int = constants.STITCHED_PULSE_PART_DURATION_NS, reference_magnitude: qblox_scheduler.operations.pulse_library.ReferenceMagnitude | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Creates a long ramp pulse by stitching together shorter ramps.

   This function creates a long ramp pulse by stitching together ramp pulses of the
   specified duration ``part_duration_ns``, with DC voltage offset instructions placed
   in between.

   .. warning::

       This function creates a
       :class:`~qblox_scheduler.schedules.schedule.TimeableSchedule`
       object, containing a combination of voltage offsets and waveforms. Overlapping
       Schedules with VoltageOffsets in time on the same port and clock may lead to unexpected
       results.

   :param amp: Amplitude of the ramp envelope function.
   :type amp: float
   :param duration: The pulse duration in seconds.
   :type duration: float
   :param port: Port of the pulse.
   :type port: str
   :param offset: Starting point of the ramp pulse. By default 0.
   :type offset: float, Optional
   :param clock: Clock used to modulate the pulse, by default the baseband clock.
   :type clock: str, Optional
   :param t0: Time in seconds when to start the pulses relative to the start time of the
              Operation in the TimeableSchedule. By default 0.
   :type t0: float, Optional
   :param part_duration_ns: Duration of each partial ramp in nanoseconds, by default
                            :class:`~qblox_scheduler.backends.qblox.constants.STITCHED_PULSE_PART_DURATION_NS`.
   :type part_duration_ns: int, Optional
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :type reference_magnitude: Optional

   :returns: TimeableSchedule
                 A ``TimeableSchedule`` composed of shorter ramp pulses with varying DC offsets,
                 forming one long ramp pulse.



