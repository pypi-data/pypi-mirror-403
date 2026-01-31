operations
==========

.. py:module:: qblox_scheduler.qblox.operations 

.. autoapi-nested-parse::

   Module containing qblox specific operations.



Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.qblox.operations.ConditionalOperation
   qblox_scheduler.qblox.operations.ConditionalReset
   qblox_scheduler.qblox.operations.LatchReset
   qblox_scheduler.qblox.operations.SimpleNumericalPulse




.. py:class:: ConditionalOperation(body: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.schedule.Schedule, qubit_name: str, t0: float = 0.0, hardware_buffer_time: float = constants.MIN_TIME_BETWEEN_OPERATIONS * 1e-09)

   Bases: :py:obj:`qblox_scheduler.operations.control_flow_library.ConditionalOperation`


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



.. py:class:: ConditionalReset(qubit_name: str, name: str = 'conditional_reset', **kwargs)

   Bases: :py:obj:`qblox_scheduler.operations.conditional_reset.ConditionalReset`


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


.. py:class:: LatchReset(portclock: tuple[str, str], t0: float = 0, duration: float = 4e-09)

   Bases: :py:obj:`qblox_scheduler.operations.hardware_operations.pulse_library.LatchReset`


   Operation that resets the feedback trigger addresses from the hardware.

   Currently only implemented for Qblox backend, refer to
   :class:`~qblox_scheduler.backends.qblox.operation_handling.virtual.ResetFeedbackTriggersStrategy`
   for more details.


.. py:class:: SimpleNumericalPulse(samples: numpy.ndarray | list, port: str, clock: str = BasebandClockResource.IDENTITY, gain: complex | float | operations.expressions.Expression | collections.abc.Sequence[complex | float | operations.expressions.Expression] = 1, reference_magnitude: qblox_scheduler.operations.pulse_library.ReferenceMagnitude | None = None, t0: float = 0)

   Bases: :py:obj:`qblox_scheduler.operations.hardware_operations.pulse_library.SimpleNumericalPulse`


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


