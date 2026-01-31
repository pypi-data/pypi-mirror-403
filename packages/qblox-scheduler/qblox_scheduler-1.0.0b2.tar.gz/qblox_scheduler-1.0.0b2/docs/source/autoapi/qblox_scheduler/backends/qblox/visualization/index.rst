visualization
=============

.. py:module:: qblox_scheduler.backends.qblox.visualization 

.. autoapi-nested-parse::

   Qblox Visualization Module.

   This module, part of the Qblox backend system, is dedicated to creating and
   managing visual and User Interface (UI) elements essential for representing
   compiled instructions and other relevant data.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.visualization._display_dict
   qblox_scheduler.backends.qblox.visualization._display_compiled_instructions



.. py:function:: _display_dict(settings: dict[str, Any]) -> None

.. py:function:: _display_compiled_instructions(data: dict[Any, Any], parent_tab_name: str | None = None) -> ipywidgets.Tab | None

   Display compiled instructions in a tabulated format.

   This function creates an interactive table, rendering and displaying
   compiled instructions along with other relevant data, allowing for a
   structured and user-friendly representation.

   In addition, it provides formatting specific for Qblox-specific sequencer
   programs, waveforms, and settings.

   .. admonition:: Note

       This function is tailored for :attr:`~.CompiledSchedule.compiled_instructions`
       but works with any nested dictionary.

   .. admonition:: Example

       .. jupyter-execute::
           :hide-code:

           from qblox_scheduler.backends import SerialCompiler
           from qblox_scheduler.device_under_test.quantum_device import QuantumDevice
           from qblox_scheduler.device_under_test.transmon_element import BasicTransmonElement
           from qblox_scheduler.operations.gate_library import (
               Measure,
               Reset,
               X,
               Y,
           )
           from qblox_scheduler.schedules.schedule import TimeableSchedule
           from qblox_scheduler.schemas.examples import utils

           compiler = SerialCompiler("compiler")

           q0 = BasicTransmonElement("q0")
           q4 = BasicTransmonElement("q4")

           for qubit in [q0, q4]:
               qubit.rxy.amp180 = 0.115
               qubit.rxy.beta = 2.5e-10
               qubit.clock_freqs.f01 = 7.3e9
               qubit.clock_freqs.f12 = 7.0e9
               qubit.clock_freqs.readout = 8.0e9
               qubit.measure.acq_delay = 100e-9

           quantum_device = QuantumDevice(name="quantum_device")
           quantum_device.add_element(q0)
           quantum_device.add_element(q4)

           device_config = quantum_device.generate_device_config()
           hardware_config = utils.load_json_example_scheme(
               "qblox_hardware_config_transmon.json"
           )
           quantum_device.hardware_config = hardware_config

           compilation_config = quantum_device.generate_compilation_config()
           compiler = SerialCompiler("compiler")
           compiler.quantum_device = quantum_device

       .. jupyter-execute::

           schedule = TimeableSchedule("demo compiled instructions")
           schedule.add(Reset("q0", "q4"))
           schedule.add(X("q0"))
           schedule.add(Y("q4"))
           schedule.add(Measure("q0", acq_channel=0, acq_protocol='ThresholdedAcquisition'))
           schedule.add(Measure("q4", acq_channel=1, acq_protocol='ThresholdedAcquisition'))

           comp_schedule = compiler.compile(schedule)
           comp_schedule.compiled_instructions

   :param data: A dictionary containing the compiled instructions and related data. The
                keys are strings representing tab names and the values are dictionaries
                containing the respective instruction data.
   :type data: dict
   :param parent_tab_name: A string representing the name of the parent tab in the user interface.
                           If not specified, the function will use a default parent tab name.
   :type parent_tab_name: str, Optional

   :returns: widgets.Tab or None
                 A Tab widget containing the structured representation of compiled
                 instructions if the input data is not empty, otherwise None.



