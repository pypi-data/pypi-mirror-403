mock_setup
==========

.. py:module:: qblox_scheduler.device_under_test.mock_setup 

.. autoapi-nested-parse::

   Code to set up a mock setup for use in tutorials and testing.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.device_under_test.mock_setup.set_up_mock_transmon_setup
   qblox_scheduler.device_under_test.mock_setup.set_standard_params_transmon
   qblox_scheduler.device_under_test.mock_setup.set_up_mock_basic_nv_setup
   qblox_scheduler.device_under_test.mock_setup.set_standard_params_basic_nv



.. py:function:: set_up_mock_transmon_setup() -> dict

   Set up a system containing 5 transmon device elements connected in a star shape.

   .. code-block::

       q0    q1
         \  /
          q2
         /  \
       q3    q4

   Returns a dictionary containing the instruments that are instantiated as part of
   this setup. The keys corresponds to the names of the instruments.


.. py:function:: set_standard_params_transmon(mock_setup: dict) -> None

   Set somewhat standard parameters to the mock setup generated above.

   These parameters serve so that the quantum-device is capable of generating
   a configuration that can be used for compiling schedules.

   In normal use, unknown parameters are set as 'nan' values, forcing the user to
   set these. However for testing purposes it can be useful to set some semi-random
   values. The values here are chosen to reflect typical values as used in practical
   experiments.


.. py:function:: set_up_mock_basic_nv_setup() -> dict

   Set up a system containing 2 electronic device elements in an NV center.

   After usage, close all instruments.

   :returns: All instruments created. Containing a "quantum_device", electronic qubit "qe0",
             "meas_ctrl" and "instrument_coordinator".



.. py:function:: set_standard_params_basic_nv(mock_nv_device: dict[str, Any]) -> None

   Set somewhat standard parameters to the mock setup generated above.

   These parameters serve so that the quantum-device is capable of generating
   a configuration that can be used for compiling schedules.

   In normal use, unknown parameters are set as 'nan' values, forcing the user to
   set these. However for testing purposes it can be useful to set some semi-random
   values. The values here are chosen to reflect typical values as used in practical
   experiments. All amplitudes for pulses are set to 1e-3.


