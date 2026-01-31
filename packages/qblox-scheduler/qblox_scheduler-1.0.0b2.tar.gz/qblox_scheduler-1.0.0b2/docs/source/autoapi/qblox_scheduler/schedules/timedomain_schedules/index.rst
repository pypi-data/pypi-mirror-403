timedomain_schedules
====================

.. py:module:: qblox_scheduler.schedules.timedomain_schedules 

.. autoapi-nested-parse::

   Module containing schedules for common time domain experiments such as a Rabi and
   T1 measurement.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules.timedomain_schedules.rabi_sched
   qblox_scheduler.schedules.timedomain_schedules.t1_sched
   qblox_scheduler.schedules.timedomain_schedules.ramsey_sched
   qblox_scheduler.schedules.timedomain_schedules.echo_sched
   qblox_scheduler.schedules.timedomain_schedules.cpmg_sched
   qblox_scheduler.schedules.timedomain_schedules.allxy_sched
   qblox_scheduler.schedules.timedomain_schedules.readout_calibration_sched
   qblox_scheduler.schedules.timedomain_schedules.rabi_pulse_sched



.. py:function:: rabi_sched(pulse_amp: numpy.ndarray | float, pulse_duration: numpy.ndarray | float, frequency: float, qubit: str, port: str = None, clock: str = None, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing a Rabi using a Gaussian pulse.

   TimeableSchedule sequence
       .. centered:: Reset -- DRAG -- Measure

   :param pulse_amp: amplitude of the Rabi pulse in V.
   :param pulse_duration: duration of the Gaussian shaped Rabi pulse. Corresponds to 4 sigma.
   :param frequency: frequency of the qubit 01 transition.
   :param qubit: the device element name on which to perform a Rabi experiment.
   :param port: location on the chip where the Rabi pulse should be applied.
                if set to :code:`None`, will use the naming convention :code:`"<device element name>:mw"` to
                infer the port.
   :param clock: name of the location in frequency space where to apply the Rabi pulse.
                 if set to :code:`None`, will use the naming convention :code:`"<device_element>.01"` to
                 infer the clock.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.


.. py:function:: t1_sched(times: numpy.ndarray | float, qubit: str, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing a :math:`T_1` experiment to measure the qubit
   relaxation time.

   TimeableSchedule sequence
       .. centered:: Reset -- pi -- Idle(tau) -- Measure

   See section III.B.2. of :cite:t:`krantz_quantum_2019` for an explanation of the Bloch-Redfield
   model of decoherence and the :math:`T_1` experiment.

   :param times: an array of wait times tau between the start of pi-pulse and the measurement.
   :param qubit: the name of the device element e.g., :code:`"q0"` to perform the T1 experiment on.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 An experiment schedule.



.. py:function:: ramsey_sched(times: numpy.ndarray | float, qubit: str, artificial_detuning: float = 0, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing a Ramsey experiment to measure the
   dephasing time :math:`T_2^{\star}`.

   TimeableSchedule sequence
       .. centered:: Reset -- pi/2 -- Idle(tau) -- pi/2 -- Measure

   See section III.B.2. of :cite:t:`krantz_quantum_2019` for an explanation of the Bloch-Redfield
   model of decoherence and the Ramsey experiment.

   :param times: an array of wait times tau between the start of the first pi/2 pulse and
                 the start of the second pi/2 pulse.
   :param artificial_detuning: frequency in Hz of the software emulated, or ``artificial`` qubit detuning, which is
                               implemented by changing the phase of the second pi/2 (recovery) pulse. The
                               artificial detuning changes the observed frequency of the Ramsey oscillation,
                               which can be useful to distinguish a slow oscillation due to a small physical
                               detuning from the decay of the dephasing noise.
   :param qubit: the name of the device element e.g., :code:`"q0"` to perform the Ramsey experiment on.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 An experiment schedule.



.. py:function:: echo_sched(times: numpy.ndarray | float, qubit: str, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing an Echo experiment to measure the qubit
   echo-dephasing time :math:`T_2^{E}`.

   TimeableSchedule sequence
       .. centered:: Reset -- pi/2 -- Idle(tau/2) -- pi -- Idle(tau/2) -- pi/2 -- Measure

   See section III.B.2. of :cite:t:`krantz_quantum_2019` for an explanation of the Bloch-Redfield
   model of decoherence and the echo experiment.

   :param qubit: the name of the device element e.g., "q0" to perform the echo experiment on.
   :param times: an array of wait times. Used as
                 tau/2 wait time between the start of the first pi/2 pulse and pi pulse,
                 tau/2 wait time between the start of the pi pulse and the final pi/2 pulse.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 An experiment schedule.



.. py:function:: cpmg_sched(n_gates: int, times: numpy.ndarray | float, qubit: str, variant: Literal['X', 'Y', 'XY'] = 'X', artificial_detuning: float = 0, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing a CPMG (n gates) experiment to measure the qubit
   dephasing time :math:`T_2^{CPMG}` with dynamical decoupling.

   TimeableSchedule sequence
       .. centered:: Reset -- pi/2 -- [Idle(tau/(2n)) -- pi -- Idle(tau/2n)]*n -- pi/2 -- Measure
       .. Idle time includes the pi pulse duration!


   :param n_gates: Number of CPMG Gates.
                   Note that `n_gates=1` corresponds to an Echo experiment (:func:`~.echo_sched`).
   :param qubit: The name of the device element, e.g., "q0", to perform the echo experiment on.
   :param times: An array of wait times between the pi/2 pulses. The wait times are
                 subdivided into multiple IdlePulse(time/(2n)) operations. Be aware that
                 time/(2n) must be an integer multiple of your hardware backend grid
                 time.
   :param variant: CPMG using either pi_x ("X"), pi_y ("Y")
                   or interleaved pi_x/pi_y ("XY") gates, default is "X".
   :param artificial_detuning: The frequency in Hz of the software emulated, or ``artificial`` qubit detuning, which is
                               implemented by changing the phase of the second pi/2 (recovery) pulse. The
                               artificial detuning changes the observed frequency of the Ramsey oscillation,
                               which can be useful to distinguish a slow oscillation due to a small physical
                               detuning from the decay of the dephasing noise.
   :param repetitions: The amount of times the TimeableSchedule will be repeated, default is 1.

   :returns: :
                 An experiment schedule.



.. py:function:: allxy_sched(qubit: str, element_select_idx: collections.abc.Iterable[int] | int = np.arange(21), repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing an AllXY experiment.

   TimeableSchedule sequence
       .. centered:: Reset -- Rxy[0] -- Rxy[1] -- Measure

   for a specific set of combinations of x90, x180, y90, y180 and idle rotations.

   See section 5.2.3 of :cite:t:`reed_entanglement_2013` for an explanation of
   the AllXY experiment and it's applications in diagnosing errors in single-qubit
   control pulses.

   :param qubit: the name of the device element e.g., :code:`"q0"` to perform the experiment on.
   :param element_select_idx: the index of the particular element of the AllXY experiment to execute.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 An experiment schedule.



.. py:function:: readout_calibration_sched(qubit: str, prepared_states: list[int], repetitions: int = 1, acq_protocol: Literal['SSBIntegrationComplex', 'ThresholdedAcquisition'] = 'SSBIntegrationComplex') -> qblox_scheduler.schedules.schedule.TimeableSchedule

   A schedule for readout calibration. Prepares a state and immediately performs
   a measurement.

   :param qubit: the name of the device element e.g., :code:`"q0"` to perform the experiment on.
   :param prepared_states: the states to prepare the qubit in before measuring as in integer corresponding
                           to the ground (0), first-excited (1) or second-excited (2) state.
   :param repetitions: The number of shots to acquire, sets the number of times the schedule will
                       be repeated.
   :param acq_protocol: The acquisition protocol used for the readout calibration. By default
                        "SSBIntegrationComplex", but "ThresholdedAcquisition" can be
                        used for verifying thresholded acquisition parameters with this function (see
                        :doc:`/tutorials/Conditional Reset`).

   :returns: :
                 An experiment schedule.

   :raises ValueError: If the prepared state is not either 0, 1, or 2.
   :raises NotImplementedError: If the prepared state is 2.


.. py:function:: rabi_pulse_sched(mw_amplitude: float, mw_beta: float, mw_frequency: float, mw_clock: str, mw_port: str, mw_pulse_duration: float, ro_pulse_amp: float, ro_pulse_duration: float, ro_pulse_delay: float, ro_pulse_port: str, ro_pulse_clock: str, ro_pulse_frequency: float, ro_acquisition_delay: float, ro_integration_time: float, init_duration: float, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing a Rabi experiment using a
   :func:`qblox_scheduler.waveforms.drag` pulse.

   .. note::

       This function allows specifying a Rabi experiment directly using the pulse-level
       abstraction. For most applications we recommend using :func:`rabi_sched`
       instead.

   :param mw_amplitude: amplitude of the gaussian component of a DRAG pulse.
   :param mw_beta: amplitude of the derivative-of-gaussian component of a DRAG pulse.
   :param mw_frequency: frequency of the DRAG pulse.
   :param mw_clock: reference clock used to track the qubit 01 transition.
   :param mw_port: location on the device where the pulse should be applied.
   :param mw_pulse_duration: duration of the DRAG pulse. Corresponds to 4 sigma.
   :param ro_pulse_amp: amplitude of the readout pulse in Volt.
   :param ro_pulse_duration: duration of the readout pulse in seconds.
   :param ro_pulse_delay: time between the end of the spectroscopy pulse and the start of the readout
                          pulse.
   :param ro_pulse_port: location on the device where the readout pulse should be applied.
   :param ro_pulse_clock: reference clock used to track the readout frequency.
   :param ro_pulse_frequency: frequency of the spectroscopy pulse and of the data acquisition in Hertz.
   :param ro_acquisition_delay: start of the data acquisition with respect to the start of the readout pulse
                                in seconds.
   :param ro_integration_time: integration time of the data acquisition in seconds.
   :param init_duration: The relaxation time or dead time.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.


