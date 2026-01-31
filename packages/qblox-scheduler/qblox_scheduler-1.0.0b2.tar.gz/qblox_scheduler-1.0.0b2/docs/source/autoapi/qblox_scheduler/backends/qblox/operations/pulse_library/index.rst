pulse_library
=============

.. py:module:: qblox_scheduler.backends.qblox.operations.pulse_library 

.. autoapi-nested-parse::

   Standard pulse-level operations for use with the qblox_scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.operations.pulse_library.LatchReset
   qblox_scheduler.backends.qblox.operations.pulse_library.SimpleNumericalPulse




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


