acquisition_library
===================

.. py:module:: qblox_scheduler.operations.acquisition_library 

.. autoapi-nested-parse::

   Standard acquisition protocols for use with the qblox_scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.acquisition_library.Acquisition
   qblox_scheduler.operations.acquisition_library.Trace
   qblox_scheduler.operations.acquisition_library.WeightedIntegratedSeparated
   qblox_scheduler.operations.acquisition_library.SSBIntegrationComplex
   qblox_scheduler.operations.acquisition_library.ThresholdedAcquisition
   qblox_scheduler.operations.acquisition_library.NumericalSeparatedWeightedIntegration
   qblox_scheduler.operations.acquisition_library.NumericalWeightedIntegration
   qblox_scheduler.operations.acquisition_library.WeightedThresholdedAcquisition
   qblox_scheduler.operations.acquisition_library.TriggerCount
   qblox_scheduler.operations.acquisition_library.TimetagTrace
   qblox_scheduler.operations.acquisition_library.Timetag
   qblox_scheduler.operations.acquisition_library.ThresholdedTriggerCount
   qblox_scheduler.operations.acquisition_library.DualThresholdedTriggerCount



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.acquisition_library._warn_deprecated_acq_index



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


.. py:function:: _warn_deprecated_acq_index(acq_index: int | None) -> None

