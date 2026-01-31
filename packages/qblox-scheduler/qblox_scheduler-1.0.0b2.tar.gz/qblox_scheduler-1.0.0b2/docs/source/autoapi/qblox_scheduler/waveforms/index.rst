waveforms
=========

.. py:module:: qblox_scheduler.waveforms 

.. autoapi-nested-parse::

   Contains function to generate most basic waveforms.

   These functions are intended to be used to generate waveforms defined in the
   :mod:`~qblox_scheduler.operations.pulse_library`.
   Examples of waveforms that are too advanced are flux pulses that require knowledge of
   the flux sensitivity and interaction strengths and qubit frequencies.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.waveforms.square
   qblox_scheduler.waveforms.square_imaginary
   qblox_scheduler.waveforms.ramp
   qblox_scheduler.waveforms.staircase
   qblox_scheduler.waveforms.soft_square
   qblox_scheduler.waveforms.chirp
   qblox_scheduler.waveforms.drag
   qblox_scheduler.waveforms.sudden_net_zero
   qblox_scheduler.waveforms.interpolated_complex_waveform
   qblox_scheduler.waveforms.rotate_wave
   qblox_scheduler.waveforms.skewed_hermite



.. py:function:: square(t: numpy.ndarray | list[float], amp: float | complex) -> numpy.ndarray

   Generate a square pulse.


.. py:function:: square_imaginary(t: numpy.ndarray | list[float], amp: float | complex) -> numpy.ndarray

   Generate a square pulse with imaginary amplitude.


.. py:function:: ramp(t: numpy.ndarray, amp: float, offset: float, duration: float) -> numpy.ndarray

   Generate a ramp pulse.


.. py:function:: staircase(t: numpy.typing.NDArray[numpy.float64], start_amp: float | complex, final_amp: float | complex, num_steps: int, duration: float) -> numpy.typing.NDArray[numpy.float64] | numpy.typing.NDArray[numpy.complex128]

   Ramps from zero to a finite value in discrete steps.

   :param t: Times at which to evaluate the function.
             Times < 0 will output `start_amp`.
             Times >= `duration` will output `final_amp`.
   :param start_amp: Starting amplitude.
   :param final_amp: Final amplitude to reach on the last step.
   :param num_steps: Number of steps to reach final value.
   :param duration: Duration of the pulse in seconds.

   :returns: :
                 The real valued waveform.



.. py:function:: soft_square(t: numpy.typing.NDArray | list[float], amp: float | complex) -> numpy.typing.NDArray

   A softened square pulse.

   :param t: Times at which to evaluate the function.
   :param amp: Amplitude of the pulse.


.. py:function:: chirp(t: numpy.ndarray, amp: float, start_freq: float, end_freq: float, duration: float) -> numpy.ndarray

   Produces a linear chirp signal.

   The frequency is determined according to the
   relation:

   .. math:

       f(t) = ct + f_0,
       c = \frac{f_1 - f_0}{T}

   The waveform is produced simply by multiplying with a complex exponential.

   :param t: Times at which to evaluate the function.
   :param amp: Amplitude of the envelope.
   :param start_freq: Start frequency of the Chirp.
   :param end_freq: End frequency of the Chirp.
   :param duration: Duration of the pulse in seconds.

   :returns: :
                 The complex waveform.



.. py:function:: drag(t: numpy.ndarray, amplitude: float, beta: float, duration: float, nr_sigma: float, sigma: float | int | None = None, phase: float = 0, subtract_offset: Literal['average', 'first', 'last', 'none'] = 'average') -> numpy.ndarray

   Generates a DRAG pulse consisting of a Gaussian :math:`G` as the I-component and a
   Derivative :math:`D` as the Q-component (:cite:t:`motzoi_simple_2009` and
   :cite:t:`gambetta_analytic_2011`).

   All inputs are in s and Hz.
   Phases are in degrees.

   The Gaussian envelope is:

   :math:`G(t) = A \exp\left(-\frac{(t-\mu)^2}{2\sigma^2}\right)`

   where :math:`A` is the ``amplitude``, :math:`\mu = t_0 + \text{duration}/2` is the
   pulse center, and :math:`\sigma = \text{duration}/(2 \cdot \text{nr_sigma})` when
   ``sigma`` is not explicitly provided.

   The derivative (DRAG) component is:

   :math:`D(t) = -\beta \frac{(t-\mu)}{\sigma^2} G(t)`

   where :math:`\beta` is the ``beta`` parameter.

   The final complex waveform is:

   :math:`W(t) = e^{i \phi} \left( G(t) + i D(t) \right)`

   where :math:`\phi` is the ``phase`` converted to radians.

   :param t: Times at which to evaluate the function.
   :param amplitude: Amplitude of the Gaussian envelope.
   :param beta: Amplitude of the derivative component, the DRAG-pulse parameter.
   :param duration: Duration of the pulse in seconds.
   :param nr_sigma: After how many sigma the Gaussian is cut off.
   :param sigma: Width of the Gaussian envelope. If None, it is calculated as
                 duration / (2 * nr_sigma).
   :param phase: Phase of the pulse in degrees.
   :param subtract_offset: Instruction on how to subtract the offset in order to avoid jumps in the
                           waveform due to the cut-off.

                           - 'average': subtract the average of the first and last point.
                           - 'first': subtract the value of the waveform at the first sample.
                           - 'last': subtract the value of the waveform at the last sample.
                           - 'none', None: don't subtract any offset.

   :returns: :
                 Complex waveform.



.. py:function:: sudden_net_zero(t: numpy.ndarray, amp_A: float, amp_B: float, net_zero_A_scale: float, t_pulse: float, t_phi: float, t_integral_correction: float) -> numpy.typing.NDArray

   Generates the sudden net zero waveform from :cite:t:`negirneac_high_fidelity_2021`.

   The waveform consists of a square pulse with a duration of half
   ``t_pulse`` and an amplitude of ``amp_A``, followed by an idling period (0
   V) with duration ``t_phi``, followed again by a square pulse with amplitude
   ``-amp_A * net_zero_A_scale`` and a duration of half ``t_pulse``, followed
   by a integral correction period with duration ``t_integral_correction``.

   The last sample of the first pulse has amplitude ``amp_A * amp_B``. The
   first sample of the second pulse has amplitude ``-amp_A * net_zero_A_scale *
   amp_B``.

   The amplitude of the integral correction period is such that ``sum(waveform)
   == 0``.

   If the total duration of the pulse parts is less than the duration set by
   the ``t`` array, the remaining samples will be set to 0 V.

   The various pulse part durations are rounded **down** (floor) to the sample
   rate of the ``t`` array. Since ``t_pulse`` is the total duration of the two
   square pulses, half this duration is rounded to the sample rate. For
   example:

   .. jupyter-execute::

       import numpy as np
       from qblox_scheduler.waveforms import sudden_net_zero

       t = np.linspace(0, 9e-9, 10)  # 1 GSa/s
       amp_A = 1.0
       amp_B = 0.5
       net_zero_A_scale = 0.8
       t_pulse = 5.0e-9  # will be rounded to 2 pulses of 2 ns
       t_phi = 2.6e-9  # rounded to 2 ns
       t_integral_correction = 4.4e-9  # rounded to 4 ns

       sudden_net_zero(
           t, amp_A, amp_B, net_zero_A_scale, t_pulse, t_phi, t_integral_correction
       )

   :param t: A uniformly sampled array of times at which to evaluate the function.
   :param amp_A: Amplitude of the main square pulse
   :param amp_B: Scaling correction for the final sample of the first square and first sample
                 of the second square pulse.
   :param net_zero_A_scale: Amplitude scaling correction factor of the negative arm of the net-zero pulse.
   :param t_pulse: The total duration of the two half square pulses. The duration of each
                   half is rounded to the sample rate of the ``t`` array.
   :param t_phi: The idling duration between the two half pulses. The duration is rounded
                 to the sample rate of the ``t`` array.
   :param t_integral_correction: The duration in which any non-zero pulse amplitude needs to be
                                 corrected. The duration is rounded to the sample rate of the ``t`` array.


.. py:function:: interpolated_complex_waveform(t: numpy.ndarray, gain: float | complex, samples: numpy.ndarray, t_samples: numpy.ndarray, interpolation: str = 'linear', **kwargs) -> numpy.ndarray

   Wrapper function around :class:`scipy.interpolate.interp1d`, which takes the
   array of (complex) samples, interpolates the real and imaginary parts
   separately and returns the interpolated values at the specified times.

   :param t: Times at which to evaluated the to be returned waveform.
   :param gain: Gain factor between -1 and 1 that multiplies with the samples, by default 1.
   :param samples: An array of (possibly complex) values specifying the shape of the waveform.
   :param t_samples: An array of values specifying the corresponding times at which the ``samples``
                     are evaluated.
   :param interpolation: The interpolation method to use, by default "linear".
   :param kwargs: Optional keyword arguments to pass to ``scipy.interpolate.interp1d``.

   :returns: :
                 An array containing the interpolated values.



.. py:function:: rotate_wave(wave: numpy.ndarray, phase: float) -> numpy.ndarray

   Rotate a wave in the complex plane.

   :param wave: Complex waveform, real component corresponds to I, imaginary component to Q.
   :param phase: Rotation angle in degrees.

   :returns: :
                 Rotated complex waveform.



.. py:function:: skewed_hermite(t: numpy.ndarray, duration: float, amplitude: float, skewness: float, phase: float, pi2_pulse: bool = False, center: float | None = None, duration_over_char_time: float = 6.0) -> numpy.ndarray

   Generates a skewed hermite pulse for single qubit rotations in NV centers.

   A Hermite pulse is a Gaussian multiplied by a second degree Hermite polynomial.
   See :cite:t:`Beukers_MSc_2019`, Appendix A.2.

   The skew parameter is a first order amplitude correction to the hermite pulse. It
   increases the fidelity of the performed gates.
   See :cite:t:`Beukers_MSc_2019`, section 4.2. To get a "standard" hermite
   pulse, use ``skewness=0``.

   The hermite factors are taken from equation 44 and 45 of
   :cite:t:`Warren_NMR_pulse_shapes_1984`.

   :param t: Times at which to evaluate the function.
   :param duration: Duration of the pulse in seconds.
   :param amplitude: Amplitude of the pulse.
   :param skewness: Skewness in the frequency space
   :param phase: Phase of the pulse in degrees.
   :param pi2_pulse: if True, the pulse will be pi/2 otherwise pi pulse
   :param center: Optional: time after which the pulse center occurs. If ``None``, it is
                  automatically set to duration/2.
   :param duration_over_char_time: Ratio of the pulse duration and the characteristic time of the hermite
                                   polynomial. Increasing this number will compress the pulse. By default, 6.

   :returns: :
                 complex skewed waveform



