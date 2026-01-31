operations
==========

.. py:module:: qblox_scheduler.operations 

.. autoapi-nested-parse::

   Module containing the standard library of commonly used operations as well as the
   :class:`.Operation` class.


   .. tip::

       Quantify scheduler can trivially be extended by creating custom operations. Take a
       look at e.g., the pulse library for examples on how to implement custom pulses.



Subpackages
-----------
.. toctree::
   :titlesonly:
   :maxdepth: 3

   hardware_operations/index.rst


Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   acquisition_library/index.rst
   composite_factories/index.rst
   conditional_reset/index.rst
   control_flow_library/index.rst
   expressions/index.rst
   gate_library/index.rst
   loop_domains/index.rst
   measurement_factories/index.rst
   nv_native_library/index.rst
   operation/index.rst
   pulse_compensation_library/index.rst
   pulse_factories/index.rst
   pulse_library/index.rst
   shared_native_library/index.rst
   spin_library/index.rst
   variables/index.rst


Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.Acquisition
   qblox_scheduler.operations.DualThresholdedTriggerCount
   qblox_scheduler.operations.NumericalSeparatedWeightedIntegration
   qblox_scheduler.operations.NumericalWeightedIntegration
   qblox_scheduler.operations.SSBIntegrationComplex
   qblox_scheduler.operations.ThresholdedAcquisition
   qblox_scheduler.operations.ThresholdedTriggerCount
   qblox_scheduler.operations.Timetag
   qblox_scheduler.operations.TimetagTrace
   qblox_scheduler.operations.Trace
   qblox_scheduler.operations.TriggerCount
   qblox_scheduler.operations.WeightedIntegratedSeparated
   qblox_scheduler.operations.WeightedThresholdedAcquisition
   qblox_scheduler.operations.ConditionalReset
   qblox_scheduler.operations.ConditionalOperation
   qblox_scheduler.operations.ControlFlowOperation
   qblox_scheduler.operations.ControlFlowSpec
   qblox_scheduler.operations.LoopOperation
   qblox_scheduler.operations.LoopStrategy
   qblox_scheduler.operations.DType
   qblox_scheduler.operations.CNOT
   qblox_scheduler.operations.CZ
   qblox_scheduler.operations.X90
   qblox_scheduler.operations.Y90
   qblox_scheduler.operations.Z90
   qblox_scheduler.operations.H
   qblox_scheduler.operations.Measure
   qblox_scheduler.operations.Reset
   qblox_scheduler.operations.Rxy
   qblox_scheduler.operations.Rz
   qblox_scheduler.operations.S
   qblox_scheduler.operations.SDagger
   qblox_scheduler.operations.T
   qblox_scheduler.operations.TDagger
   qblox_scheduler.operations.X
   qblox_scheduler.operations.Y
   qblox_scheduler.operations.Z
   qblox_scheduler.operations.InlineQ1ASM
   qblox_scheduler.operations.LatchReset
   qblox_scheduler.operations.SimpleNumericalPulse
   qblox_scheduler.operations.ChargeReset
   qblox_scheduler.operations.CRCount
   qblox_scheduler.operations.Operation
   qblox_scheduler.operations.PulseCompensation
   qblox_scheduler.operations.ChirpPulse
   qblox_scheduler.operations.DRAGPulse
   qblox_scheduler.operations.GaussPulse
   qblox_scheduler.operations.IdlePulse
   qblox_scheduler.operations.MarkerPulse
   qblox_scheduler.operations.NumericalPulse
   qblox_scheduler.operations.RampPulse
   qblox_scheduler.operations.ReferenceMagnitude
   qblox_scheduler.operations.ResetClockPhase
   qblox_scheduler.operations.SetClockFrequency
   qblox_scheduler.operations.ShiftClockPhase
   qblox_scheduler.operations.SkewedHermitePulse
   qblox_scheduler.operations.SoftSquarePulse
   qblox_scheduler.operations.SquarePulse
   qblox_scheduler.operations.StaircasePulse
   qblox_scheduler.operations.SuddenNetZeroPulse
   qblox_scheduler.operations.Timestamp
   qblox_scheduler.operations.VoltageOffset
   qblox_scheduler.operations.WindowOperation



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.long_chirp_pulse
   qblox_scheduler.operations.long_ramp_pulse
   qblox_scheduler.operations.long_square_pulse
   qblox_scheduler.operations.staircase_pulse
   qblox_scheduler.operations.arange
   qblox_scheduler.operations.linspace
   qblox_scheduler.operations.composite_square_pulse
   qblox_scheduler.operations.non_implemented_pulse
   qblox_scheduler.operations.nv_spec_pulse_mw
   qblox_scheduler.operations.phase_shift
   qblox_scheduler.operations.rxy_drag_pulse
   qblox_scheduler.operations.rxy_gauss_pulse
   qblox_scheduler.operations.rxy_pulse
   qblox_scheduler.operations.spin_init_pulse



.. py:class:: Acquisition(name: str)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   An operation representing data acquisition at the quantum-device abstraction layer.

   An Acquisition must consist of (at least) an AcquisitionProtocol specifying how the
   acquired signal is to be processed, and an AcquisitionChannel and AcquisitionIndex
   specifying where the acquired data is to be stored in the RawDataset.


   N.B. This class helps differentiate an acquisition operation from the regular
   operations. This enables us to use
   :func:`~.qblox_scheduler.schedules._visualization.pulse_diagram.plot_acquisition_operations`
   to highlight acquisition pulses in the pulse diagrams.


.. py:class:: DualThresholdedTriggerCount(port: str, clock: str, duration: float, threshold_low: int, threshold_high: int, *, label_low: str | None = None, label_mid: str | None = None, label_high: str | None = None, label_invalid: str | None = None, acq_channel: collections.abc.Hashable = 0, coords: dict | None = None, acq_index: int | None = None, bin_mode: qblox_scheduler.enums.BinMode | str = BinMode.APPEND, t0: float = 0)

   Bases: :py:obj:`Acquisition`


   Thresholded trigger count protocol that uses two thresholds.

   Four outcomes are possible for this measurement, and each of those four can be assigned a label
   to use in a :class:`~qblox_scheduler.operations.control_flow_library.ConditionalOperation`:

   - "low" if ``counts < threshold_low``,
   - "mid" if ``threshold_low <= counts < threshold_high``,
   - "high" if ``counts >= threshold_high``,
   - "invalid" if the counts are invalid (can occur in very rare cases, e.g. when the counter
     overflows).

   The returned acquisition data is the raw number of counts.

   .. important::

       The exact duration of this operation, and the possible bin modes may depend on the control
       hardware. Please consult your hardware vendor's :ref:`Reference guide` for more information.

   :param port: The acquisition port.
   :param clock: The clock used to demodulate the acquisition.
   :param duration: The duration of the operation in seconds.
   :param threshold_low: The lower counts threshold of the ThresholdedTriggerCount acquisition.
   :param threshold_high: The upper counts threshold of the ThresholdedTriggerCount acquisition.
   :param label_low: The label that can be used to link a result of `counts < threshold_low` to a
                     ConditionalOperation, by default None.
   :param label_mid: The label that can be used to link a result of `threshold_low <= counts < threshold_high` to
                     a ConditionalOperation, by default None.
   :param label_high: The label that can be used to link a result of `counts >= threshold_high` to a
                      ConditionalOperation, by default None.
   :param label_invalid: The label that can be used to link an invalid counts result (e.g. a counter overflow) to a
                         ConditionalOperation, by default None.
   :param feedback_trigger_condition: The comparison condition (greater-equal, less-than) for the ThresholdedTriggerCount
                                      acquisition.
   :param acq_channel: The data channel in which the acquisition is stored, by default 0.  Describes the "where"
                       information of the measurement, which typically corresponds to a qubit idx.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Deprecated.
                     The data register in which the acquisition is stored, by default ``None``.
                     Describes the "when"
                     information of the measurement, used to label or tag individual measurements in a large
                     circuit. Typically corresponds to the setpoints of a schedule (e.g., tau in a T1
                     experiment).
   :param bin_mode: Describes what is done when data is written to a register that already contains a value.
                    Options are "append" which appends the result to the list or "average" which stores the
                    count value of the new result and the old register value, by default BinMode.APPEND.
   :param t0: The acquisition start time in seconds, by default 0.


.. py:class:: NumericalSeparatedWeightedIntegration(port: str, clock: str, weights_a: list[complex] | numpy.ndarray, weights_b: list[complex] | numpy.ndarray, weights_sampling_rate: float = 1000000000.0, interpolation: str = 'linear', acq_channel: collections.abc.Hashable = 0, coords: dict | None = None, acq_index: int | None = None, bin_mode: qblox_scheduler.enums.BinMode | str = BinMode.AVERAGE_APPEND, phase: float = 0, t0: float = 0)

   Bases: :py:obj:`WeightedIntegratedSeparated`


   Subclass of :class:`~WeightedIntegratedSeparated` with parameterized waveforms as weights.

   A WeightedIntegratedSeparated class using parameterized waveforms and
   interpolation as the integration weights.

   Weights are applied as:

   .. math::

       \widetilde{A} = \int \mathrm{Re}(S(t)\cdot W_A(t) \mathrm{d}t

   .. math::

       \widetilde{B} = \int \mathrm{Im}(S(t))\cdot W_B(t) \mathrm{d}t

   :param port: The acquisition port.
   :param clock: The clock used to demodulate the acquisition.
   :param weights_a: The list of complex values used as weights :math:`A(t)` on
                     the incoming complex signal.
   :param weights_b: The list of complex values used as weights :math:`B(t)` on
                     the incoming complex signal.
   :param weights_sampling_rate: The rate with which the weights have been sampled, in Hz. By default equal
                                 to 1 GHz. Note that during hardware compilation, the weights will be resampled
                                 with the sampling rate supported by the target hardware.
   :param interpolation: The type of interpolation to use, by default "linear". This argument is
                         passed to :obj:`~scipy.interpolate.interp1d`.
   :param acq_channel: The data channel in which the acquisition is stored, by default 0.
                       Describes the "where" information of the  measurement, which typically
                       corresponds to a device element idx.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Deprecated.
                     The data register in which the acquisition is stored, by default ``None``.
                     Describes the "when" information of the measurement, used to label or
                     tag individual measurements in a large circuit. Typically corresponds
                     to the setpoints of a schedule (e.g., tau in a T1 experiment).
   :param bin_mode: Describes what is done when data is written to a register that already
                    contains a value. Options are "append" which appends the result to the
                    list or "average" which stores the weighted average value of the
                    new result and the old register value, by default BinMode.APPEND.
   :param phase: The phase of the pulse and acquisition in degrees, by default 0.
   :param t0: The acquisition start time in seconds, by default 0.


.. py:class:: NumericalWeightedIntegration(port: str, clock: str, weights_a: list[complex] | numpy.ndarray, weights_b: list[complex] | numpy.ndarray, weights_sampling_rate: float = 1000000000.0, interpolation: str = 'linear', acq_channel: collections.abc.Hashable = 0, coords: dict | None = None, acq_index: int | None = None, bin_mode: qblox_scheduler.enums.BinMode | str = BinMode.AVERAGE_APPEND, phase: float = 0, t0: float = 0)

   Bases: :py:obj:`NumericalSeparatedWeightedIntegration`


   Subclass of :class:`~NumericalSeparatedWeightedIntegration` returning a complex number.

   :param port: The acquisition port.
   :param clock: The clock used to demodulate the acquisition.
   :param weights_a: The list of complex values used as weights :math:`A(t)` on
                     the incoming complex signal.
   :param weights_b: The list of complex values used as weights :math:`B(t)` on
                     the incoming complex signal.
   :param weights_sampling_rate: The rate with which the weights have been sampled, in Hz. By default equal
                                 to 1 GHz. Note that during hardware compilation, the weights will be resampled
                                 with the sampling rate supported by the target hardware.
   :param interpolation: The type of interpolation to use, by default "linear". This argument is
                         passed to :obj:`~scipy.interpolate.interp1d`.
   :param acq_channel: The data channel in which the acquisition is stored, by default 0.
                       Describes the "where" information of the  measurement, which typically
                       corresponds to a device element idx.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Deprecated.
                     The data register in which the acquisition is stored, by default ``None``.
                     Describes the "when" information of the measurement, used to label or
                     tag individual measurements in a large circuit. Typically corresponds
                     to the setpoints of a schedule (e.g., tau in a T1 experiment).
   :param bin_mode: Describes what is done when data is written to a register that already
                    contains a value. Options are "append" which appends the result to the
                    list or "average" which stores the weighted average value of the
                    new result and the old register value, by default BinMode.APPEND.
   :param phase: The phase of the pulse and acquisition in degrees, by default 0.
   :param t0: The acquisition start time in seconds, by default 0.


.. py:class:: SSBIntegrationComplex(port: str, clock: str, duration: float, acq_channel: collections.abc.Hashable = 0, coords: dict | None = None, acq_index: int | None = None, bin_mode: qblox_scheduler.enums.BinMode | str = BinMode.AVERAGE_APPEND, phase: float = 0, t0: float = 0)

   Bases: :py:obj:`Acquisition`


   Single sideband integration acquisition protocol with complex results.

   A weighted integrated acquisition on a complex signal using a
   square window for the acquisition weights.

   The signal is demodulated using the specified clock, and the
   square window then effectively specifies an integration window.

   :param port: The acquisition port.
   :param clock: The clock used to demodulate the acquisition.
   :param duration: The acquisition duration in seconds.
   :param acq_channel: The data channel in which the acquisition is stored, by default 0.
                       Describes the "where" information of the  measurement, which typically
                       corresponds to a device element idx.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Deprecated.
                     The data register in which the acquisition is stored, by default ``None``.
                     Describes the "when" information of the measurement, used to label or
                     tag individual measurements in a large circuit. Typically corresponds
                     to the setpoints of a schedule (e.g., tau in a T1 experiment).
   :param bin_mode: Describes what is done when data is written to a register that already
                    contains a value. Options are "append" which appends the result to the
                    list or "average" which stores the weighted average value of the
                    new result and the old register value, by default BinMode.AVERAGE.
   :param phase: The phase of the pulse and acquisition in degrees, by default 0.
   :param t0: The acquisition start time in seconds, by default 0.


.. py:class:: ThresholdedAcquisition(port: str, clock: str, duration: float, acq_channel: collections.abc.Hashable = 0, coords: dict | None = None, acq_index: int | None = None, bin_mode: qblox_scheduler.enums.BinMode | str = BinMode.AVERAGE_APPEND, feedback_trigger_label: str | None = None, phase: float = 0, t0: float = 0, acq_rotation: float = 0, acq_threshold: float = 0)

   Bases: :py:obj:`Acquisition`


   Acquisition protocol allowing to control rotation and threshold.

   This acquisition protocol is similar to the :class:`~.SSBIntegrationComplex`
   acquisition protocol, but the complex result is now rotated and thresholded
   to produce a "0" or a "1", as controlled by the parameters for rotation
   angle `<device_element>.measure.acq_rotation` and threshold value
   `<device_element>.measure.acq_threshold` in the device configuration (see example
   below).

   The rotation angle and threshold value for each qubit can be set through
   the device configuration.

   .. admonition:: Note

       Thresholded acquisition is currently only supported by the Qblox
       backend.

   .. admonition:: Examples

       .. jupyter-execute::

           from qblox_scheduler import TimeableSchedule
           from qblox_scheduler.device_under_test.transmon_element import BasicTransmonElement
           from qblox_scheduler.operations.acquisition_library import ThresholdedAcquisition

           # set up qubit
           device_element = BasicTransmonElement("q0")
           device_element.clock_freqs.readout = 8.0e9

           # set rotation and threshold value
           rotation, threshold = 20, -0.1
           device_element.measure.acq_rotation = rotation
           device_element.measure.acq_threshold = threshold

           # basic schedule
           schedule = TimeableSchedule("thresholded acquisition")
           schedule.add(ThresholdedAcquisition(port="q0:res", clock="q0.ro", duration=1e-6))


   :param port: The acquisition port.
   :type port: str
   :param clock: The clock used to demodulate the acquisition.
   :type clock: str
   :param duration: The acquisition duration in seconds.
   :type duration: float
   :param acq_channel: The data channel in which the acquisition is stored, by default 0.
                       Describes the "where" information of the  measurement, which
                       typically corresponds to a device element idx.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Deprecated.
                     The data register in which the acquisition is stored, by default ``None``.
                     Describes the "when" information of the measurement, used to label
                     or tag individual measurements in a large circuit. Typically
                     corresponds to the setpoints of a schedule (e.g., tau in a T1
                     experiment).
   :param bin_mode: Describes what is done when data is written to a register that
                    already contains a value. Options are "append" which appends the
                    result to the list or "average" which stores the weighted average
                    value of the new result and the old register value, by default
                    BinMode.AVERAGE.
   :type bin_mode: BinMode or str
   :param feedback_trigger_label: The label corresponding to the feedback trigger, which is mapped by the
                                  compiler to a feedback trigger address on hardware, by default None.
   :type feedback_trigger_label: str
   :param phase: The phase of the pulse and acquisition in degrees, by default 0.
   :type phase: float
   :param t0: The acquisition start time in seconds, by default 0.
   :type t0: float


.. py:class:: ThresholdedTriggerCount(port: str, clock: str, duration: float, threshold: int, *, feedback_trigger_label: str | None = None, feedback_trigger_condition: str | qblox_scheduler.enums.TriggerCondition = TriggerCondition.GREATER_THAN_EQUAL_TO, acq_channel: collections.abc.Hashable = 0, coords: dict | None = None, acq_index: int | None = None, bin_mode: qblox_scheduler.enums.BinMode | str = BinMode.APPEND, t0: float = 0)

   Bases: :py:obj:`Acquisition`


   Thresholded trigger counting acquisition protocol returning the comparison result with a
   threshold.

   If the number of triggers counted is less than the threshold, a 0 is returned, otherwise a 1.

   The analog threshold for registering a single count is set in the hardware configuration.

   .. important::

       The exact duration of this operation, and the possible bin modes may depend on the control
       hardware. Please consult your hardware vendor's :ref:`Reference guide` for more information.

   :param port: The acquisition port.
   :param clock: The clock used to demodulate the acquisition.
   :param duration: The duration of the operation in seconds.
   :param threshold: The threshold of the ThresholdedTriggerCount acquisition.
   :param feedback_trigger_label: The label corresponding to the feedback trigger, which is mapped by the compiler to a
                                  feedback trigger address on hardware, by default None.
                                  Note: this label is merely used to link this acquisition together with a
                                  ConditionalOperation. It does not affect the acquisition result.
   :param feedback_trigger_condition: The comparison condition (greater-equal, less-than) for the ThresholdedTriggerCount
                                      acquisition.
   :param acq_channel: The data channel in which the acquisition is stored, by default 0.  Describes the "where"
                       information of the measurement, which typically corresponds to a qubit idx.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Deprecated.
                     The data register in which the acquisition is stored, by default ``None``.
                     Describes the "when"
                     information of the measurement, used to label or tag individual measurements in a large
                     circuit. Typically corresponds to the setpoints of a schedule (e.g., tau in a T1
                     experiment).
   :param bin_mode: Describes what is done when data is written to a register that already contains a value.
                    Options are "append" which appends the result to the list or "average" which stores the
                    count value of the new result and the old register value, by default BinMode.APPEND.
   :param t0: The acquisition start time in seconds, by default 0.


.. py:class:: Timetag(duration: float, port: str, clock: str = DigitalClockResource.IDENTITY, acq_channel: collections.abc.Hashable = 0, coords: dict | None = None, acq_index: int | None = None, bin_mode: qblox_scheduler.enums.BinMode | str = BinMode.APPEND, time_source: qblox_scheduler.enums.TimeSource | str = TimeSource.FIRST, time_ref: qblox_scheduler.enums.TimeRef | str = TimeRef.START, time_ref_port: str | None = None, t0: float = 0, fine_start_delay: float = 0, fine_end_delay: float = 0)

   Bases: :py:obj:`Acquisition`


   Acquire a single timetag per acquisition index.

   .. important::

       The exact duration of this operation, and the possible bin modes may depend on
       the control hardware. Please consult your hardware vendor's :ref:`Reference
       guide` for more information.

   :param port: The acquisition port.
   :param clock: The clock used to demodulate the acquisition.
   :param duration: The acquisition duration in seconds.
   :param acq_channel: The data channel in which the acquisition is stored, by default 0.
                       Describes the "where" information of the  measurement, which typically
                       corresponds to a device element idx.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Deprecated.
                     The data register in which the acquisition is stored, by default ``None``.
                     Describes the "when" information of the measurement, used to label or
                     tag individual measurements in a large circuit. Typically corresponds
                     to the setpoints of a schedule (e.g., tau in a T1 experiment).
   :param bin_mode: Describes what is done when data is written to a register that already
                    contains a value. Options are "append" which appends the result to the
                    list or "average" which stores the weighted average value of the
                    new result and the old register value, by default BinMode.APPEND.
   :param time_source: Selects the timetag data source for this acquisition type. String enumeration,
                       one of:

                       * ``first`` (default): record the first timetag in the window.
                       * ``second``: record the second timetag in the window. Can be used to measure
                         pulse distance when combined with first as reference.
                       * ``last``: record the last timetag in the window.
   :param time_ref: Selects the time reference that the timetag is recorded in relation to. String
                    enumeration, one of:

                    * ``start`` (default): record relative to the start of the window.
                    * ``end``: record relative to the end of the window. Note that this always
                      yields a negative timetag.
                    * ``first``: record relative to the first timetag in the window.
                    * ``timestamp``: record relative to the timestamp marked using the
                      :class:`~qblox_scheduler.operations.pulse_library.Timestamp` operation.
                    * ``port``: record relative to the timetag measured on another port. If this
                      option is used, the ``time_ref_port`` argument must be specified as well. The
                      acquisition operation that is measuring the timetag on the *other* port must
                      end before or at the same time as *this* acquisition operation.
   :param time_ref_port: If the ``port`` time reference is used, ``time_ref_port`` specifies the port on
                         which the other acquisition is executed.
   :param t0: The acquisition start time in seconds, by default 0.
   :param fine_start_delay: Delays the start of the acquisition by the given amount in seconds. Does
                            not delay the start time of the operation in the schedule. If the
                            hardware supports it, this parameter can be used to shift the
                            acquisition window by a small amount of time, independent of the
                            hardware instruction timing grid. Currently only implemented for Qblox
                            QTM modules, which allow only positive values for this parameter. By
                            default 0.
   :param fine_end_delay: Delays the end of the pulse by the given amount. Does not delay the end
                          time of the operation in the schedule. If the hardware supports it, this
                          parameter can be used to shift the acquisition window by a small amount
                          of time, independent of the hardware instruction timing grid. Currently
                          only implemented for Qblox QTM modules, which allow only positive values
                          for this parameter. By default 0.


.. py:class:: TimetagTrace(duration: float, port: str, clock: str = DigitalClockResource.IDENTITY, acq_channel: collections.abc.Hashable = 0, coords: dict | None = None, acq_index: int | None = None, bin_mode: qblox_scheduler.enums.BinMode | str = BinMode.APPEND, time_ref: qblox_scheduler.enums.TimeRef | str = TimeRef.START, time_ref_port: str | None = None, t0: float = 0, fine_start_delay: float = 0, fine_end_delay: float = 0)

   Bases: :py:obj:`Acquisition`


   The TimetagTrace acquisition protocol records timetags within an acquisition window.

   .. important::

       The exact duration of this operation, and the possible bin modes may depend on
       the control hardware. Please consult your hardware vendor's :ref:`Reference
       guide` for more information.

   :param port: The acquisition port.
   :param clock: The clock used to demodulate the acquisition.
   :param duration: The acquisition duration in seconds.
   :param acq_channel: The data channel in which the acquisition is stored, is by default 0.
                       Describes the "where" information of the  measurement, which typically
                       corresponds to a device element idx.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Deprecated.
                     The data register in which the acquisition is stored, by default ``None``.
                     Describes the "when" information of the measurement, used to label or
                     tag individual measurements in a large circuit. Typically corresponds
                     to the setpoints of a schedule (e.g., tau in a T1 experiment).
   :param bin_mode: Describes what is done when data is written to a register that already
                    contains a value. Only "BinMode.APPEND" is available at the moment; this option
                    concatenates timetag results with the same acquisition channel and index.
   :param time_ref: Selects the time reference that the timetag is recorded in relation to. String
                    enumeration, one of:

                    * start (default): record relative to the start of the window.
                    * end: record relative to the end of the window. Note that this always yields a
                      negative timetag.
                    * first: syntactic sugar for first#, where # is the current channel.
                    * timestamp: record relative to the timestamp marked using the ``Timestamp`` operation.
                    * ``port``: record relative to the timetag measured on another port. If this
                      option is used, the ``time_ref_port`` argument must be specified as well. The
                      acquisition operation that is measuring the timetag on the *other* port must
                      end before or at the same time as *this* acquisition operation.
   :param time_ref_port: If the ``port`` time reference is used, ``time_ref_port`` specifies the port on
                         which the other acquisition is executed.
   :param t0: The acquisition start time in seconds, by default 0.
   :param fine_start_delay: Delays the start of the acquisition by the given amount in seconds. Does
                            not delay the start time of the operation in the schedule. If the
                            hardware supports it, this parameter can be used to shift the
                            acquisition window by a small amount of time, independent of the
                            hardware instruction timing grid. Currently only implemented for Qblox
                            QTM modules, which allow only positive values for this parameter. By
                            default 0.
   :param fine_end_delay: Delays the end of the pulse by the given amount in seconds. Does not
                          delay the end time of the operation in the schedule. If the hardware
                          supports it, this parameter can be used to shift the acquisition window
                          by a small amount of time, independent of the hardware instruction
                          timing grid. Currently only implemented for Qblox QTM modules, which
                          allow only positive values for this parameter. By default 0.


.. py:class:: Trace(duration: float, port: str, clock: str, acq_channel: collections.abc.Hashable = 0, coords: dict | None = None, acq_index: int | None = None, bin_mode: qblox_scheduler.enums.BinMode | str = BinMode.AVERAGE, t0: float = 0)

   Bases: :py:obj:`Acquisition`


   The Trace acquisition protocol measures a signal s(t).

   Only processing performed is rescaling and adding
   units based on a calibrated scale. Values are returned
   as a raw trace (numpy array of float datatype). Length of
   this array depends on the sampling rate of the acquisition
   device.

   .. important::

       The exact duration of this operation, and the possible bin modes may depend on
       the control hardware. Please consult your hardware vendor's :ref:`Reference
       guide` for more information.

   :param port: The acquisition port.
   :param clock: The clock used to demodulate the acquisition.
   :param duration: The acquisition duration in seconds.
   :param acq_channel: The data channel in which the acquisition is stored, is by default 0.
                       Describes the "where" information of the  measurement, which typically
                       corresponds to a device element idx.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Deprecated.
                     The data register in which the acquisition is stored, by default ``None``.
                     Describes the "when" information of the measurement, used to label or
                     tag individual measurements in a large circuit. Typically corresponds
                     to the setpoints of a schedule (e.g., tau in a T1 experiment).
   :param bin_mode: Describes what is done when data is written to a memory location that already
                    contains values. Which bin mode can be used for Trace acquisitions may depend on
                    the hardware. ``BinMode.AVERAGE``, the default, works on most hardware. This bin
                    mode stores the weighted average value of the new result and the old values.
                    ``BinMode.FIRST`` is used for hardware where only the result of the first
                    acquisition in a TimeableSchedule is stored, e.g. for a Trace acquisition with Qblox QTM
                    modules.
   :param t0: The acquisition start time in seconds, by default 0.


.. py:class:: TriggerCount(port: str, clock: str, duration: float, acq_channel: collections.abc.Hashable = 0, coords: dict | None = None, acq_index: int | None = None, bin_mode: qblox_scheduler.enums.BinMode | str = BinMode.APPEND, t0: float = 0, fine_start_delay: float = 0, fine_end_delay: float = 0)

   Bases: :py:obj:`Acquisition`


   Trigger counting acquisition protocol returning an integer.

   The trigger acquisition mode is used to measure how
   many times the trigger level is surpassed. The level is set
   in the hardware configuration.

   .. important::

       The exact duration of this operation, and the possible bin modes may depend on
       the control hardware. Please consult your hardware vendor's :ref:`Reference
       guide` for more information.

   :param port: The acquisition port.
   :param clock: The clock used to demodulate the acquisition.
   :param duration: The duration of the operation in seconds.
   :param acq_channel: The data channel in which the acquisition is stored, by default 0.
                       Describes the "where" information of the measurement, which typically
                       corresponds to a device element idx.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Deprecated.
                     The data register in which the acquisition is stored, by default ``None``.
                     Describes the "when" information of the measurement, used to label or
                     tag individual measurements in a large circuit. Typically corresponds
                     to the setpoints of a schedule (e.g., tau in a T1 experiment).
   :param bin_mode: Describes what is done when data is written to a register that already
                    contains a value. Options are "append" which appends the result to the
                    list or "distribution" which stores the count value of the
                    new result and the old register value, by default BinMode.APPEND.
   :param t0: The acquisition start time in seconds, by default 0.
   :param fine_start_delay: Delays the start of the acquisition by the given amount in seconds. Does
                            not delay the start time of the operation in the schedule. If the
                            hardware supports it, this parameter can be used to shift the
                            acquisition window by a small amount of time, independent of the
                            hardware instruction timing grid. Currently only implemented for Qblox
                            QTM modules, which allow only positive values for this parameter. By
                            default 0.
   :param fine_end_delay: Delays the end of the pulse by the given amount in seconds. Does not
                          delay the end time of the operation in the schedule. If the hardware
                          supports it, this parameter can be used to shift the acquisition window
                          by a small amount of time, independent of the hardware instruction
                          timing grid. Currently only implemented for Qblox QTM modules, which
                          allow only positive values for this parameter. By default 0.


.. py:class:: WeightedIntegratedSeparated(waveform_a: dict[str, Any], waveform_b: dict[str, Any], port: str, clock: str, duration: float, acq_channel: collections.abc.Hashable = 0, coords: dict | None = None, acq_index: int | None = None, bin_mode: qblox_scheduler.enums.BinMode | str = BinMode.AVERAGE_APPEND, phase: float = 0, t0: float = 0)

   Bases: :py:obj:`Acquisition`


   Weighted integration acquisition protocol where two sets weights
   are applied separately to the real and imaginary parts
   of the signal.

   Weights are applied as:

   .. math::

       \widetilde{A} = \int \mathrm{Re}(S(t))\cdot W_A(t) \mathrm{d}t

   .. math::

       \widetilde{B} = \int \mathrm{Im}(S(t))\cdot W_B(t) \mathrm{d}t

   :param waveform_a: The complex waveform used as integration weights :math:`W_A(t)`.
   :param waveform_b: The complex waveform used as integration weights :math:`W_B(t)`.
   :param port: The acquisition port.
   :param clock: The clock used to demodulate the acquisition.
   :param duration: The acquisition duration in seconds.
   :param acq_channel: The data channel in which the acquisition is stored, by default 0.
                       Describes the "where" information of the  measurement, which typically
                       corresponds to a device element idx.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Deprecated.
                     The data register in which the acquisition is stored, by default ``None``.
                     Describes the "when" information of the measurement, used to label or
                     tag individual measurements in a large circuit. Typically corresponds
                     to the setpoints of a schedule (e.g., tau in a T1 experiment).
   :param bin_mode: Describes what is done when data is written to a register that already
                    contains a value. Options are "append" which appends the result to the
                    list or "average" which stores the weighted average value of the
                    new result and the old register value, by default BinMode.APPEND.
   :param phase: The phase of the pulse and acquisition in degrees, by default 0.
   :param t0: The acquisition start time in seconds, by default 0.

   :raises NotImplementedError:


.. py:class:: WeightedThresholdedAcquisition(port: str, clock: str, weights_a: list[complex] | numpy.ndarray, weights_b: list[complex] | numpy.ndarray, weights_sampling_rate: float = 1000000000.0, interpolation: str = 'linear', acq_channel: collections.abc.Hashable = 0, coords: dict | None = None, acq_index: int | None = None, bin_mode: qblox_scheduler.enums.BinMode | str = BinMode.AVERAGE_APPEND, phase: float = 0, t0: float = 0, feedback_trigger_label: str | None = None, acq_rotation: float | None = None, acq_threshold: float = 0)

   Bases: :py:obj:`NumericalWeightedIntegration`


   Subclass of :class:`~NumericalWeightedIntegration` but Thresholded.

   Acquisition protocol allowing to control rotation and threshold.

   This acquisition protocol is similar to the :class:`~.SSBIntegrationComplex`
   acquisition protocol, but the complex result is now rotated and thresholded
   to produce a "0" or a "1", as controlled by the parameters for rotation
   angle `<qubit>.measure.acq_rotation` and threshold value
   `<qubit>.measure.acq_threshold` in the device configuration (see example
   below).

   The rotation angle and threshold value for each qubit can be set through
   the device configuration.

   .. admonition:: Note

       Thresholded acquisition is currently only supported by the Qblox
       backend.

   :param port: The acquisition port.
   :param clock: The clock used to demodulate the acquisition.
   :param weights_a: The list of complex values used as weights :math:`A(t)` on
                     the incoming complex signal.
   :param weights_b: The list of complex values used as weights :math:`B(t)` on
                     the incoming complex signal.
   :param weights_sampling_rate: The rate with which the weights have been sampled, in Hz. By default equal
                                 to 1 GHz. Note that during hardware compilation, the weights will be resampled
                                 with the sampling rate supported by the target hardware.
   :param interpolation: The type of interpolation to use, by default "linear". This argument is
                         passed to :obj:`~scipy.interpolate.interp1d`.
   :param acq_channel: The data channel in which the acquisition is stored, by default 0.
                       Describes the "where" information of the  measurement, which typically
                       corresponds to a qubit idx.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Deprecated.
                     The data register in which the acquisition is stored, by default ``None``.
                     Describes the "when" information of the measurement, used to label or
                     tag individual measurements in a large circuit. Typically corresponds
                     to the setpoints of a schedule (e.g., tau in a T1 experiment).
   :param bin_mode: Describes what is done when data is written to a register that already
                    contains a value. Options are "append" which appends the result to the
                    list or "average" which stores the weighted average value of the
                    new result and the old register value, by default BinMode.APPEND.
   :param phase: The phase of the pulse and acquisition in degrees, by default 0.
   :param t0: The acquisition start time in seconds, by default 0.
   :param feedback_trigger_label: The label corresponding to the feedback trigger, which is mapped by the
                                  compiler to a feedback trigger address on hardware, by default None.
   :type feedback_trigger_label: str


.. py:class:: ConditionalReset(qubit_name: str, name: str = 'conditional_reset', **kwargs)

   Bases: :py:obj:`qblox_scheduler.schedules.schedule.TimeableSchedule`


   Reset a qubit to the :math:`|0\rangle` state.

   The
   :class:`~qblox_scheduler.operations.conditional_reset.ConditionalReset`
   gate is a conditional gate that first measures the state of the device element using
   an
   :class:`~qblox_scheduler.operations.acquisition_library.ThresholdedAcquisition`
   operation and then performs a :math:`\pi` rotation on the condition that the
   measured state is :math:`|1\rangle`. If the measured state is in
   :math:`|0\rangle`, the hardware will wait the same amount of time the
   :math:`\pi` rotation would've taken to ensure that total execution time of
   :class:`~qblox_scheduler.operations.conditional_reset.ConditionalReset`
   is the same regardless of the measured state.

   .. note::

       The total time of the ConditionalReset is the sum of

        1) integration time (<device_element>.measure.integration_time)
        2) acquisition delay (<device_element>.measure.acq_delay)
        3) trigger delay (364ns)
        4) pi-pulse duration (<device_element>.rxy.duration)
        5) idle time (4ns)

   .. note::

       Due to current hardware limitations, overlapping conditional resets
       might not work correctly if multiple triggers are sent within a 364ns
       window. See :ref:`sec-qblox-conditional-playback` for more information.

   .. note::

       :class:`~qblox_scheduler.operations.conditional_reset.ConditionalReset`
       is currently implemented as a subschedule, but can be added to an
       existing schedule as if it were a gate. See examples below.

   :param name: The name of the conditional subschedule, by default "conditional_reset".
   :type name: str
   :param qubit_name: The name of the device element to reset to the :math:`|0\rangle` state.
   :type qubit_name: str
   :param \*\*kwargs: Additional keyword arguments are passed to
                      :class:`~qblox_scheduler.operations.gate_library.Measure`. e.g.
                      ``acq_channel``, ``acq_index``, and ``bin_mode``.

   .. rubric:: Examples

   .. jupyter-execute::
       :hide-output:

       from qblox_scheduler import Schedule
       from qblox_scheduler.operations import ConditionalReset

       schedule = Schedule("example schedule")
       schedule.add(ConditionalReset("q0"))


.. py:class:: ConditionalOperation(body: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.schedule.Schedule, qubit_name: str, t0: float = 0.0, hardware_buffer_time: float = constants.MIN_TIME_BETWEEN_OPERATIONS * 1e-09)

   Bases: :py:obj:`ControlFlowOperation`


   Conditional over another operation.

   If a preceding thresholded acquisition on ``qubit_name`` results in a "1", the
   body will be executed, otherwise it will generate a wait time that is
   equal to the time of the subschedule, to ensure the absolute timing of later
   operations remains consistent.

   :param body: Operation to be conditionally played
   :param qubit_name: Name of the device element on which the body will be conditioned
   :param t0: Time offset, by default 0
   :param hardware_buffer_time: Time buffer, by default the minimum time between operations on the hardware

   .. rubric:: Example

   A conditional reset can be implemented as follows:

   .. jupyter-execute::

       # relevant imports
       from qblox_scheduler import Schedule
       from qblox_scheduler.operations import ConditionalOperation, Measure, X

       # define conditional reset as a Schedule
       conditional_reset = Schedule("conditional reset")
       conditional_reset.add(Measure("q0", feedback_trigger_label="q0"))
       conditional_reset.add(
           ConditionalOperation(body=X("q0"), qubit_name="q0"),
           rel_time=364e-9,
       )

   .. versionadded:: 0.22.0

       For some hardware specific implementations, a ``hardware_buffer_time``
       might be required to ensure the correct timing of the operations. This will
       be added to the duration of the ``body`` to prevent overlap with other
       operations.



   .. py:property:: body
      :type: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule


      Body of a control flow.


   .. py:property:: duration
      :type: float


      Duration of a control flow.


.. py:class:: ControlFlowOperation(name: str)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Control flow operation that can be used as an ``Operation`` in ``.TimeableSchedule``.

   This is an abstract class. Each concrete implementation
   of the control flow operation decides how and when
   their ``body`` operation is executed.


   .. py:property:: body
      :type: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule

      :abstractmethod:


      Body of a control flow.


   .. py:method:: get_used_port_clocks() -> set[tuple[str, str]]

      Extracts which port-clock combinations are used in this control flow operation.

      :returns: :
                    All (port, clock) combinations that operations
                    in the body of this control flow operation uses.




.. py:class:: ControlFlowSpec

   Control flow specification to be used at ``Schedule.add``.

   The users can specify any concrete control flow with
   the ``control_flow`` argument to ``Schedule.add``.
   The ``ControlFlowSpec`` is only a type which by itself
   cannot be used for the ``control_flow`` argument,
   use any concrete control flow derived from it.


   .. py:method:: create_operation(body: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule) -> qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule
      :abstractmethod:


      Transform the control flow specification to an operation or schedule.



.. py:class:: LoopOperation(body: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.schedule.Schedule, *, repetitions: int | None = None, domain: dict[qblox_scheduler.operations.variables.Variable, qblox_scheduler.operations.loop_domains.LinearDomain] | None = None, t0: float = 0.0, strategy: LoopStrategy | None = None)

   Bases: :py:obj:`ControlFlowOperation`


   Loop over another operation predefined times.

   Repeats the operation defined in ``body`` ``repetitions`` times.
   The actual implementation depends on the backend.

   One of ``domain`` or ``repetitions`` must be specified.

   :param body: Operation to be repeated
   :param repetitions: Number of repetitions, by default None
   :param domain: Linear domain to loop over, by default None
   :param t0: Time offset, by default 0
   :param strategy: Strategy to use for implementing this loop, by default None to make own decision


   .. py:property:: body
      :type: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule


      Body of a control flow.


   .. py:property:: duration
      :type: float


      Duration of a control flow.


   .. py:property:: domain
      :type: dict[qblox_scheduler.operations.variables.Variable, qblox_scheduler.operations.loop_domains.LinearDomain]


      Linear domain to loop over.


   .. py:property:: repetitions
      :type: int


      Number of times the body will execute.


   .. py:property:: strategy
      :type: LoopStrategy | None


      What strategy to use for implementing this loop.


.. py:class:: LoopStrategy

   Bases: :py:obj:`qblox_scheduler.enums.StrEnum`


   Strategy to use for implementing loops.

   REALTIME: Use native loops.
   UNROLLED: Unroll loop at compilation time into separate instructions.


   .. py:attribute:: REALTIME
      :value: 'realtime'



   .. py:attribute:: UNROLLED
      :value: 'unrolled'



.. py:class:: DType

   Bases: :py:obj:`qblox_scheduler.enums.StrEnum`


   Data type of a variable or expression.


   .. py:attribute:: NUMBER
      :value: 'number'


      A number, corresponding to 1, 2, 3, etc.


   .. py:attribute:: AMPLITUDE
      :value: 'amplitude'


      An amplitude, corresponding to 0.1, 0.2, 0.3, etc. in dimensionless units
      ranging from -1 to 1.


   .. py:attribute:: TIME
      :value: 'time'


      A time, corresponding to 20e-9, 40e-9, 60e-9, etc. in seconds.


   .. py:attribute:: FREQUENCY
      :value: 'frequency'


      A frequency, corresponding to 1e9, 2e9, 3e9, etc. in Hz.


   .. py:attribute:: PHASE
      :value: 'phase'


      A phase, corresponding to e.g. 0, 30, 60, 90, etc. in degrees ranging from 0 to 360.


   .. py:method:: is_timing_sensitive() -> bool

      Whether an expression of this type affects timing.



.. py:class:: CNOT(qC: str, qT: str, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Conditional-NOT gate, a common entangling gate.

   Performs an X gate on the target qubit qT conditional on the state
   of the control qubit qC.

   This operation can be represented by the following unitary:

   .. math::

       \mathrm{CNOT}  = \begin{bmatrix}
           1 & 0 & 0 & 0 \\
           0 & 1 & 0 & 0 \\
           0 & 0 & 0 & 1 \\
           0 & 0 & 1 & 0 \\ \end{bmatrix}

   :param qC: The control device element.
   :param qT: The target device element
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: CZ(qC: str, qT: str, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Conditional-phase gate, a common entangling gate.

   Performs a Z gate on the target device element qT conditional on the state
   of the control device element qC.

   This operation can be represented by the following unitary:

   .. math::

       \mathrm{CZ}  = \begin{bmatrix}
           1 & 0 & 0 & 0 \\
           0 & 1 & 0 & 0 \\
           0 & 0 & 1 & 0 \\
           0 & 0 & 0 & -1 \\ \end{bmatrix}

   :param qC: The control device element.
   :param qT: The target device element
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: X90(qubit: str, **device_overrides)

   Bases: :py:obj:`Rxy`


   A single qubit rotation of 90 degrees around the X-axis.

   It is identical to the Rxy gate with theta=90 and phi=0

   Defined by the unitary:

   .. math::
       X90 = R_{X90} = \frac{1}{\sqrt{2}}\begin{bmatrix}
               1 & -i \\
               -i & 1 \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: Y90(qubit: str, **device_overrides)

   Bases: :py:obj:`Rxy`


   A single qubit rotation of 90 degrees around the Y-axis.

   It is identical to the Rxy gate with theta=90 and phi=90

   Defined by the unitary:

   .. math::

       Y90 = R_{Y90} = \frac{1}{\sqrt{2}}\begin{bmatrix}
               1 & -1 \\
               1 & 1 \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: Z90(qubit: str, **device_overrides)

   Bases: :py:obj:`Rz`


   A single qubit rotation of 90 degrees around the Z-axis.

   This operation can be represented by the following unitary:

   .. math::

       Z90 =
       R_{Z90} =
       e^{-\frac{\pi/2}{2}}S =
       e^{-\frac{\pi/2}{2}}\sqrt{Z} = \frac{1}{\sqrt{2}}\begin{bmatrix}
            1-i & 0 \\
            0 & 1+i \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: H(*qubits: str, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   A single qubit Hadamard gate.

   Note that the gate uses :math:`R_z(\pi) = -iZ`, adding a global phase of :math:`-\pi/2`.
   This operation can be represented by the following unitary:

   .. math::

       H = Y90 \cdot Z = \frac{-i}{\sqrt{2}}\begin{bmatrix}
            1 & 1 \\
            1 & -1 \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: Measure(*qubits: str, acq_channel: collections.abc.Hashable | None = None, coords: dict | None = None, acq_index: tuple[int, Ellipsis] | tuple[None, Ellipsis] | int | None = None, acq_protocol: Literal['SSBIntegrationComplex', 'Timetag', 'TimetagTrace', 'Trace', 'TriggerCount', 'ThresholdedTriggerCount', 'NumericalSeparatedWeightedIntegration', 'NumericalWeightedIntegration', 'ThresholdedAcquisition'] | None = None, bin_mode: qblox_scheduler.enums.BinMode | str | None = None, feedback_trigger_label: str | None = None, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   A projective measurement in the Z-basis.

   The measurement is compiled according to the type of acquisition specified
   in the device configuration.

   .. note::

       Strictly speaking this is not a gate as it can not
       be described by a unitary.

   :param qubits: The device elements you want to measure.
   :param acq_channel: Only for special use cases.
                       By default (if None): the acquisition channel specified in the device element is used.
                       If set, this acquisition channel is used for this measurement.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Index of the register where the measurement is stored.  If None specified,
                     this defaults to writing the result of all device elements to acq_index 0. By default
                     None.
   :param acq_protocol: Acquisition protocols that are supported. If ``None`` is specified, the
                        default protocol is chosen based on the device and backend configuration. By
                        default None.
   :type acq_protocol: "SSBIntegrationComplex" | "Trace" | "TriggerCount" |             "NumericalSeparatedWeightedIntegration" |             "NumericalWeightedIntegration" | None, Optional
   :param bin_mode: The binning mode that is to be used. If not None, it will overwrite the
                    binning mode used for Measurements in the circuit-to-device compilation
                    step. By default None.
   :param feedback_trigger_label: The label corresponding to the feedback trigger, which is mapped by the
                                  compiler to a feedback trigger address on hardware, by default None.
   :type feedback_trigger_label: str
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: Reset(*qubits: str, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Reset a qubit to the :math:`|0\rangle` state.

   The Reset gate is an idle operation that is used to initialize one or more qubits.

   .. note::

       Strictly speaking this is not a gate as it can not
       be described by a unitary.

   .. admonition:: Examples
       :class: tip

       The operation can be used in several ways:

       .. jupyter-execute::

           from qblox_scheduler.operations.gate_library import Reset

           reset_1 = Reset("q0")
           reset_2 = Reset("q1", "q2")
           reset_3 = Reset(*[f"q{i}" for i in range(3, 6)])

   :param qubits: The device element(s) to reset. NB one or more device element can be specified, e.g.,
                  :code:`Reset("q0")`, :code:`Reset("q0", "q1", "q2")`, etc..
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: Rxy(theta: float, phi: float, qubit: str, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   A single qubit rotation around an axis in the equator of the Bloch sphere.

   This operation can be represented by the following unitary as defined in
   https://doi.org/10.1109/TQE.2020.2965810:

   .. math::

       \mathsf {R}_{xy} \left(\theta, \varphi\right) = \begin{bmatrix}
       \textrm {cos}(\theta /2) & -ie^{-i\varphi }\textrm {sin}(\theta /2)
       \\ -ie^{i\varphi }\textrm {sin}(\theta /2) & \textrm {cos}(\theta /2)
       \end{bmatrix}


   :param theta: Rotation angle in degrees, will be casted to the [-180, 180) domain.
   :param phi: Phase of the rotation axis, will be casted to the [0, 360) domain.
   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: Rz(theta: float, qubit: str, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   A single qubit rotation about the Z-axis of the Bloch sphere.

   This operation can be represented by the following unitary as defined in
   https://www.quantum-inspire.com/kbase/rz-gate/:

   .. math::

       \mathsf {R}_{z} \left(\theta\right) = \begin{bmatrix}
       e^{-i\theta/2} & 0
       \\ 0 & e^{i\theta/2} \end{bmatrix}

   :param theta: Rotation angle in degrees, will be cast to the [-180, 180) domain.
   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: S(qubit: str, **device_overrides)

   Bases: :py:obj:`Z90`


   A single qubit rotation of 90 degrees around the Z-axis.

   This implements an :math:`S` gate up to a global phase.
   Therefore, this operation is a direct alias of the `Z90` operations

   This operation can be represented by the following unitary:

   .. math::

       R_{Z90} =
       e^{-i\frac{\pi}{4}}S =
       e^{-i\frac{\pi}{4}}\sqrt{Z} = \frac{1}{\sqrt{2}}\begin{bmatrix}
            1-i & 0 \\
            0 & 1+i \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: SDagger(qubit: str, **device_overrides)

   Bases: :py:obj:`Rz`


   A single qubit rotation of -90 degrees around the Z-axis.

   Implements :math:`S^\dagger` up to a global phase.

   This operation can be represented by the following unitary:

   .. math::

       R_{Z270} =
       e^{\frac{\pi}{4}}S^\dagger =
       e^{\frac{\pi}{4}}\sqrt{Z}^\dagger = \frac{1}{\sqrt{2}}\begin{bmatrix}
            1+i & 0 \\
            0 & 1-i \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: T(qubit: str, **device_overrides)

   Bases: :py:obj:`Rz`


   A single qubit rotation of 45 degrees around the Z-axis.

   Implements :math:`T` up to a global phase.

   This operation can be represented by the following unitary:

   .. math::

       R_{Z45} =
       e^{-\frac{\pi}{8}}T =
       e^{-\frac{\pi}{8}}\begin{bmatrix}
            1 & 0 \\
            0 & \frac{1+i}{\sqrt{2}} \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: TDagger(qubit: str, **device_overrides)

   Bases: :py:obj:`Rz`


   A single qubit rotation of -45 degrees around the Z-axis.

   Implements :math:`T^\dagger` up to a global phase.

   This operation can be represented by the following unitary:

   .. math::

       R_{Z315} =
       e^{\frac{\pi}{8}}T^\dagger =
       e^{\frac{\pi}{8}}\begin{bmatrix}
            1 & 0 \\
            0 & \frac{1-i}{\sqrt{2}} \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: X(qubit: str, **device_overrides)

   Bases: :py:obj:`Rxy`


   A single qubit rotation of 180 degrees around the X-axis.

   This operation can be represented by the following unitary:

   .. math::

       X180 = R_{X180} = \begin{bmatrix}
            0 & -i \\
            -i & 0 \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: Y(qubit: str, **device_overrides)

   Bases: :py:obj:`Rxy`


   A single qubit rotation of 180 degrees around the Y-axis.

   It is identical to the Rxy gate with theta=180 and phi=90

   Defined by the unitary:

   .. math::
       Y180 = R_{Y180} = \begin{bmatrix}
            0 & -1 \\
            1 & 0 \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: Z(qubit: str, **device_overrides)

   Bases: :py:obj:`Rz`


   A single qubit rotation of 180 degrees around the Z-axis.

   Note that the gate implements :math:`R_z(\pi) = -iZ`, adding a global phase of :math:`-\pi/2`.
   This operation can be represented by the following unitary:

   .. math::

       Z180 = R_{Z180} = -iZ = e^{-\frac{\pi}{2}}Z = \begin{bmatrix}
            -i & 0 \\
            0 & i \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


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


.. py:function:: arange(stop: float, dtype: qblox_scheduler.operations.expressions.DType) -> LinearDomain
                 arange(start: float, stop: float, dtype: qblox_scheduler.operations.expressions.DType) -> LinearDomain
                 arange(start: float, stop: float, step: float, dtype: qblox_scheduler.operations.expressions.DType) -> LinearDomain

   Linear range of values to loop over, specified with a start value, an exclusive stop value and a
   step size.

   :param start: Start of interval. The interval includes this value.
   :param stop: End of interval. The interval does not include this value, except in some cases where step
                is not an integer and floating point round-off affects the length of out.
   :param step: Spacing between values. For any output out, this is the distance between two adjacent
                values, out[i+1] - out[i].
   :param dtype: Data type of the linear domain.


.. py:function:: linspace(start: complex | float, stop: complex | float, num: int, dtype: qblox_scheduler.operations.expressions.DType) -> LinearDomain

   Linear range of values to loop over, specified with a start value, an inclusive stop value and
   the number of linearly spaced points to generate.

   :param start: The starting value of the sequence.
   :param stop: The end value of the sequence.
   :param num: Number of samples to generate. Must be non-negative.
   :param dtype: Data type of the linear domain.


.. py:class:: ChargeReset(*qubits: str)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Prepare a NV to its negative charge state NV$^-$.

   Create a new instance of ChargeReset operation that is used to initialize the
   charge state of an NV center.

   :param qubit: The qubit to charge-reset. NB one or more qubits can be specified, e.g.,
                 :code:`ChargeReset("qe0")`, :code:`ChargeReset("qe0", "qe1", "qe2")`, etc..


.. py:class:: CRCount(*qubits: str, acq_channel: collections.abc.Hashable | None = None, coords: dict | None = None, acq_index: tuple[int, Ellipsis] | tuple[None, Ellipsis] | int | None = None, acq_protocol: Literal['Trace', 'TriggerCount', None] = None, bin_mode: qblox_scheduler.enums.BinMode | None = None)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Operate ionization and spin pump lasers for charge and resonance counting.

   Gate level description for an optical CR count measurement.

   The measurement is compiled according to the type of acquisition specified
   in the device configuration.

   :param qubits: The qubits you want to measure
   :param acq_channel: Only for special use cases.
                       By default (if None): the acquisition channel specified in the device element is used.
                       If set, this acquisition channel is used for this measurement.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Index of the register where the measurement is stored.
                     If None specified, it will default to a list of zeros of len(qubits)
   :param acq_protocol: Acquisition protocol (currently ``"TriggerCount"`` and ``"Trace"``)
                        are supported. If ``None`` is specified, the default protocol is chosen
                        based on the device and backend configuration.
   :param bin_mode: The binning mode that is to be used. If not None, it will overwrite
                    the binning mode used for Measurements in the quantum-circuit to
                    quantum-device compilation step.


.. py:class:: Operation(name: str)

   Bases: :py:obj:`qblox_scheduler.json_utils.JSONSchemaValMixin`, :py:obj:`collections.UserDict`


   A representation of quantum circuit operations.

   The :class:`~Operation` class is a JSON-compatible data structure that contains information
   on how to represent the operation on the quantum-circuit and/or the quantum-device
   layer. It also contains information on where the operation should be applied: the
   :class:`~qblox_scheduler.resources.Resource` s used.

   An operation always has the following attributes:

   - duration (float): duration of the operation in seconds (can be 0).
   - hash (str): an auto generated unique identifier.
   - name (str): a readable identifier, does not have to be unique.



   An Operation can contain information  on several levels of abstraction.
   This information is used when different representations are required. Note that when
   initializing an operation  not all of this information needs to be available
   as operations are typically modified during the compilation steps.

   .. tip::

       :mod:`qblox_scheduler` comes with a
       :mod:`~qblox_scheduler.operations.gate_library` and a
       :mod:`~qblox_scheduler.operations.pulse_library` , both containing common
       operations.


   **JSON schema of a valid Operation**

   .. jsonschema:: https://gitlab.com/qblox/packages/software/qblox-scheduler/-/raw/main/src/qblox_scheduler/schemas/operation.json


   .. note::

       Two different Operations containing the same information generate the
       same hash and are considered identical.


   .. py:attribute:: schema_filename
      :value: 'operation.json'



   .. py:attribute:: _class_signature
      :value: None



   .. py:attribute:: _duration
      :type:  float
      :value: 0



   .. py:method:: clone() -> Operation

      Clone this operation into a new independent operation.



   .. py:method:: substitute(substitutions: dict[qblox_scheduler.operations.expressions.Expression, qblox_scheduler.operations.expressions.Expression | int | float | complex]) -> Operation

      Substitute matching expressions in operand, possibly evaluating a result.



   .. py:property:: name
      :type: str


      Return the name of the operation.


   .. py:property:: duration
      :type: float


      Determine operation duration from pulse_info.

      If the operation contains no pulse info, it is assumed to be ideal and
      have zero duration.


   .. py:property:: hash
      :type: str


      A hash based on the contents of the Operation.

      Needs to be a str for easy compatibility with json.


   .. py:method:: _get_signature(parameters: dict) -> str
      :classmethod:


      Returns the constructor call signature of this instance for serialization.

      The string constructor representation can be used to recreate the object
      using eval(signature).

      :param parameters: The current data dictionary.
      :type parameters: dict

      :returns: :




   .. py:method:: add_gate_info(gate_operation: Operation) -> None

      Updates self.data['gate_info'] with contents of gate_operation.

      :param gate_operation: an operation containing gate_info.



   .. py:method:: add_device_representation(device_operation: Operation) -> None

      Adds device-level representation details to the current operation.

      :param device_operation: an operation containing the pulse_info and/or acquisition info describing
                               how to represent the current operation at the quantum-device layer.



   .. py:method:: get_used_port_clocks() -> set[tuple[str, str]]

      Extracts which port-clock combinations are used in this operation.

      :returns: :
                    All (port, clock) combinations this operation uses.




   .. py:method:: is_valid(object_to_be_validated: Operation) -> bool
      :classmethod:


      Validates the object's contents against the schema.

      Additionally, checks if the hash property of the object evaluates correctly.



   .. py:property:: valid_gate
      :type: bool


      An operation is a valid gate if it has gate-level representation details.


   .. py:property:: valid_pulse
      :type: bool


      An operation is a valid pulse if it has pulse-level representation details.


   .. py:property:: valid_acquisition
      :type: bool


      An operation is a valid acquisition
      if it has pulse-level acquisition representation details.


   .. py:property:: is_conditional_acquisition
      :type: bool


      An operation is conditional if one of the following holds, ``self`` is an
      an acquisition with a ``feedback_trigger_label`` assigned to it.


   .. py:property:: is_control_flow
      :type: bool


      Determine if operation is a control flow operation.

      :returns: bool
                    Whether the operation is a control flow operation.


   .. py:property:: has_voltage_offset
      :type: bool


      Checks if the operation contains information for a voltage offset.


.. py:class:: PulseCompensation(body: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.schedule.Schedule, qubits: str | collections.abc.Iterable[str] | None = None, max_compensation_amp: dict[Port, float] | None = None, time_grid: float | None = None, sampling_rate: float | None = None)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Apply pulse compensation to an operation or schedule.

   Inserts a pulse at the end of the operation or schedule set in ``body`` for each port.
   The compensation pulses are calculated so that the integral of all pulses
   (including the compensation pulses) are zero for each port.
   Moreover, the compensating pulses are square pulses, and start just after the last
   pulse on each port individually, and their maximum amplitude is the one
   specified in the ``max_compensation_amp``. Their duration is divisible by ``duration_grid``.
   The clock is assumed to be the baseband clock; any other clock is not allowed.

   :param body: Operation to be pulse-compensated
   :param qubits: For circuit-level operations, this is a list of device element names.
   :param max_compensation_amp: Dictionary for each port the maximum allowed amplitude for the compensation pulse.
   :param time_grid: Grid time of the duration of the compensation pulse.
   :param sampling_rate: Sampling rate for pulse integration calculation.


   .. py:property:: body
      :type: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule


      Body of a pulse compensation.


   .. py:property:: max_compensation_amp
      :type: dict[Port, float]


      For each port the maximum allowed amplitude for the compensation pulse.


   .. py:property:: time_grid
      :type: float


      Grid time of the duration of the compensation pulse.


   .. py:property:: sampling_rate
      :type: float


      Sampling rate for pulse integration calculation.


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



.. py:function:: non_implemented_pulse(**kwargs) -> qblox_scheduler.schedules.TimeableSchedule

   Raise an error indicating that the requested gate or pulse is not implemented.


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



.. py:function:: phase_shift(theta: float, clock: str) -> qblox_scheduler.operations.pulse_library.ShiftClockPhase

   Generate a :class:`~.operations.pulse_library.ShiftClockPhase` that shifts the phase of the
   ``clock`` by an angle `theta`.

   :param theta: Angle to shift the clock by, in degrees.
   :param clock: Name of the clock to shift.

   :returns: :
                 ShiftClockPhase operation.



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



.. py:function:: spin_init_pulse(square_duration: float, ramp_diff: float, parent_port: str, parent_clock: str, parent_square_amp: float, parent_ramp_amp: float, parent_ramp_rate: float, child_port: str, child_clock: str, child_square_amp: float, child_ramp_amp: float, child_ramp_rate: float) -> qblox_scheduler.schedules.TimeableSchedule

   Device compilation of the spin init operation.


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


.. py:class:: IdlePulse(duration: float | qblox_scheduler.operations.expressions.Expression)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   The IdlePulse Operation is a placeholder for a specified duration of time.

   :param duration: The duration of idle time in seconds.


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


.. py:class:: WindowOperation(window_name: str, duration: float | qblox_scheduler.operations.expressions.Expression, t0: float | qblox_scheduler.operations.expressions.Expression = 0.0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   The WindowOperation is an operation for visualization purposes.

   The :class:`~WindowOperation` has a starting time and duration.


   .. py:property:: window_name
      :type: str


      Return the window name of this operation.


