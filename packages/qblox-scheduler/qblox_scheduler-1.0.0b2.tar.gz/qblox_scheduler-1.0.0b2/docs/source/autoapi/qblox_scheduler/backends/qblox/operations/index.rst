operations
==========

.. py:module:: qblox_scheduler.backends.qblox.operations 


Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   control_flow_library/index.rst
   gate_library/index.rst
   inline_q1asm/index.rst
   pulse_factories/index.rst
   pulse_library/index.rst
   rf_switch_toggle/index.rst


Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.operations.ConditionalOperation



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.operations.long_ramp_pulse
   qblox_scheduler.backends.qblox.operations.long_square_pulse
   qblox_scheduler.backends.qblox.operations.staircase_pulse



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



.. py:function:: long_ramp_pulse(*args, **kwargs)

.. py:function:: long_square_pulse(*args, **kwargs)

.. py:function:: staircase_pulse(*args, **kwargs)

