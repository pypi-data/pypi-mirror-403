waveforms
=========

.. py:module:: qblox_scheduler.helpers.waveforms 

.. autoapi-nested-parse::

   Module containing helper functions related to waveforms.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.helpers.waveforms.GetWaveformPartial



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.helpers.waveforms.get_waveform_size
   qblox_scheduler.helpers.waveforms.resize_waveforms
   qblox_scheduler.helpers.waveforms.resize_waveform
   qblox_scheduler.helpers.waveforms.shift_waveform
   qblox_scheduler.helpers.waveforms.get_waveform
   qblox_scheduler.helpers.waveforms.get_waveform_by_pulseid
   qblox_scheduler.helpers.waveforms.exec_waveform_partial
   qblox_scheduler.helpers.waveforms.exec_waveform_function
   qblox_scheduler.helpers.waveforms.exec_custom_waveform_function
   qblox_scheduler.helpers.waveforms.apply_mixer_skewness_corrections
   qblox_scheduler.helpers.waveforms.modulate_waveform
   qblox_scheduler.helpers.waveforms.normalize_waveform_data
   qblox_scheduler.helpers.waveforms.area_pulses
   qblox_scheduler.helpers.waveforms.area_pulse



.. py:class:: GetWaveformPartial

   Bases: :py:obj:`Protocol`


   Protocol type definition class for the get_waveform partial function.


.. py:function:: get_waveform_size(waveform: numpy.ndarray, granularity: int) -> int

   Return the number of samples required to respect the granularity.

   :param waveform: Numerical waveform.
   :param granularity: The granularity.


.. py:function:: resize_waveforms(waveforms_dict: dict[int, numpy.ndarray], granularity: int) -> None

   Resizes the waveforms to a multiple of the given granularity.

   :param waveforms_dict: The waveforms dictionary.
   :param granularity: The granularity.


.. py:function:: resize_waveform(waveform: numpy.ndarray, granularity: int) -> numpy.ndarray

   Return the waveform in a size that is a modulo of the given granularity.

   :param waveform: The waveform array.
   :param granularity: The waveform granularity.

   :returns: :
                 The resized waveform with a length equal to
                 `mod(len(waveform), granularity) == 0`.



.. py:function:: shift_waveform(waveform: numpy.ndarray, start_in_seconds: float, sampling_rate: int, resolution: int) -> tuple[int, numpy.ndarray]

   Return the waveform shifted with a number of samples.

   This compensates for rounding errors that cause misalignment
   of the waveform in the clock time domain.

   .. Note::
       when using this method be sure that the pulse starts
       at a `round(start_in_sequencer_count)`.

   .. code-block::

       waveform = np.ones(32)
       sampling_rate = int(2.4e9)
       resolution: int = 8

       t0: float = 16e-9
       #                 4.8 = 16e-9 / (8 / 2.4e9)
       start_in_sequencer_count = (t0 // (resolution / sampling_rate))

       start_waveform_at_sequencer_count(start_in_sequencer_count, waveform)

   :param waveform: The waveform.
   :param start_in_seconds: The start time (in seconds).
   :param sampling_rate: The sampling rate
   :param resolution: The sequencer resolution.


.. py:function:: get_waveform(pulse_info: dict[str, Any], sampling_rate: float) -> numpy.ndarray

   Return the waveform of a pulse_info dictionary.

   :param pulse_info: The pulse_info dictionary.
   :param sampling_rate: The sample rate of the waveform.

   :returns: :
                 The waveform.



.. py:function:: get_waveform_by_pulseid(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule) -> dict[int, GetWaveformPartial]

   Return a lookup dictionary of pulse_id and its partial waveform function.

   The keys are pulse info ids while the values are partial functions. Executing
   the waveform will return a :class:`numpy.ndarray`.

   :param schedule: The schedule.


.. py:function:: exec_waveform_partial(pulse_id: int, pulseid_waveformfn_dict: dict[int, GetWaveformPartial], sampling_rate: int) -> numpy.ndarray

   Return the result of the partial waveform function.

   :param pulse_id: The pulse uuid.
   :param pulseid_waveformfn_dict: The partial waveform lookup dictionary.
   :param sampling_rate: The sampling rate.

   :returns: :
                 The waveform array.



.. py:function:: exec_waveform_function(wf_func: str, t: numpy.ndarray, pulse_info: dict) -> numpy.ndarray

   Return the result of the pulse's waveform function.

   If the wf_func is defined outside qblox-scheduler then the
   wf_func is dynamically loaded and executed using
   :func:`~qblox_scheduler.helpers.waveforms.exec_custom_waveform_function`.

   :param wf_func: The custom waveform function path.
   :param t: The linear timespace.
   :param pulse_info: The dictionary containing pulse information.

   :returns: :
                 Returns the computed waveform.



.. py:function:: exec_custom_waveform_function(wf_func: str, t: numpy.ndarray, pulse_info: dict) -> numpy.ndarray

   Load and import an ambiguous waveform function from a module by string.

   The parameters of the dynamically loaded wf_func are extracted using
   :func:`inspect.signature` while the values are extracted from the



.. py:function:: apply_mixer_skewness_corrections(waveform: numpy.ndarray, amplitude_ratio: float, phase_shift: float) -> numpy.ndarray

   Apply a correction for amplitude imbalances and phase errors.

   Using an IQ mixer from previously calibrated values.

   Phase correction is done using:

   .. math::

       Re(z_{corrected}) (t) = Re(z (t)) + Im(z (t)) \tan(\phi)
       Im(z_{corrected}) (t) = Im(z (t)) / \cos(\phi)

   The amplitude correction is achieved by rescaling the waveforms back to their
   original amplitudes and multiplying or dividing the I and Q signals respectively by
   the square root of the amplitude ratio.

   :param waveform: The complex valued waveform on which the correction will be applied.
   :param amplitude_ratio: The ratio between the amplitudes of I and Q that is used to correct
                           for amplitude imbalances between the different paths in the IQ mixer.
   :param phase_shift: The phase error (in deg) used to correct the phase between I and Q.

   :returns: :
                 The complex valued waveform with the applied phase and amplitude
                 corrections.



.. py:function:: modulate_waveform(t: numpy.ndarray, envelope: numpy.ndarray, freq: float, t0: float = 0) -> numpy.ndarray

   Generate a (single sideband) modulated waveform from a given envelope.

   This is done by multiplying it with a complex exponential.

   .. math::

       z_{mod} (t) = z (t) \cdot e^{2\pi i f (t+t_0)}

   The signs are chosen such that the frequencies follow the relation RF = LO + IF for
   LO, IF > 0.

   :param t: A numpy array with time values
   :param envelope: The complex-valued envelope of the modulated waveform
   :param freq: The frequency of the modulation
   :param t0: Time offset for the modulation

   :returns: :
                 The modulated waveform



.. py:function:: normalize_waveform_data(data: numpy.ndarray) -> tuple[numpy.ndarray, float, float]

   Normalize waveform data, such that the value is +1.0 where the absolute value is
   maximal.

   This means that two waveforms where waveform_1 = c * waveform_2 (c can be any real
   number) will be normalized to the same normalized waveform data; this holds
   separately for the real and imaginary parts.

   :param data: The waveform data to rescale.

   :returns: rescaled_data
                 The rescaled data.
             amp_real
                 The original amplitude of the real part.
             amp_imag
                 The original amplitude of the imaginary part.



.. py:function:: area_pulses(pulses: list[dict[str, Any]], sampling_rate: float) -> float

   Calculate the area of a set of pulses.

   For details of the calculation see `area_pulse`.

   :param pulses: List of dictionary with information of the pulses
   :param sampling_rate: Sampling rate for the pulse

   :returns: :
                 The area formed by all the pulses



.. py:function:: area_pulse(pulse: dict[str, Any], sampling_rate: float) -> float

   Calculate the area of a single pulse.

   The sampled area is calculated, which means that the area calculated is
   based on the sampled waveform. This can differ slightly from the ideal area of
   the parameterized pulse.

   The duration used for calculation is the duration of the pulse. This duration
   is equal to the duration of the sampled waveform for pulse durations that
   are integer multiples of the 1/`sampling_rate`.

   :param pulse: The dictionary with information of the pulse
   :param sampling_rate: Sampling rate for the pulse

   :returns: :
                 The area defined by the pulse



