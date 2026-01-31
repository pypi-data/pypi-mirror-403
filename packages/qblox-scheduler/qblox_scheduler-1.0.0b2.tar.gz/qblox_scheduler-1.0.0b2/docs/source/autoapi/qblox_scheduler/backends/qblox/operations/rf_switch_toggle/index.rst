rf_switch_toggle
================

.. py:module:: qblox_scheduler.backends.qblox.operations.rf_switch_toggle 

.. autoapi-nested-parse::

   Module that contains the RFSwitchToggle operation.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.operations.rf_switch_toggle.RFSwitchToggle




.. py:class:: RFSwitchToggle(duration: float, port: str, clock: str)

   Bases: :py:obj:`qblox_scheduler.operations.hardware_operations.pulse_library.RFSwitchToggle`


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


