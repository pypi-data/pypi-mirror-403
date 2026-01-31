pulse_library
=============

.. py:module:: qblox_scheduler.operations.hardware_operations.pulse_library 

.. autoapi-nested-parse::

   Standard pulse-level operations for use with the qblox_scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.hardware_operations.pulse_library.LatchReset
   qblox_scheduler.operations.hardware_operations.pulse_library.SimpleNumericalPulse
   qblox_scheduler.operations.hardware_operations.pulse_library.RFSwitchToggle




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


.. py:class:: RFSwitchToggle(duration: float, port: str, clock: str)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Turn the RF complex output on for the given duration.
   The RF ports are on by default, make sure to set
   :attr:`~.qblox_scheduler.backends.types.qblox.RFDescription.rf_output_on`
   to `False` to turn them off.

   :param duration: Duration to turn the RF output on.
   :param port: Name of the associated port.
   :param clock: Name of the associated clock.
                 For now the given port-clock combination must
                 have a LO frequency defined in the hardware configuration.

   .. rubric:: Examples

   Partial hardware configuration to turn the RF complex output off by default
   to be able to use this operation.

   .. code-block:: python

       hardware_compilation_config = {
           "config_type": QbloxHardwareCompilationConfig,
           "hardware_description": {
               "cluster0": {
                   "instrument_type": "Cluster",
                   "modules": {
                       "0": {"instrument_type": "QCM_RF", "rf_output_on": False},
                       "1": {"instrument_type": "QRM_RF", "rf_output_on": False},
                   },
               },
           },
       }


