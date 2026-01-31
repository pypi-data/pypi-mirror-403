verification
============

.. py:module:: qblox_scheduler.schedules.verification 

.. autoapi-nested-parse::

   Schedules intended to verify (test) functionality of the system.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules.verification.acquisition_staircase_sched
   qblox_scheduler.schedules.verification.awg_staircase_sched
   qblox_scheduler.schedules.verification.multiplexing_staircase_sched



.. py:function:: acquisition_staircase_sched(readout_pulse_amps: numpy.typing.NDArray[numpy.ScalarType], readout_pulse_duration: float, readout_frequency: float, acquisition_delay: float, integration_time: float, port: str, clock: str, init_duration: float = 1e-06, acq_channel: collections.abc.Hashable = 0, repetitions: int = 1) -> qblox_scheduler.TimeableSchedule

   Generates a staircase program in which the amplitude of a readout pulse is varied.

   TimeableSchedule sequence
       .. centered:: Reset -- RO_pulse[i] -- Acq[i]

   :param readout_pulse_amps: amplitudes of the square readout pulse in Volts.
   :param readout_pulse_duration: duration of the spectroscopy pulse in seconds.
   :param readout_frequency: readout_frequency of the spectroscopy pulse and of the data acquisition in
                             Hertz.
   :param acquisition_delay: start of the data acquisition with respect to the start of the spectroscopy
                             pulse in seconds.
   :param integration_time: integration time of the data acquisition in seconds.
   :param port: location on the device where the pulse should be applied.
   :param clock: reference clock used to track the readout frequency.
   :param batched: schedule to be run in batched mode in the hardware backend.
   :param init_duration: The relaxation time or dead time.
   :param acq_channel: The acquisition channel to use for the acquisitions.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   .. rubric:: Notes

   This schedule can be used to verify the binning and averaging functionality of
   weighted acquisition for readout modules such as a Qblox QRM.

   Because of the overlap between the readout pulse and the integration window, the
   change in readout pulse amplitude should show up immediately in the acquired signal.


.. py:function:: awg_staircase_sched(pulse_amps: numpy.typing.NDArray[numpy.ScalarType], pulse_duration: float, readout_frequency: float, acquisition_delay: float, integration_time: float, mw_port: str, ro_port: str, mw_clock: str, ro_clock: str, init_duration: float = 1e-06, acq_channel: collections.abc.Hashable = 0, repetitions: int = 1) -> qblox_scheduler.TimeableSchedule

   Generates a staircase program in which the amplitude of a control pulse is varied.

   TimeableSchedule sequence
       .. centered:: Reset -- MW_pulse[i] -- Acq[i]

   :param pulse_amps: amplitudes of the square readout pulse in Volts.
   :param pulse_duration: duration of the spectroscopy pulse in seconds.
   :param readout_frequency: readout_frequency of the spectroscopy pulse and of the data acquisition in
                             Hertz.
   :param acquisition_delay: start of the data acquisition with respect to the start of the spectroscopy
                             pulse in seconds.
   :param integration_time: integration time of the data acquisition in seconds.
   :param mw_port: location on the device where the pulse should be applied.
   :param ro_port: location on the device where the signal should should be interpreted.
   :param ro_clock: reference clock connected to hdawg used to track the readout frequency.
   :param mw_clock: reference clock connected to uhfqa used to track the readout frequency.
   :param batched: schedule to be run in batched mode in the hardware backend.
   :param init_duration: The relaxation time or dead time.
   :param acq_channel: The acquisition channel to use for the acquisitions.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   .. rubric:: Notes

   The control pulse is configured to be applied at the same frequency as the
   acquisition so that it shows up in the in the acquired signal.

   This schedule can be used to verify the binning and averaging functionality of
   weighted acquisition in combination with the synchronization between the readout
   module (e.g., Qblox QRM) and the pulse generating module (e.g., Qblox QCM).


.. py:function:: multiplexing_staircase_sched(pulse_amps: numpy.typing.NDArray[numpy.ScalarType], pulse_duration: float, acquisition_delay: float, integration_time: float, ro_port: str, ro_clock0: str, ro_clock1: str, readout_frequency0: float, readout_frequency1: float, init_duration: float = 1e-06, repetitions: int = 1) -> qblox_scheduler.TimeableSchedule

   Adds two simultaneous staircases where the amplitudes are varied in opposite order.

   The schedule will always use acquisition channels 0 and 1.

   :param pulse_amps: Amplitudes of the square readout pulse in Volts. The second staircase will use
                      this same array in reverse order.
   :param pulse_duration: duration of the spectroscopy pulse in seconds.
   :param acquisition_delay: start of the data acquisition with respect to the start of the spectroscopy
                             pulse in seconds.
   :param integration_time: integration time of the data acquisition in seconds.
   :param ro_port: location on the device where the signal should should be interpreted.
   :param ro_clock0: Clock used to modulate the first staircase.
   :param ro_clock1: Clock used to modulate the second staircase.
   :param readout_frequency0: readout_frequency of the spectroscopy pulse and of the data acquisition in
                              Hertz of the first staircase.
   :param readout_frequency1: readout_frequency of the spectroscopy pulse and of the data acquisition in
                              Hertz of the second staircase.
   :param init_duration: The relaxation time or dead time.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 The generated schedule.



