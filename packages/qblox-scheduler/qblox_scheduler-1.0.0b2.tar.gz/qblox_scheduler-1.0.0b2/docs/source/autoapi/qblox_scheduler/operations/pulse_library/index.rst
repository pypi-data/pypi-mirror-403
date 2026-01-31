pulse_library
=============

.. py:module:: qblox_scheduler.operations.pulse_library 

.. autoapi-nested-parse::

   Standard pulse-level operations for use with the qblox_scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.pulse_library.ReferenceMagnitude
   qblox_scheduler.operations.pulse_library.ShiftClockPhase
   qblox_scheduler.operations.pulse_library.ResetClockPhase
   qblox_scheduler.operations.pulse_library.SetClockFrequency
   qblox_scheduler.operations.pulse_library.VoltageOffset
   qblox_scheduler.operations.pulse_library.IdlePulse
   qblox_scheduler.operations.pulse_library.RampPulse
   qblox_scheduler.operations.pulse_library.StaircasePulse
   qblox_scheduler.operations.pulse_library.MarkerPulse
   qblox_scheduler.operations.pulse_library.SquarePulse
   qblox_scheduler.operations.pulse_library.SuddenNetZeroPulse
   qblox_scheduler.operations.pulse_library.SoftSquarePulse
   qblox_scheduler.operations.pulse_library.ChirpPulse
   qblox_scheduler.operations.pulse_library.DRAGPulse
   qblox_scheduler.operations.pulse_library.GaussPulse
   qblox_scheduler.operations.pulse_library.WindowOperation
   qblox_scheduler.operations.pulse_library.NumericalPulse
   qblox_scheduler.operations.pulse_library.SkewedHermitePulse
   qblox_scheduler.operations.pulse_library.Timestamp



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.pulse_library.decompose_long_square_pulse
   qblox_scheduler.operations.pulse_library.create_dc_compensation_pulse



.. py:class:: ReferenceMagnitude

   Dataclass defining a reference level for pulse amplitudes in units of 'V', 'dBm', or 'A'.

   TODO: Deprecate?


   .. py:attribute:: value
      :type:  float


   .. py:attribute:: unit
      :type:  Literal['V', 'dBm', 'A']


   .. py:method:: from_parameter(parameter: qblox_scheduler.device_under_test.transmon_element.ReferenceMagnitude | None) -> ReferenceMagnitude | None
      :classmethod:


      Initialize from ReferenceMagnitude QCoDeS InstrumentChannel values.



.. py:class:: ShiftClockPhase(phase_shift: float | qblox_scheduler.operations.expressions.Expression, clock: str, t0: float | qblox_scheduler.operations.expressions.Expression = 0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Operation that shifts the phase of a clock by a specified amount.

   This is a low-level operation and therefore depends on the backend.

   Currently only implemented for Qblox backend, refer to
   :class:`~qblox_scheduler.backends.qblox.operation_handling.virtual.NcoPhaseShiftStrategy`
   for more details.

   :param phase_shift: The phase shift in degrees.
   :param clock: The clock of which to shift the phase.
   :param t0: Time in seconds when to execute the command relative
              to the start time of the Operation in the TimeableSchedule.


.. py:class:: ResetClockPhase(clock: str, t0: float | qblox_scheduler.operations.expressions.Expression = 0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   An operation that resets the phase of a clock.

   :param clock: The clock of which to reset the phase.


.. py:class:: SetClockFrequency(clock: str, clock_freq_new: float | qblox_scheduler.operations.expressions.Expression | None, t0: float | qblox_scheduler.operations.expressions.Expression = 0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Operation that sets updates the frequency of a clock.

   This is a low-level operation and therefore depends on the backend.

   Currently only implemented for Qblox backend, refer to
   :class:`~qblox_scheduler.backends.qblox.operation_handling.virtual.NcoSetClockFrequencyStrategy`
   for more details.

   :param clock: The clock for which a new frequency is to be set.
   :param clock_freq_new: The new frequency in Hz.
                          If None, it will reset to the clock frequency set by the configuration or resource.
   :param t0: Time in seconds when to execute the command relative to the start time of
              the Operation in the TimeableSchedule.


.. py:class:: VoltageOffset(offset_path_I: float | qblox_scheduler.operations.expressions.Expression, offset_path_Q: float | qblox_scheduler.operations.expressions.Expression, port: str, clock: str = BasebandClockResource.IDENTITY, t0: float | qblox_scheduler.operations.expressions.Expression = 0, reference_magnitude: ReferenceMagnitude | None = None)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Operation that represents setting a constant offset to the output voltage.

   Please refer to :ref:`sec-qblox-offsets-long-voltage-offsets` in the reference guide
   for more details.

   :param offset_path_I: Offset of path I.
   :type offset_path_I: float
   :param offset_path_Q: Offset of path Q.
   :type offset_path_Q: float
   :param port: Port of the voltage offset.
   :type port: str
   :param clock: Clock used to modulate the voltage offset.
                 By default the baseband clock.
   :type clock: str, Optional
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule.
   :type t0: float, Optional
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.


.. py:class:: IdlePulse(duration: float | qblox_scheduler.operations.expressions.Expression)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   The IdlePulse Operation is a placeholder for a specified duration of time.

   :param duration: The duration of idle time in seconds.


.. py:class:: RampPulse(amp: float | qblox_scheduler.operations.expressions.Expression, duration: float | qblox_scheduler.operations.expressions.Expression, port: str, clock: str = BasebandClockResource.IDENTITY, reference_magnitude: ReferenceMagnitude | None = None, offset: float | qblox_scheduler.operations.expressions.Expression = 0, t0: float | qblox_scheduler.operations.expressions.Expression = 0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   RampPulse Operation is a pulse that ramps from zero to a set amplitude over its duration.

   The pulse is given as a function of time :math:`t` and the parameters offset and
   amplitude by

   .. math::

       P(t) = \mathrm{offset} + t \times \frac{\mathrm{amp}}{\mathrm{duration}}

   :param amp: Unitless amplitude of the ramp envelope function.
   :param duration: The pulse duration in seconds.
   :param offset: Starting point of the ramp pulse
   :param port: Port of the pulse.
   :param clock: Clock used to modulate the pulse.
                 By default the baseband clock.
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :param t0: Time in seconds when to start the pulses relative
              to the start time
              of the Operation in the TimeableSchedule.


.. py:class:: StaircasePulse(start_amp: float | qblox_scheduler.operations.expressions.Expression, final_amp: float | qblox_scheduler.operations.expressions.Expression, num_steps: int, duration: float | qblox_scheduler.operations.expressions.Expression, port: str, clock: str = BasebandClockResource.IDENTITY, reference_magnitude: ReferenceMagnitude | None = None, t0: float | qblox_scheduler.operations.expressions.Expression = 0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   A real valued staircase pulse, which reaches it's final amplitude in discrete steps.

   In between it will maintain a plateau.

   :param start_amp: Starting unitless amplitude of the staircase envelope function.
   :param final_amp: Final unitless amplitude of the staircase envelope function.
   :param num_steps: The number of plateaus.
   :param duration: Duration of the pulse in seconds.
   :param port: Port of the pulse.
   :param clock: Clock used to modulate the pulse.
                 By default the baseband clock.
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule.


.. py:class:: MarkerPulse(duration: float | qblox_scheduler.operations.expressions.Expression, port: str, t0: float | qblox_scheduler.operations.expressions.Expression = 0, clock: str = DigitalClockResource.IDENTITY, fine_start_delay: float | qblox_scheduler.operations.expressions.Expression = 0, fine_end_delay: float | qblox_scheduler.operations.expressions.Expression = 0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Digital pulse that is HIGH for the specified duration.

   Marker pulse is played on marker output. Currently only implemented for Qblox
   backend.

   :param duration: Duration of the HIGH signal.
   :param port: Name of the associated port.
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule.
   :param clock: Name of the associated clock. By default
                 :class:`~qblox_scheduler.resources.DigitalClockResource`. This only needs to
                 be specified if a custom clock name is used for a digital channel (for example,
                 when a port-clock combination of a device element is used with a digital
                 channel).
   :param fine_start_delay: Delays the start of the pulse by the given amount in seconds. Does not
                            delay the start time of the operation in the schedule. If the hardware
                            supports it, this parameter can be used to shift the pulse by a small
                            amount of time, independent of the hardware instruction timing grid.
                            Currently only implemented for Qblox QTM modules, which allow only
                            positive values for this parameter. By default 0.
   :param fine_end_delay: Delays the end of the pulse by the given amount in seconds. Does not
                          delay the end time of the operation in the schedule. If the hardware
                          supports it, this parameter can be used to shift the pulse by a small
                          amount of time, independent of the hardware instruction timing grid.
                          Currently only implemented for Qblox QTM modules, which allow only
                          positive values for this parameter. By default 0.


.. py:class:: SquarePulse(amp: complex | float | qblox_scheduler.operations.expressions.Expression | collections.abc.Sequence[complex | float | qblox_scheduler.operations.expressions.Expression], duration: complex | float | qblox_scheduler.operations.expressions.Expression, port: str, clock: str = BasebandClockResource.IDENTITY, reference_magnitude: ReferenceMagnitude | None = None, t0: float | qblox_scheduler.operations.expressions.Expression = 0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   A real-valued pulse with the specified amplitude during the pulse.

   :param amp: Unitless complex valued amplitude of the envelope.
   :param duration: The pulse duration in seconds.
   :param port: Port of the pulse, must be capable of playing a complex waveform.
   :param clock: Clock used to modulate the pulse.
                 By default the baseband clock.
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule.


.. py:class:: SuddenNetZeroPulse(amp_A: float | qblox_scheduler.operations.expressions.Expression, amp_B: float | qblox_scheduler.operations.expressions.Expression, net_zero_A_scale: float | qblox_scheduler.operations.expressions.Expression, t_pulse: float | qblox_scheduler.operations.expressions.Expression, t_phi: float | qblox_scheduler.operations.expressions.Expression, t_integral_correction: float | qblox_scheduler.operations.expressions.Expression, port: str, clock: str = BasebandClockResource.IDENTITY, reference_magnitude: ReferenceMagnitude | None = None, t0: float | qblox_scheduler.operations.expressions.Expression = 0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   A pulse that can be used to implement a conditional phase gate in transmon device elements.

   The sudden net-zero (SNZ) pulse is defined in
   :cite:t:`negirneac_high_fidelity_2021`.

   :param amp_A: Unitless amplitude of the main square pulse.
   :param amp_B: Unitless scaling correction for the final sample of the first square and first
                 sample of the second square pulse.
   :param net_zero_A_scale: Amplitude scaling correction factor of the negative arm of the net-zero
                            pulse.
   :param t_pulse: The total duration of the two half square pulses
   :param t_phi: The idling duration between the two half pulses
   :param t_integral_correction: The duration in which any non-zero pulse amplitude needs to be corrected.
   :param port: Port of the pulse, must be capable of playing a complex waveform.
   :param clock: Clock used to modulate the pulse.
                 By default the baseband clock.
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule.


.. py:function:: decompose_long_square_pulse(duration: float, duration_max: float, single_duration: bool = False, **kwargs) -> list

   Generates a list of square pulses equivalent to a (very) long square pulse.

   Intended to be used for waveform-memory-limited devices. Effectively, only two
   square pulses, at most, will be needed: a main one of duration ``duration_max`` and
   a second one for potential mismatch between N ``duration_max`` and overall `duration`.

   :param duration: Duration of the long pulse in seconds.
   :param duration_max: Maximum duration of square pulses to be generated in seconds.
   :param single_duration: If ``True``, only square pulses of duration ``duration_max`` will be generated.
                           If ``False``, a square pulse of ``duration`` < ``duration_max`` might be generated if
                           necessary.
   :param \*\*kwargs: Other keyword arguments to be passed to the :class:`~SquarePulse`.

   :returns: :
                 A list of :class`SquarePulse` s equivalent to the desired long pulse.



.. py:class:: SoftSquarePulse(amp: float | qblox_scheduler.operations.expressions.Expression | collections.abc.Sequence[float | qblox_scheduler.operations.expressions.Expression], duration: float | qblox_scheduler.operations.expressions.Expression, port: str, clock: str = BasebandClockResource.IDENTITY, reference_magnitude: ReferenceMagnitude | None = None, t0: float | qblox_scheduler.operations.expressions.Expression = 0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   A real valued square pulse convolved with a Hann window for smoothing.

   :param amp: Unitless amplitude of the envelope.
   :param duration: The pulse duration in seconds.
   :param port: Port of the pulse, must be capable of playing a complex waveform.
   :param clock: Clock used to modulate the pulse.
                 By default the baseband clock.
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule.


.. py:class:: ChirpPulse(amp: float | qblox_scheduler.operations.expressions.Expression | collections.abc.Sequence[float | qblox_scheduler.operations.expressions.Expression], duration: float | qblox_scheduler.operations.expressions.Expression, port: str, clock: str, start_freq: float | qblox_scheduler.operations.expressions.Expression, end_freq: float | qblox_scheduler.operations.expressions.Expression, reference_magnitude: ReferenceMagnitude | None = None, t0: float | qblox_scheduler.operations.expressions.Expression = 0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   A linear chirp signal. A sinusoidal signal that ramps up in frequency.

   :param amp: Unitless amplitude of the envelope.
   :param duration: Duration of the pulse.
   :param port: The port of the pulse.
   :param clock: Clock used to modulate the pulse.
   :param start_freq: Start frequency of the Chirp. Note that this is the frequency at which the
                      waveform is calculated, this may differ from the clock frequency.
   :param end_freq: End frequency of the Chirp.
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :param t0: Shift of the start time with respect to the start of the operation.


.. py:class:: DRAGPulse(amplitude: float | qblox_scheduler.operations.expressions.Expression, beta: float, phase: float | qblox_scheduler.operations.expressions.Expression, duration: float | qblox_scheduler.operations.expressions.Expression, port: str, clock: str, reference_magnitude: ReferenceMagnitude | None = None, sigma: float | qblox_scheduler.operations.expressions.Expression | None = None, t0: float | qblox_scheduler.operations.expressions.Expression = 0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   A Gaussian pulse with a derivative component added to the out-of-phase channel.
   It uses the specified amplitude and sigma.
   If sigma is not specified it is set to 1/4 of the duration.

   The DRAG pulse is intended for single qubit gates in transmon based systems.
   It can be calibrated to reduce unwanted excitations of the
   :math:`|1\rangle - |2\rangle` transition (:cite:t:`motzoi_simple_2009` and
   :cite:t:`gambetta_analytic_2011`).

   The waveform is generated using :func:`.waveforms.drag` .

   :param amplitude: Unitless amplitude of the Gaussian envelope.
   :param beta: Unitless amplitude of the derivative component, the DRAG-pulse parameter.
   :param duration: The pulse duration in seconds.
   :param phase: Phase of the pulse in degrees.
   :param clock: Clock used to modulate the pulse.
   :param port: Port of the pulse, must be capable of carrying a complex waveform.
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :param sigma: Width of the Gaussian envelope in seconds. If not provided, the sigma
                 is set to 1/4 of the duration.
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule.


.. py:class:: GaussPulse(amplitude: float | qblox_scheduler.operations.expressions.Expression, phase: float | qblox_scheduler.operations.expressions.Expression, duration: float | qblox_scheduler.operations.expressions.Expression, port: str, clock: str = BasebandClockResource.IDENTITY, reference_magnitude: ReferenceMagnitude | None = None, sigma: float | qblox_scheduler.operations.expressions.Expression | None = None, t0: float | qblox_scheduler.operations.expressions.Expression = 0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   The GaussPulse Operation is a real-valued pulse with the specified
   amplitude and sigma.
   If sigma is not specified it is set to 1/4 of the duration.

   The waveform is generated using :func:`.waveforms.drag` with a beta set to zero,
   corresponding to a Gaussian pulse.

   :param amplitude: Unitless amplitude of the Gaussian envelope.
   :param duration: The pulse duration in seconds.
   :param phase: Phase of the pulse in degrees.
   :param clock: Clock used to modulate the pulse.
                 By default the baseband clock.
   :param port: Port of the pulse, must be capable of carrying a complex waveform.
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :param sigma: Width of the Gaussian envelope in seconds. If not provided, the sigma
                 is set to 1/4 of the duration.
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule.


.. py:function:: create_dc_compensation_pulse(pulses: list[qblox_scheduler.operations.operation.Operation], sampling_rate: float, port: str, t0: float = 0, amp: float | None = None, reference_magnitude: ReferenceMagnitude | None = None, duration: float | None = None) -> SquarePulse

   Calculates a SquarePulse to counteract charging effects based on a list of pulses.

   The compensation is calculated by summing the area of all pulses on the specified
   port.
   This gives a first order approximation for the pulse required to compensate the
   charging. All modulated pulses ignored in the calculation.

   :param pulses: List of pulses to compensate
   :param sampling_rate: Resolution to calculate the enclosure of the
                         pulses to calculate the area to compensate.
   :param amp: Desired unitless amplitude of the DC compensation SquarePulse.
               Leave to None to calculate the value for compensation,
               in this case you must assign a value to duration.
               The sign of the amplitude is ignored and adjusted
               automatically to perform the compensation.
   :param duration: Desired pulse duration in seconds.
                    Leave to None to calculate the value for compensation,
                    in this case you must assign a value to amp.
                    The sign of the value of amp given in the previous step
                    is adjusted to perform the compensation.
   :param port: Port to perform the compensation. Any pulse that does not
                belong to the specified port is ignored.
   :param clock: Clock used to modulate the pulse.
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :param phase: Phase of the pulse in degrees.
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule.

   :returns: :
                 Returns a SquarePulse object that compensates all pulses passed as argument.



.. py:class:: WindowOperation(window_name: str, duration: float | qblox_scheduler.operations.expressions.Expression, t0: float | qblox_scheduler.operations.expressions.Expression = 0.0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   The WindowOperation is an operation for visualization purposes.

   The :class:`~WindowOperation` has a starting time and duration.


   .. py:property:: window_name
      :type: str


      Return the window name of this operation.


.. py:class:: NumericalPulse(samples: numpy.ndarray | list, t_samples: numpy.ndarray | list, port: str, clock: str = BasebandClockResource.IDENTITY, gain: complex | float | qblox_scheduler.operations.expressions.Expression | collections.abc.Sequence[complex | float | qblox_scheduler.operations.expressions.Expression] = 1, reference_magnitude: ReferenceMagnitude | None = None, t0: float | qblox_scheduler.operations.expressions.Expression = 0, interpolation: str = 'linear')

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   A pulse where the shape is determined by specifying an array of (complex) points.

   If points are required between the specified samples (such as could be
   required by the sampling rate of the hardware), meaning :math:`t[n] < t' < t[n+1]`,
   `scipy.interpolate.interp1d` will be used to interpolate between the two points and
   determine the value.

   :param samples: An array of (possibly complex) values specifying the shape of the pulse.
   :param t_samples: An array of values specifying the corresponding times at which the
                     ``samples`` are evaluated.
   :param port: The port that the pulse should be played on.
   :param clock: Clock used to (de)modulate the pulse.
                 By default the baseband clock.
   :param gain: Gain factor between -1 and 1 that multiplies with the samples, by default 1.
   :param reference_magnitude: Scaling value and unit for the unitless samples. Uses settings in
                               hardware config if not provided.
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule.
   :param interpolation: Specifies the type of interpolation used. This is passed as the "kind"
                         argument to `scipy.interpolate.interp1d`.


.. py:class:: SkewedHermitePulse(duration: float | qblox_scheduler.operations.expressions.Expression, amplitude: float | qblox_scheduler.operations.expressions.Expression, skewness: float | qblox_scheduler.operations.expressions.Expression, phase: float | qblox_scheduler.operations.expressions.Expression, port: str, clock: str, reference_magnitude: ReferenceMagnitude | None = None, t0: float | qblox_scheduler.operations.expressions.Expression = 0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Hermite pulse intended for single qubit gates in diamond based systems.

   The waveform is generated using :func:`~qblox_scheduler.waveforms.skewed_hermite`.

   :param duration: The pulse duration in seconds.
   :param amplitude: Unitless amplitude of the hermite pulse.
   :param skewness: Skewness in the frequency space.
   :param phase: Phase of the pulse in degrees.
   :param clock: Clock used to modulate the pulse.
   :param port: Port of the pulse, must be capable of carrying a complex waveform.
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule. By default 0.


.. py:class:: Timestamp(port: str, t0: float | qblox_scheduler.operations.expressions.Expression = 0, clock: str = DigitalClockResource.IDENTITY)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Operation that marks a time reference for timetags.

   Specifically, all timetags in
   :class:`~qblox_scheduler.operations.acquisition_library.Timetag` and
   :class:`~qblox_scheduler.operations.acquisition_library.TimetagTrace` are
   measured relative to the timing of this operation, if they have a matching port and
   clock, and if ``time_ref=TimeRef.TIMESTAMP`` is given as an argument.

   :param port: The same port that the timetag acquisition is defined on.
   :param clock: The same clock that the timetag acquisition is defined on.
   :param t0: Time offset (in seconds) of this Operation, relative to the start time in the
              TimeableSchedule. By default 0.


