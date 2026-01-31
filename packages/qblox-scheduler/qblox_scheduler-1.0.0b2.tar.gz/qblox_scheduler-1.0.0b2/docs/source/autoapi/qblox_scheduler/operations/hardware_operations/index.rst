hardware_operations
===================

.. py:module:: qblox_scheduler.operations.hardware_operations 

.. autoapi-nested-parse::

   Hardware specific operations



Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   inline_q1asm/index.rst
   pulse_factories/index.rst
   pulse_library/index.rst


Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.hardware_operations.InlineQ1ASM
   qblox_scheduler.operations.hardware_operations.LatchReset
   qblox_scheduler.operations.hardware_operations.SimpleNumericalPulse



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.hardware_operations.long_chirp_pulse
   qblox_scheduler.operations.hardware_operations.long_ramp_pulse
   qblox_scheduler.operations.hardware_operations.long_square_pulse
   qblox_scheduler.operations.hardware_operations.staircase_pulse



.. py:class:: InlineQ1ASM(program: str, duration: float, port: str, clock: str, *, waveforms: dict | None = None, safe_labels: bool = True)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Initialize an InlineQ1ASM operation.

   This method sets up an operation that contains inline Q1ASM code
    to be injected directly into a Schedule.

   All comments in the program will be prefixed with an '[inline]' prefix
   to help identify the inline assembly within the sequencer program.


   When using safe labels, then all labels included in the input program
   will get a prefix of 'inj<digits>_'.
   By default, safe labels are always used.
   Labels in comments will not be modified.

   :param program: The Q1ASM program to be injected.
   :param duration: The duration of the operation in seconds.
   :param port: The port on which the operation is to be executed.
   :param clock: The clock associated with the operation.
   :param waveforms: Dictionary containing waveform information, by default None.
   :param safe_labels: Flag to indicate if safe labels should be used, by default True.

   :returns: None

   .. rubric:: Notes

   .. warning::

       When using safe_labels=False then all labels in the sequencer program are accessible from
       inside the inline Q1ASM injection, and so can be jumped to or overwritten.  Disabling this
       feature is available for debugging and advanced compilation strategies only.


   .. py:attribute:: _name
      :value: 'InlineQ1ASM'



   .. py:attribute:: program


   .. py:attribute:: _duration


   .. py:attribute:: port


   .. py:attribute:: clock


   .. py:attribute:: waveforms


   .. py:attribute:: safe_labels
      :value: True



   .. py:property:: name
      :type: str


      Return the name of the operation.


   .. py:property:: duration
      :type: float


      The duration of this operation.


   .. py:method:: get_used_port_clocks() -> set[tuple[str, str]]

      Extracts which port-clock combinations are used in this operation.

      :returns: :
                    All (port, clock) combinations this operation uses.




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


.. py:class:: LatchReset(portclock: tuple[str, str], t0: float = 0, duration: float = 4e-09)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Operation that resets the feedback trigger addresses from the hardware.

   Currently only implemented for Qblox backend, refer to
   :class:`~qblox_scheduler.backends.qblox.operation_handling.virtual.ResetFeedbackTriggersStrategy`
   for more details.


.. py:class:: SimpleNumericalPulse(samples: numpy.ndarray | list, port: str, clock: str = BasebandClockResource.IDENTITY, gain: complex | float | operations.expressions.Expression | collections.abc.Sequence[complex | float | operations.expressions.Expression] = 1, reference_magnitude: qblox_scheduler.operations.pulse_library.ReferenceMagnitude | None = None, t0: float = 0)

   Bases: :py:obj:`qblox_scheduler.operations.pulse_library.NumericalPulse`


   Wrapper on top of NumericalPulse to provide a simple interface for creating a pulse
   where the samples correspond 1:1 to the produced waveform, without needing to specify
   the time samples.


   :param samples: An array of (possibly complex) values specifying the shape of the pulse.
   :param port: The port that the pulse should be played on.
   :param clock: Clock used to (de)modulate the pulse.
                 By default the baseband clock.
   :param gain: Gain factor between -1 and 1 that multiplies with the samples, by default 1.
   :param reference_magnitude: Scaling value and unit for the unitless samples. Uses settings in
                               hardware config if not provided.
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule.

   .. rubric:: Example

   .. jupyter-execute::

       from qblox_scheduler.operations.hardware_operations.pulse_library import (
           SimpleNumericalPulse
       )
       from qblox_scheduler import TimeableSchedule

       waveform = [0.1,0.2,0.2,0.3,0.5,0.4]

       schedule = TimeableSchedule("")
       schedule.add(SimpleNumericalPulse(waveform, port="q0:out"))


