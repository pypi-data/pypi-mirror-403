pulse_factories
===============

.. py:module:: qblox_scheduler.backends.qblox.operations.pulse_factories 

.. autoapi-nested-parse::

   Module containing factory functions for pulses on the quantum-device layer.

   These factories take a parametrized representation of an operation and create an
   instance of the operation itself. The created operations make use of Qblox-specific
   hardware features.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.operations.pulse_factories.long_square_pulse
   qblox_scheduler.backends.qblox.operations.pulse_factories.long_ramp_pulse
   qblox_scheduler.backends.qblox.operations.pulse_factories.staircase_pulse



.. py:function:: long_square_pulse(*args, **kwargs)

.. py:function:: long_ramp_pulse(*args, **kwargs)

.. py:function:: staircase_pulse(*args, **kwargs)

