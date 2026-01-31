corrections
===========

.. py:module:: qblox_scheduler.backends.corrections 

.. autoapi-nested-parse::

   Pulse and acquisition corrections for hardware compilation.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.corrections.determine_relative_latency_corrections
   qblox_scheduler.backends.corrections.distortion_correct_pulse
   qblox_scheduler.backends.corrections._is_distortion_correctable
   qblox_scheduler.backends.corrections.apply_software_distortion_corrections



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.corrections.logger


.. py:data:: logger

.. py:function:: determine_relative_latency_corrections(hardware_cfg: qblox_scheduler.backends.types.common.HardwareCompilationConfig, schedule: qblox_scheduler.schedules.schedule.TimeableSchedule | None = None) -> dict[str, float]

   Generates the latency configuration dict for all port-clock combinations that are present
   in the schedule.
   This is done by first setting unspecified latency corrections to zero, and then
   subtracting the minimum latency from all latency corrections.


.. py:function:: distortion_correct_pulse(pulse_data: dict[str, Any], distortion_correction: qblox_scheduler.backends.types.common.SoftwareDistortionCorrection) -> qblox_scheduler.operations.pulse_library.NumericalPulse

   Sample pulse and apply filter function to the sample to distortion correct it.

   :param pulse_data: Definition of the pulse.
   :param distortion_correction: The distortion_correction configuration for this pulse.

   :returns: :
                 The sampled, distortion corrected pulse wrapped in a ``NumericalPulse``.



.. py:function:: _is_distortion_correctable(operation: qblox_scheduler.operations.operation.Operation) -> bool

   Checks whether distortion corrections can be applied to the given operation.


.. py:function:: apply_software_distortion_corrections(operation: qblox_scheduler.operations.operation.Operation, distortion_corrections: dict) -> qblox_scheduler.operations.operation.Operation | None
                 apply_software_distortion_corrections(operation: qblox_scheduler.schedules.schedule.TimeableSchedule, distortion_corrections: dict) -> None

   Apply distortion corrections to operations in the schedule.

   Defined via the hardware configuration file, example:

   .. code-block::

       "distortion_corrections": {
           "q0:fl-cl0.baseband": {
               "filter_func": "scipy.signal.lfilter",
               "input_var_name": "x",
               "kwargs": {
                   "b": [0.0, 0.5, 1.0],
                   "a": [1]
               },
               "clipping_values": [-2.5, 2.5]
           }
       }

   Clipping values are the boundaries to which the corrected pulses will be clipped,
   upon exceeding, these are optional to supply.

   For pulses in need of correcting (indicated by their port-clock combination) we are
   **only** replacing the dict in ``"pulse_info"`` associated to that specific
   pulse. This means that we can have a combination of corrected (i.e., pre-sampled)
   and uncorrected pulses in the same operation.

   Note that we are **not** updating the ``"operation_id"`` key, used to reference
   the operation from schedulables.

   :param operation: The operation that contains operations that are to be distortion corrected.
                     Note, this function updates the operation.
   :param distortion_corrections: The distortion_corrections configuration of the setup.

   :returns: :
                 The new operation with distortion corrected operations, if it needs to be replaced.
                 If it doesn't need to be replaced in the schedule or control flow, it returns ``None``.

   :Warns: **RuntimeWarning** -- If distortion correction can not be applied to the type of Operation in the
           schedule.

   :raises KeyError: when elements are missing in distortion correction config for a port-clock
       combination.
   :raises KeyError: when clipping values are supplied but not two values exactly, min and max.


