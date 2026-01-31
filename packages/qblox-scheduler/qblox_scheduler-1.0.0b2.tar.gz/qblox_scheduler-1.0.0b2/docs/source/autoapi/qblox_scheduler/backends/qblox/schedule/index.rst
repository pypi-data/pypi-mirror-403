schedule
========

.. py:module:: qblox_scheduler.backends.qblox.schedule 

.. autoapi-nested-parse::

   Qblox backend specific schedule classes and associated utilities.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.schedule.CompiledInstructions




.. py:class:: CompiledInstructions(compiled_instructions: dict[Any, Any])

   Bases: :py:obj:`collections.UserDict`


   Create an interactive table that represents the compiled instructions.

   When displayed in an interactive environment such as a jupyter notebook, the
   dictionary is displayed as an interactive table (if supported by the
   backend), otherwise is displayed as a regular dictionary. Each key from the
   compiled instructions can be retrieved with the usual ``[key]`` and
   ``.get(key)`` syntax. A raw dictionary can also be obtained via the
   ``.data`` attribute.

   These values typically contain a combination of sequence files, waveform
   definitions, and parameters to configure on the instrument.

   See examples below as well.

   .. admonition:: Examples

       .. admonition:: Example

           .. jupyter-execute::
               :hide-code:

               from qblox_scheduler import (
                   BasicTransmonElement,
                   QuantumDevice,
                   SerialCompiler,
                   TimeableSchedule,
               )
               from qblox_scheduler.operations import (
                   Measure,
                   Reset,
                   X,
                   Y,
               )
               from qblox_scheduler.schemas.examples import utils
               from qcodes.instrument import Instrument

               Instrument.close_all()

               q0 = BasicTransmonElement("q0")
               q4 = BasicTransmonElement("q4")

               for qubit in [q0, q4]:
                   qubit.rxy.amp180 = 0.115
                   qubit.rxy.beta = 2.5e-10
                   qubit.clock_freqs.f01 = 7.3e9
                   qubit.clock_freqs.f12 = 7.0e9
                   qubit.clock_freqs.readout = 8.0e9
                   qubit.measure.acq_delay = 100e-9

               quantum_device = QuantumDevice(name="quantum_device0")
               quantum_device.add_element(q0)
               quantum_device.add_element(q4)

               hardware_config = utils.load_json_example_scheme(
                   "qblox_hardware_config_transmon.json"
               )
               quantum_device.hardware_config = hardware_config

               compiler = SerialCompiler("compiler")
               compiler.quantum_device = quantum_device

           .. jupyter-execute::

               schedule = TimeableSchedule("demo compiled instructions")
               schedule.add(Reset("q0", "q4"))
               schedule.add(X("q0"))
               schedule.add(Y("q4"))
               schedule.add(Measure("q0", acq_channel=0, acq_protocol="ThresholdedAcquisition"))
               schedule.add(Measure("q4", acq_channel=1, acq_protocol="ThresholdedAcquisition"))

               compiled_schedule = compiler.compile(schedule)
               compiled_instructions = compiled_schedule.compiled_instructions
               compiled_instructions


       .. admonition:: CompiledInstructions behave like dictionaries


           .. jupyter-execute::

               compiled_instructions["cluster0"]["cluster0_module4"]["sequencers"]["seq0"].integration_length_acq

   :param compiled_instructions: Instructions in a dictionary form that are sent to the hardware.
   :type compiled_instructions: dict


   .. py:attribute:: data

      The raw compiled instructions in a dictionary form.


   .. py:method:: _ipython_display_() -> None

      Generate interactive table when running in jupyter notebook.



