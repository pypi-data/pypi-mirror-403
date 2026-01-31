nv_element
==========

.. py:module:: qblox_scheduler.device_under_test.nv_element 

.. autoapi-nested-parse::

   Device elements for NV centers.

   Currently only for the electronic qubit,
   but could be extended for other qubits (eg. carbon qubit).



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.device_under_test.nv_element.Ports
   qblox_scheduler.device_under_test.nv_element.ClockFrequencies
   qblox_scheduler.device_under_test.nv_element.SpectroscopyOperationNV
   qblox_scheduler.device_under_test.nv_element.ResetSpinpump
   qblox_scheduler.device_under_test.nv_element.Measure
   qblox_scheduler.device_under_test.nv_element.ChargeReset
   qblox_scheduler.device_under_test.nv_element.CRCount
   qblox_scheduler.device_under_test.nv_element.RxyNV
   qblox_scheduler.device_under_test.nv_element.BasicElectronicNVElement




.. py:class:: Ports(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing the ports.


   .. py:attribute:: microwave
      :type:  str
      :value: None


      Name of the element's microwave port.


   .. py:attribute:: optical_control
      :type:  str
      :value: None


      Port to control the device element with optical pulses.


   .. py:attribute:: optical_readout
      :type:  str
      :value: None


      Port to readout photons from the device element.


   .. py:method:: _fill_defaults() -> None


.. py:class:: ClockFrequencies(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule with clock frequencies specifying the transitions to address.


   .. py:attribute:: f01
      :type:  qblox_scheduler.structure.types.Frequency
      :value: None


      Microwave frequency to resonantly drive the electron spin state of a
      negatively charged diamond NV center from the 0-state to 1-state
      :cite:t:`DOHERTY20131`.


   .. py:attribute:: spec
      :type:  qblox_scheduler.structure.types.Frequency
      :value: None


      Parameter that is swept for a spectroscopy measurement. It does not track
      properties of the device element.


   .. py:attribute:: ge0
      :type:  qblox_scheduler.structure.types.Frequency
      :value: None


      Transition frequency from the m_s=0 state to the E_x,y state.


   .. py:attribute:: ge1
      :type:  qblox_scheduler.structure.types.Frequency
      :value: None


      Transition frequency from the m_s=+-1 state to any of the A_1, A_2, or
      E_1,2 states.


   .. py:attribute:: ionization
      :type:  qblox_scheduler.structure.types.Frequency
      :value: None


      Frequency of the green ionization laser for manipulation of the NVs charge state.


.. py:class:: SpectroscopyOperationNV(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Convert the SpectroscopyOperation into a hermite, square, or gaussian microwave pulse.

   This class contains parameters with a certain amplitude and duration for
   spin-state manipulation.

   The modulation frequency of the pulse is determined by the clock ``spec`` in
   :class:`~.ClockFrequencies`.


   .. py:attribute:: amplitude
      :type:  qblox_scheduler.structure.types.Amplitude
      :value: None


      Amplitude of spectroscopy pulse.


   .. py:attribute:: duration
      :type:  qblox_scheduler.structure.types.Duration
      :value: None


      Duration of the MW pulse.


   .. py:attribute:: pulse_shape
      :type:  Literal['SquarePulse', 'SkewedHermitePulse', 'GaussPulse']
      :value: None


      Shape of the MW pulse.


.. py:class:: ResetSpinpump(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing parameters to run the spinpump laser with a square pulse.

   This should reset the NV to the :math:`|0\rangle` state.


   .. py:attribute:: amplitude
      :type:  qblox_scheduler.structure.types.Amplitude
      :value: None


      Amplitude of reset pulse.


   .. py:attribute:: duration
      :type:  qblox_scheduler.structure.types.Duration
      :value: None


      Duration of reset pulse.


.. py:class:: Measure(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing parameters to read out the spin state of the NV center.

   Excitation with a readout laser from the :math:`|0\rangle` to an excited state.
   Acquisition of photons when decaying back into the :math:`|0\rangle` state.


   .. py:attribute:: pulse_amplitude
      :type:  qblox_scheduler.structure.types.Amplitude
      :value: None


      Amplitude of readout pulse.


   .. py:attribute:: pulse_duration
      :type:  qblox_scheduler.structure.types.Duration
      :value: None


      Readout pulse duration.


   .. py:attribute:: acq_duration
      :type:  qblox_scheduler.structure.types.Duration
      :value: None


      Duration of the acquisition.


   .. py:attribute:: acq_delay
      :type:  qblox_scheduler.structure.types.Delay
      :value: None


      Delay between the start of the readout pulse and the start of the acquisition.


   .. py:attribute:: acq_channel
      :type:  collections.abc.Hashable
      :value: None


      Acquisition channel of this device element.


   .. py:attribute:: time_source
      :type:  qblox_scheduler.enums.TimeSource
      :value: None


      Optional time source, in case the
      :class:`~qblox_scheduler.operations.acquisition_library.Timetag` acquisition
      protocols are used. Please see that protocol for more information.


   .. py:attribute:: time_ref
      :type:  qblox_scheduler.enums.TimeRef
      :value: None


      Optional time reference, in case
      :class:`~qblox_scheduler.operations.acquisition_library.Timetag` or
      :class:`~qblox_scheduler.operations.acquisition_library.TimetagTrace`
      acquisition protocols are used. Please see those protocols for more information.


.. py:class:: ChargeReset(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing parameters to run an ionization laser square pulse to reset the NV.

   After resetting, the qubit should be in its negatively charged state.


   .. py:attribute:: amplitude
      :type:  qblox_scheduler.structure.types.Amplitude
      :value: None


      Amplitude of charge reset pulse.


   .. py:attribute:: duration
      :type:  qblox_scheduler.structure.types.Duration
      :value: None


      Duration of the charge reset pulse.


.. py:class:: CRCount(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing parameters to run the ionization laser and the spin pump laser.

   This uses a photon count to perform a charge and resonance count.


   .. py:attribute:: readout_pulse_amplitude
      :type:  qblox_scheduler.structure.types.Amplitude
      :value: None


      Amplitude of readout pulse.


   .. py:attribute:: spinpump_pulse_amplitude
      :type:  qblox_scheduler.structure.types.Amplitude
      :value: None


      Amplitude of spin-pump pulse.


   .. py:attribute:: readout_pulse_duration
      :type:  qblox_scheduler.structure.types.Duration
      :value: None


      Readout pulse duration.


   .. py:attribute:: spinpump_pulse_duration
      :type:  qblox_scheduler.structure.types.Duration
      :value: None


      Spin-pump pulse duration.


   .. py:attribute:: acq_duration
      :type:  qblox_scheduler.structure.types.Duration
      :value: None


      Duration of the acquisition.


   .. py:attribute:: acq_delay
      :type:  qblox_scheduler.structure.types.Delay
      :value: None


      Delay between the start of the readout pulse and the start of the acquisition.


   .. py:attribute:: acq_channel
      :type:  collections.abc.Hashable
      :value: None


      Default acquisition channel of this device element.


.. py:class:: RxyNV(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing parameters to perform an Rxy operation
   using a Hermite or Gaussian pulse.


   .. py:attribute:: amp180
      :type:  qblox_scheduler.structure.types.Amplitude
      :value: None


      Amplitude of :math:`\pi` pulse.


   .. py:attribute:: skewness
      :type:  float
      :value: None


      First-order amplitude to the Hermite pulse envelope.


   .. py:attribute:: duration
      :type:  qblox_scheduler.structure.types.Duration
      :value: None


      Duration of the pi pulse.


   .. py:attribute:: pulse_shape
      :type:  Literal['SkewedHermitePulse', 'GaussPulse']
      :value: None


      Shape of the pi pulse.


.. py:class:: BasicElectronicNVElement(/, name, **data: Any)

   Bases: :py:obj:`qblox_scheduler.device_under_test.device_element.DeviceElement`


   A device element representing an electronic qubit in an NV center.

   The submodules contain the necessary device element parameters to translate higher-level
   operations into pulses. Please see the documentation of these classes.

   .. admonition:: Examples

       Qubit parameters can be set through submodule attributes

       .. jupyter-execute::

           from qblox_scheduler import BasicElectronicNVElement

           device_element = BasicElectronicNVElement("q2")

           device_element.rxy.amp180 = 0.1
           device_element.measure.pulse_amplitude = 0.25
           device_element.measure.pulse_duration = 300e-9
           device_element.measure.acq_delay = 430e-9
           device_element.measure.acq_duration = 1e-6
           ...



   .. py:attribute:: element_type
      :type:  Literal['BasicElectronicNVElement']
      :value: 'BasicElectronicNVElement'



   .. py:attribute:: spectroscopy_operation
      :type:  SpectroscopyOperationNV


   .. py:attribute:: ports
      :type:  Ports


   .. py:attribute:: clock_freqs
      :type:  ClockFrequencies


   .. py:attribute:: reset
      :type:  ResetSpinpump


   .. py:attribute:: charge_reset
      :type:  ChargeReset


   .. py:attribute:: measure
      :type:  Measure


   .. py:attribute:: pulse_compensation
      :type:  qblox_scheduler.device_under_test.transmon_element.PulseCompensationModule


   .. py:attribute:: cr_count
      :type:  CRCount


   .. py:attribute:: rxy
      :type:  RxyNV


   .. py:method:: _generate_config() -> dict[str, dict[str, qblox_scheduler.backends.graph_compilation.OperationCompilationConfig]]

      Generate part of the device configuration specific to a single qubit.

      This method is intended to be used when this object is part of a
      device object containing multiple elements.



   .. py:method:: generate_device_config() -> qblox_scheduler.backends.graph_compilation.DeviceCompilationConfig

      Generate a valid device config for the qblox-scheduler.

      This makes use of the
      :func:`~.circuit_to_device.compile_circuit_to_device_with_config_validation` function.

      This enables the settings of this qubit to be used in isolation.

      .. note:

          This config is only valid for single qubit experiments.



