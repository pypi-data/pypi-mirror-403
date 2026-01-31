pulses
======

.. py:module:: qblox_scheduler.backends.qblox.operation_handling.pulses 

.. autoapi-nested-parse::

   Classes for handling pulses.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.operation_handling.pulses.PulseStrategyPartial
   qblox_scheduler.backends.qblox.operation_handling.pulses.GenericPulseStrategy
   qblox_scheduler.backends.qblox.operation_handling.pulses.DigitalOutputStrategy
   qblox_scheduler.backends.qblox.operation_handling.pulses.MarkerPulseStrategy
   qblox_scheduler.backends.qblox.operation_handling.pulses.DigitalPulseStrategy



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.operation_handling.pulses._get_i_and_q_gain_from_pulse_info
   qblox_scheduler.backends.qblox.operation_handling.pulses._get_var_from_supported_expression



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.operation_handling.pulses.logger


.. py:data:: logger

.. py:class:: PulseStrategyPartial(operation_info: qblox_scheduler.backends.types.qblox.OpInfo, channel_name: str)

   Bases: :py:obj:`qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy`, :py:obj:`abc.ABC`


   Contains the logic shared between all the pulses.

   :param operation_info: The operation info that corresponds to this pulse.
   :param channel_name: Specifies the channel identifier of the hardware config (e.g. `complex_output_0`).


   .. py:attribute:: _amplitude_path_I
      :type:  float | qblox_scheduler.operations.variables.Variable | None


   .. py:attribute:: _amplitude_path_Q
      :type:  float | qblox_scheduler.operations.variables.Variable | None


   .. py:attribute:: _pulse_info
      :type:  qblox_scheduler.backends.types.qblox.OpInfo


   .. py:attribute:: channel_name


   .. py:property:: operation_info
      :type: qblox_scheduler.backends.types.qblox.OpInfo


      Property for retrieving the operation info.


.. py:function:: _get_i_and_q_gain_from_pulse_info(pulse_info: dict[str, Any]) -> tuple[float | qblox_scheduler.operations.variables.Variable | None, float | qblox_scheduler.operations.variables.Variable | None]

.. py:function:: _get_var_from_supported_expression(expression: qblox_scheduler.operations.expressions.Expression) -> qblox_scheduler.operations.variables.Variable

.. py:class:: GenericPulseStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo, channel_name: str)

   Bases: :py:obj:`PulseStrategyPartial`


   Default class for handling pulses.

   No assumptions are made with regards to the pulse shape and no optimizations
   are done.

   :param operation_info: The operation info that corresponds to this pulse.
   :param channel_name: Specifies the channel identifier of the hardware config (e.g. `complex_output_0`).


   .. py:attribute:: _amplitude_path_I
      :type:  float | qblox_scheduler.operations.variables.Variable | None
      :value: None



   .. py:attribute:: _amplitude_path_Q
      :type:  float | qblox_scheduler.operations.variables.Variable | None
      :value: None



   .. py:attribute:: _waveform_index0
      :type:  int | None
      :value: None



   .. py:attribute:: _waveform_index1
      :type:  int | None
      :value: None



   .. py:attribute:: _waveform_len
      :type:  int | None
      :value: None



   .. py:method:: generate_data(wf_dict: dict[str, Any]) -> None

      Generates the data and adds them to the ``wf_dict`` (if not already present).

      In complex mode (e.g. ``complex_output_0``), the NCO produces real-valued data
      (:math:`I_\\text{IF}`) on sequencer path_I and imaginary data (:math:`Q_\\text{IF}`)
      on sequencer path_Q.

      .. math::
          \\underbrace{\\begin{bmatrix}
          \\cos\\omega t & -\\sin\\omega t \\\\
          \\sin\\omega t & \\phantom{-}\\cos\\omega t \\end{bmatrix}}_\\text{NCO}
          \\begin{bmatrix}
          I \\\\
          Q \\end{bmatrix} =
          \\begin{bmatrix}
          I \\cdot \\cos\\omega t - Q \\cdot\\sin\\omega t \\\\
          I \\cdot \\sin\\omega t + Q \\cdot\\cos\\omega t \\end{bmatrix}
          \\begin{matrix}
          \\ \\text{(path_I)} \\\\
          \\ \\text{(path_Q)} \\end{matrix}
          =
          \\begin{bmatrix}
          I_\\text{IF} \\\\
          Q_\\text{IF} \\end{bmatrix}


      In real mode (e.g. ``real_output_0``), the NCO produces :math:`I_\\text{IF}` on
      path_I


      .. math::
          \\underbrace{\\begin{bmatrix}
          \\cos\\omega t & -\\sin\\omega t \\\\
          \\sin\\omega t & \\phantom{-}\\cos\\omega t \\end{bmatrix}}_\\text{NCO}
          \\begin{bmatrix}
          I \\\\
          Q \\end{bmatrix}  =
          \\begin{bmatrix}
          I \\cdot \\cos\\omega t - Q \\cdot\\sin\\omega t\\\\
           - \\end{bmatrix}
          \\begin{matrix}
          \\ \\text{(path_I)} \\\\
          \\ \\text{(path_Q)} \\end{matrix}
          =
          \\begin{bmatrix}
          I_\\text{IF} \\\\
          - \\end{bmatrix}


      Note that the fields marked with `-` represent waveforms that are not relevant
      for the mode.


      :param wf_dict: The dictionary to add the waveform to. N.B. the dictionary is modified in
                      function.
      :param domains: The domains used in the schedule, keyed by variable. This is added as temporarily
                      to ensure we do not upload unnecessary waveforms. The domain information will be used to
                      figure out whether or not a "Q" path waveform needs to be uploaded.

      :raises ValueError: Data is complex (has an imaginary component), but the channel_name is not
          set as complex (e.g. ``complex_output_0``).



   .. py:method:: insert_qasm(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Add the assembly instructions for the Q1 sequence processor that corresponds to
      this pulse.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



.. py:class:: DigitalOutputStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo, channel_name: str)

   Bases: :py:obj:`PulseStrategyPartial`, :py:obj:`abc.ABC`


   Interface class for :class:`MarkerPulseStrategy` and :class:`DigitalPulseStrategy`.

   Both classes work very similarly, since they are both strategy classes for the
   `~qblox_scheduler.operations.pulse_library.MarkerPulse`. The
   ``MarkerPulseStrategy`` is for the QCM/QRM modules, and the ``DigitalPulseStrategy``
   for the QTM.


   .. py:method:: generate_data(wf_dict: dict[str, Any]) -> None

      Returns None as no waveforms are generated in this strategy.



.. py:class:: MarkerPulseStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo, channel_name: str, module_options: qblox_scheduler.backends.types.qblox.ClusterModuleDescription)

   Bases: :py:obj:`DigitalOutputStrategy`


   If this strategy is used a digital pulse is played on the corresponding marker.


   .. py:attribute:: module_options


   .. py:method:: insert_qasm(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Inserts the QASM instructions to play the marker pulse.
      Note that for RF modules the first two bits of set_mrk
      are used as switches for the RF outputs.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



.. py:class:: DigitalPulseStrategy(operation_info: qblox_scheduler.backends.types.qblox.OpInfo, channel_name: str)

   Bases: :py:obj:`DigitalOutputStrategy`


   If this strategy is used a digital pulse is played
   on the corresponding digital output channel.


   .. py:method:: insert_qasm(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None

      Inserts the QASM instructions to play the marker pulse.
      Note that for RF modules the first two bits of set_mrk
      are used as switches for the RF outputs.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



