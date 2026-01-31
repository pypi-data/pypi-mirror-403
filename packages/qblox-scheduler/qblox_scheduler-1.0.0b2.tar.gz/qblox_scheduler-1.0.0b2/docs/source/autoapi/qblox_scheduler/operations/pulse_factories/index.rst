pulse_factories
===============

.. py:module:: qblox_scheduler.operations.pulse_factories 

.. autoapi-nested-parse::

   A module containing factory functions for pulses on the quantum-device layer.

   These factories are used to take a parametrized representation of on a operation
   and use that to create an instance of the operation itself.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.pulse_factories.rxy_drag_pulse
   qblox_scheduler.operations.pulse_factories.rxy_gauss_pulse
   qblox_scheduler.operations.pulse_factories.phase_shift
   qblox_scheduler.operations.pulse_factories.composite_square_pulse
   qblox_scheduler.operations.pulse_factories.rxy_pulse
   qblox_scheduler.operations.pulse_factories.nv_spec_pulse_mw
   qblox_scheduler.operations.pulse_factories.spin_init_pulse
   qblox_scheduler.operations.pulse_factories.non_implemented_pulse



.. py:function:: rxy_drag_pulse(amp180: float, beta: float, theta: float, phi: float, port: str, duration: float, clock: str, reference_magnitude: qblox_scheduler.operations.pulse_library.ReferenceMagnitude | None = None) -> qblox_scheduler.operations.pulse_library.DRAGPulse

   Generate a :class:`~.operations.pulse_library.DRAGPulse` that achieves the right
   rotation angle ``theta`` based on a calibrated pi-pulse amplitude and beta
   parameter based on linear interpolation of the pulse amplitudes.

   :param amp180: Unitless amplitude of excitation pulse to get the maximum 180 degree theta.
   :param beta: Unitless amplitude of the derivative component, the DRAG-pulse parameter.
   :param theta: Angle in degrees to rotate around an equatorial axis on the Bloch sphere.
   :param phi: Phase of the pulse in degrees.
   :param port: Name of the port where the pulse is played.
   :param duration: Duration of the pulse in seconds.
   :param clock: Name of the clock used to modulate the pulse.
   :param reference_magnitude: Optional scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :type reference_magnitude: :class:`~qblox_scheduler.operations.pulse_library.ReferenceMagnitude`,

   :returns: :
                 DRAGPulse operation.



.. py:function:: rxy_gauss_pulse(amp180: float, theta: float, phi: float, port: str, duration: float, clock: str, reference_magnitude: qblox_scheduler.operations.pulse_library.ReferenceMagnitude | None = None) -> qblox_scheduler.operations.pulse_library.GaussPulse

   Generate a Gaussian drive with :class:`~.operations.pulse_library.GaussPulse` that achieves
   the right rotation angle ``theta`` based on a calibrated pi-pulse amplitude.

   :param amp180: Unitless amplitude of excitation pulse to get the maximum 180 degree theta.
   :param theta: Angle in degrees to rotate around an equatorial axis on the Bloch sphere.
   :param phi: Phase of the pulse in degrees.
   :param port: Name of the port where the pulse is played.
   :param duration: Duration of the pulse in seconds.
   :param clock: Name of the clock used to modulate the pulse.
   :param reference_magnitude: Optional scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :type reference_magnitude: :class:`~qblox_scheduler.operations.pulse_library.ReferenceMagnitude`,

   :returns: :
                 GaussPulse operation.



.. py:function:: phase_shift(theta: float, clock: str) -> qblox_scheduler.operations.pulse_library.ShiftClockPhase

   Generate a :class:`~.operations.pulse_library.ShiftClockPhase` that shifts the phase of the
   ``clock`` by an angle `theta`.

   :param theta: Angle to shift the clock by, in degrees.
   :param clock: Name of the clock to shift.

   :returns: :
                 ShiftClockPhase operation.



.. py:function:: composite_square_pulse(square_amp: float, square_duration: float, square_port: str, square_clock: str, virt_z_parent_qubit_phase: float, virt_z_parent_qubit_clock: str, virt_z_child_qubit_phase: float, virt_z_child_qubit_clock: str, reference_magnitude: qblox_scheduler.operations.pulse_library.ReferenceMagnitude | None = None, t0: float = 0) -> qblox_scheduler.schedules.TimeableSchedule

   An example composite pulse to implement a CZ gate.

   It applies the
   square pulse and then corrects for the phase shifts on both the device elements.

   :param square_amp: Amplitude of the square envelope.
   :param square_duration: The square pulse duration in seconds.
   :param square_port: Port of the pulse, must be capable of playing a complex waveform.
   :param square_clock: Clock used to modulate the pulse.
   :param virt_z_parent_qubit_phase: The phase shift in degrees applied to the parent qubit.
   :param virt_z_parent_qubit_clock: The clock of which to shift the phase applied to the parent qubit.
   :param virt_z_child_qubit_phase: The phase shift in degrees applied to the child qubit.
   :param virt_z_child_qubit_clock: The clock of which to shift the phase applied to the child qubit.
   :param reference_magnitude: Optional scaling value and unit for the unitless amplitude. Uses settings in
                               hardware config if not provided.
   :type reference_magnitude: :class:`~qblox_scheduler.operations.pulse_library.ReferenceMagnitude`,
   :param t0: Time in seconds when to start the pulses relative to the start time
              of the Operation in the TimeableSchedule.

   :returns: :
                 SquarePulse operation.



.. py:function:: rxy_pulse(amp180: float, skewness: float, theta: float, phi: float, port: str, duration: float, clock: str, pulse_shape: Literal['SkewedHermitePulse', 'GaussPulse'], reference_magnitude: qblox_scheduler.operations.pulse_library.ReferenceMagnitude | None = None) -> qblox_scheduler.operations.pulse_library.SkewedHermitePulse | qblox_scheduler.operations.pulse_library.GaussPulse

   Generate a Hermite or Gaussian drive pulse for a specified rotation on the Bloch sphere.

   The pulse achieves the desired rotation angle ``theta`` using a calibrated pi-pulse
   amplitude ``amp180``. The shape of the pulse can be either a skewed Hermite pulse or a
   Gaussian pulse, depending on the specified `pulse_shape`.

   :param amp180: Unitless amplitude of the excitation pulse for a 180-degree rotation.
   :type amp180: float
   :param skewness: Amplitude correction for the Hermite pulse. A value of 0 results in a standard
                    Hermite pulse.
   :type skewness: float
   :param theta: Rotation angle around an equatorial axis on the Bloch sphere, in degrees.
   :type theta: float
   :param phi: Phase of the pulse, in degrees.
   :type phi: float
   :param port: Name of the port where the pulse will be played.
   :type port: str
   :param duration: Duration of the pulse, in seconds.
   :type duration: float
   :param clock: Name of the clock used to modulate the pulse.
   :type clock: str
   :param pulse_shape: Shape of the pulse to be generated.
   :type pulse_shape: Literal["SkewedHermitePulse", "GaussPulse"]
   :param reference_magnitude: Reference magnitude for hardware configuration. If not provided, defaults to `None`.
   :type reference_magnitude: pulse_library.ReferenceMagnitude | None, Optional

   :returns: pulse_library.SkewedHermitePulse | pulse_library.GaussPulse
                 The generated pulse operation based on the specified shape and parameters.



.. py:function:: nv_spec_pulse_mw(duration: float, amplitude: float, clock: str, port: str, pulse_shape: Literal['SquarePulse', 'SkewedHermitePulse', 'GaussPulse'], reference_magnitude: qblox_scheduler.operations.pulse_library.ReferenceMagnitude | None = None) -> qblox_scheduler.operations.pulse_library.SquarePulse | qblox_scheduler.operations.pulse_library.SkewedHermitePulse | qblox_scheduler.operations.pulse_library.GaussPulse

   Generate a microwave pulse for spectroscopy experiments.

   The pulse can take one of three shapes: Square, Skewed Hermite, or Gaussian,
   based on the specified `pulse_shape`. This function supports frequency-modulated
   pulses for spectroscopy applications.

   :param duration: Duration of the pulse, in seconds.
   :type duration: float
   :param amplitude: Amplitude of the pulse.
   :type amplitude: float
   :param clock: Name of the clock used for frequency modulation.
   :type clock: str
   :param port: Name of the port where the pulse is applied.
   :type port: str
   :param pulse_shape: Shape of the pulse. The default is "SquarePulse".
   :type pulse_shape: Literal["SquarePulse", "SkewedHermitePulse", "GaussPulse"]
   :param reference_magnitude: Scaling value and unit for the unitless amplitude. If not provided,
                               settings from the hardware configuration are used.
   :type reference_magnitude: pulse_library.ReferenceMagnitude | None, Optional

   :returns: pulse_library.SquarePulse | pulse_library.SkewedHermitePulse | pulse_library.GaussPulse
                 The generated pulse operation based on the specified shape and parameters.



.. py:function:: spin_init_pulse(square_duration: float, ramp_diff: float, parent_port: str, parent_clock: str, parent_square_amp: float, parent_ramp_amp: float, parent_ramp_rate: float, child_port: str, child_clock: str, child_square_amp: float, child_ramp_amp: float, child_ramp_rate: float) -> qblox_scheduler.schedules.TimeableSchedule

   Device compilation of the spin init operation.


.. py:function:: non_implemented_pulse(**kwargs) -> qblox_scheduler.schedules.TimeableSchedule

   Raise an error indicating that the requested gate or pulse is not implemented.


