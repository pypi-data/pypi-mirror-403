spectroscopy_schedules
======================

.. py:module:: qblox_scheduler.schedules.spectroscopy_schedules 

.. autoapi-nested-parse::

   Module containing schedules for common spectroscopy experiments.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules.spectroscopy_schedules.heterodyne_spec_sched
   qblox_scheduler.schedules.spectroscopy_schedules.heterodyne_spec_sched_nco
   qblox_scheduler.schedules.spectroscopy_schedules.two_tone_spec_sched
   qblox_scheduler.schedules.spectroscopy_schedules.two_tone_spec_sched_nco
   qblox_scheduler.schedules.spectroscopy_schedules.nv_dark_esr_sched
   qblox_scheduler.schedules.spectroscopy_schedules.nv_dark_esr_sched_nco



.. py:function:: heterodyne_spec_sched(pulse_amp: float, pulse_duration: float, frequency: float, acquisition_delay: float, integration_time: float, port: str, clock: str, init_duration: float = 1e-05, repetitions: int = 1, port_out: str | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing heterodyne spectroscopy.

   :param pulse_amp: Amplitude of the spectroscopy pulse in Volt.
   :param pulse_duration: Duration of the spectroscopy pulse in seconds.
   :param frequency: Frequency of the spectroscopy pulse in Hertz.
   :param acquisition_delay: Start of the data acquisition with respect to the start of the spectroscopy
                             pulse in seconds.
   :param integration_time: Integration time of the data acquisition in seconds.
   :param port: Location on the device where the acquisition is performed.
   :param clock: Reference clock used to track the spectroscopy frequency.
   :param init_duration: The relaxation time or dead time.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.
   :param port_out: Output port on the device where the pulse should be applied. If `None`, then use
                    the same as `port`.


.. py:function:: heterodyne_spec_sched_nco(pulse_amp: float, pulse_duration: float, frequencies: numpy.ndarray, acquisition_delay: float, integration_time: float, port: str, clock: str, init_duration: float = 1e-05, repetitions: int = 1, port_out: str | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a batched schedule for performing fast heterodyne spectroscopy
   using the :class:`~qblox_scheduler.operations.pulse_library.SetClockFrequency`
   operation for doing an NCO sweep.

   .. admonition:: Example use of the ``heterodyne_spec_sched_nco`` schedule
       :class: tip

       .. jupyter-execute::

           import numpy as np
           from qcodes.parameters.parameter import ManualParameter

           from qblox_scheduler.gettables import ScheduleGettable
           from qblox_scheduler.device_under_test.quantum_device import QuantumDevice
           from qblox_scheduler.device_under_test.transmon_element import BasicTransmonElement
           from qblox_scheduler.schedules.spectroscopy_schedules import heterodyne_spec_sched_nco

           quantum_device = QuantumDevice(name="quantum_device")
           q0 = BasicTransmonElement("q0")
           quantum_device.add_element(q0)

           ...

           # Manual parameter for batched schedule
           ro_freq = ManualParameter("ro_freq", unit="Hz")
           ro_freq.batched = True
           ro_freqs = np.linspace(start=4.5e9, stop=5.5e9, num=11)
           quantum_device.cfg_sched_repetitions = 5

           # Configure the gettable
           device_element = quantum_device.get_element("q0")
           schedule_kwargs = {
               "pulse_amp": device_element.measure.pulse_amp,
               "pulse_duration": device_element.measure.pulse_duration,
               "frequencies": ro_freqs,
               "acquisition_delay": device_element.measure.acq_delay,
               "integration_time": device_element.measure.integration_time,
               "port": device_element.ports.readout,
               "clock": device_element.name + ".ro",
               "init_duration": device_element.reset.duration,
           }
           spec_gettable = ScheduleGettable(
               quantum_device=quantum_device,
               schedule_function=heterodyne_spec_sched_nco,
               schedule_kwargs=schedule_kwargs,
               real_imag=False,
               batched=True,
           )


   :param pulse_amp: Amplitude of the spectroscopy pulse in Volt.
   :param pulse_duration: Duration of the spectroscopy pulse in seconds.
   :param frequencies: Sample frequencies for the spectroscopy pulse in Hertz.
   :param acquisition_delay: Start of the data acquisition with respect to the start of the spectroscopy
                             pulse in seconds.
   :param integration_time: Integration time of the data acquisition in seconds.
   :param port: Location on the device where the acquisition is performed.
   :param clock: Reference clock used to track the spectroscopy frequency.
   :param init_duration: The relaxation time or dead time.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.
   :param port_out: Output port on the device where the pulse should be applied. If `None`, then use
                    the same as `port`.


.. py:function:: two_tone_spec_sched(spec_pulse_amp: float, spec_pulse_duration: float, spec_pulse_port: str, spec_pulse_clock: str, spec_pulse_frequency: float, ro_pulse_amp: float, ro_pulse_duration: float, ro_pulse_delay: float, ro_pulse_port: str, ro_pulse_clock: str, ro_pulse_frequency: float, ro_acquisition_delay: float, ro_integration_time: float, init_duration: float = 1e-05, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a schedule for performing two-tone spectroscopy.

   :param spec_pulse_amp: Amplitude of the spectroscopy pulse in Volt.
   :param spec_pulse_duration: Duration of the spectroscopy pulse in seconds.
   :param spec_pulse_port: Location on the device where the spectroscopy pulse should be applied.
   :param spec_pulse_clock: Reference clock used to track the spectroscopy frequency.
   :param spec_pulse_frequency: Frequency of the spectroscopy pulse in Hertz.
   :param ro_pulse_amp: Amplitude of the readout (spectroscopy) pulse in Volt.
   :param ro_pulse_duration: Duration of the readout (spectroscopy) pulse in seconds.
   :param ro_pulse_delay: Time between the end of the spectroscopy pulse and the start of the readout
                          (spectroscopy) pulse.
   :param ro_pulse_port: Location on the device where the readout (spectroscopy) pulse should be applied.
   :param ro_pulse_clock: Reference clock used to track the readout (spectroscopy) frequency.
   :param ro_pulse_frequency: Frequency of the readout (spectroscopy) pulse in Hertz.
   :param ro_acquisition_delay: Start of the data acquisition with respect to the start of the readout pulse in
                                seconds.
   :param ro_integration_time: Integration time of the data acquisition in seconds.
   :param init_duration: The relaxation time or dead time.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.


.. py:function:: two_tone_spec_sched_nco(spec_pulse_amp: float, spec_pulse_duration: float, spec_pulse_port: str, spec_pulse_clock: str, spec_pulse_frequencies: numpy.ndarray, ro_pulse_amp: float, ro_pulse_duration: float, ro_pulse_delay: float, ro_pulse_port: str, ro_pulse_clock: str, ro_pulse_frequency: float, ro_acquisition_delay: float, ro_integration_time: float, init_duration: float, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generate a batched schedule for performing fast two-tone spectroscopy using
   the :class:`~qblox_scheduler.operations.pulse_library.SetClockFrequency`
   operation for doing an NCO sweep.

   For long-lived qubits, it is advisable to use a small number of repetitions and
   compensate by doing continuous spectroscopy (low amplitude, long duration pulse with
   simultaneous long readout).

   The "dead-time" between two data points needs to be sufficient to properly reset the
   qubit. That means that `init_duration` should be >> T1 (so typically >200us).

   .. admonition:: Example use of the ``two_tone_spec_sched_nco`` schedule
       :class: tip

       .. jupyter-execute::

           import numpy as np
           from qcodes.parameters.parameter import ManualParameter

           from qblox_scheduler.gettables import ScheduleGettable
           from qblox_scheduler.device_under_test.quantum_device import QuantumDevice
           from qblox_scheduler.device_under_test.transmon_element import BasicTransmonElement
           from qblox_scheduler.schedules.spectroscopy_schedules import two_tone_spec_sched_nco

           quantum_device = QuantumDevice(name="quantum_device")
           q0 = BasicTransmonElement("q0")
           quantum_device.add_element(q0)

           ...

           # Manual parameter for batched schedule
           spec_freq = ManualParameter("spec_freq", unit="Hz")
           spec_freq.batched = True
           spec_freqs = np.linspace(start=4.5e9, stop=5.5e9, num=11)
           quantum_device.cfg_sched_repetitions = 5

           # Configure the gettable
           device_element = quantum_device.get_element("q0")
           schedule_kwargs = {
               "spec_pulse_amp": 0.5,
               "spec_pulse_duration": 8e-6,
               "spec_pulse_port": device_element.ports.microwave,
               "spec_pulse_clock": device_element.name + ".01",
               "spec_pulse_frequencies": spec_freqs,
               "ro_pulse_amp": device_element.measure.pulse_amp,
               "ro_pulse_duration": device_element.measure.pulse_duration,
               "ro_pulse_delay": 300e-9,
               "ro_pulse_port": device_element.ports.readout,
               "ro_pulse_clock": device_element.name + ".ro",
               "ro_pulse_frequency": 7.04e9,
               "ro_acquisition_delay": device_element.measure.acq_delay,
               "ro_integration_time": device_element.measure.integration_time,
               "init_duration": 300e-6,
           }
           spec_gettable = ScheduleGettable(
               quantum_device=quantum_device,
               schedule_function=two_tone_spec_sched_nco,
               schedule_kwargs=schedule_kwargs,
               real_imag=False,
               batched=True,
           )


   :param spec_pulse_amp: Amplitude of the spectroscopy pulse in Volt.
   :param spec_pulse_duration: Duration of the spectroscopy pulse in seconds.
   :param spec_pulse_port: Location on the device where the spectroscopy pulse should be applied.
   :param spec_pulse_clock: Reference clock used to track the spectroscopy frequency.
   :param spec_pulse_frequencies: Sample frequencies for the spectroscopy pulse in Hertz.
   :param ro_pulse_amp: Amplitude of the readout (spectroscopy) pulse in Volt.
   :param ro_pulse_duration: Duration of the readout (spectroscopy) pulse in seconds.
   :param ro_pulse_delay: Time between the end of the spectroscopy pulse and the start of the readout
                          (spectroscopy) pulse.
   :param ro_pulse_port: Location on the device where the readout (spectroscopy) pulse should be applied.
   :param ro_pulse_clock: Reference clock used to track the readout (spectroscopy) frequency.
   :param ro_pulse_frequency: Frequency of the readout (spectroscopy) pulse in Hertz.
   :param ro_acquisition_delay: Start of the data acquisition with respect to the start of the readout pulse in
                                seconds.
   :param ro_integration_time: Integration time of the data acquisition in seconds.
   :param init_duration: The relaxation time or dead time.
   :param repetitions: The amount of times the TimeableSchedule will be repeated.


.. py:function:: nv_dark_esr_sched(qubit: str, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generates a schedule for a dark ESR experiment on an NV-center.

   The spectroscopy frequency is taken from the device element. Please use the clock
   specified in the `spectroscopy_operation` entry of the device config.

   :param qubit: Name of the `DeviceElement` representing the NV-center.
   :param repetitions: Number of schedule repetitions.

   :returns: :
                 TimeableSchedule with a single frequency



.. py:function:: nv_dark_esr_sched_nco(qubit: str, spec_clock: str, spec_frequencies: numpy.ndarray, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Generates a schedule for a dark ESR experiment on an NV-center, in which
   the NCO frequency is swept.

   :param qubit: Name of the `DeviceElement` representing the NV-center.
   :param spec_clock: Reference clock of the spectroscopy operation.
   :param spec_frequencies: Sample frequencies for the spectroscopy pulse in Hertz.
   :param repetitions: Number of schedule repetitions.

   :returns: :
                 TimeableSchedule with NCO frequency sweeping for spectroscopy operation.



