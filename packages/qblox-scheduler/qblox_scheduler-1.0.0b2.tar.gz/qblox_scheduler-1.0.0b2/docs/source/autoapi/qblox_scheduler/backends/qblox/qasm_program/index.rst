qasm_program
============

.. py:module:: qblox_scheduler.backends.qblox.qasm_program 

.. autoapi-nested-parse::

   QASM program class for Qblox backend.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.qasm_program._AcqBinRegister
   qblox_scheduler.backends.qblox.qasm_program.QASMProgram



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.qasm_program.expand_awg_from_normalised_range



.. py:class:: _AcqBinRegister

   Container for additional data for acquisition bin register
   at a specific loop depth. For each loop depth, this data is stored.


   .. py:attribute:: bin_mode
      :type:  qblox_scheduler.enums.BinMode | None

      Bin mode of the loop.


   .. py:attribute:: increments
      :type:  int

      Stores the number of increments the register already did
      for all acquisitions in total that are inside this loop depth.
      For example, if there is a loop within this block with
      3 repetitions and 2 acquisitions, and a single acquisition directly in this block,
      then the increments is 2*3+1.


.. py:function:: expand_awg_from_normalised_range(val: float, immediate_size: int = constants.IMMEDIATE_SZ_GAIN, param: str | None = None, operation: qblox_scheduler.backends.types.qblox.OpInfo | None = None) -> int

   Takes the value of an awg gain or offset parameter
   in normalized form (abs(param) <= 1.0),
   and expands it to an integer
   in the appropriate range required by the sequencer.

   :param val: The value of the parameter to expand.
   :param immediate_size: The size of the immediate. Used to find the max int value.
   :param param: The name of the parameter, to make a possible exception message more
                 descriptive.
   :param operation: The operation this value is expanded for, to make a possible exception
                     message more descriptive.

   :returns: :
                 The expanded value of the parameter.

   :raises ValueError: Parameter is not in the normalized range.


.. py:class:: QASMProgram(static_hw_properties: qblox_scheduler.backends.types.qblox.StaticHardwareProperties, register_manager: qblox_scheduler.backends.qblox.register_manager.RegisterManager | None = None, align_fields: bool = True)

   Class that holds the compiled Q1ASM program that is to be executed by the sequencer.

   Apart from this the class holds some convenience functions that auto generate
   certain instructions with parameters, as well as update the elapsed time.

   :param static_hw_properties: Dataclass holding the properties of the hardware that this program is to be
                                played on.
   :param register_manager: The register manager that keeps track of the occupied/available registers.
   :param align_fields: If True, make QASM program more human-readable by aligning its fields.


   .. py:attribute:: static_hw_properties

      Dataclass holding the properties of the hardware that this program is to be
      played on.


   .. py:attribute:: register_manager

      The register manager that keeps track of the occupied/available registers.


   .. py:attribute:: align_fields
      :value: True


      If true, all labels, instructions, arguments and comments
      in the string representation of the program are printed on the same indention level.
      This worsens performance.


   .. py:attribute:: time_last_acquisition_triggered
      :type:  int | None
      :value: None


      Time on which the last acquisition was triggered. Is ``None`` if no previous
      acquisition was triggered.


   .. py:attribute:: time_last_pulse_triggered
      :type:  int | None
      :value: None


      Time on which the last operation was triggered. Is ``None`` if no previous
      operation was triggered.


   .. py:attribute:: instructions
      :type:  list[list]
      :value: []


      A list containing the instructions added to the program. The instructions
      added are in turn a list of the instruction string with arguments.


   .. py:attribute:: conditional_manager

      The conditional manager that keeps track of the conditionals.


   .. py:attribute:: _lock_conditional
      :type:  bool
      :value: False


      A lock to prevent nested conditionals.


   .. py:attribute:: _elapsed_times_in_loops
      :type:  list[int]
      :value: [0]


      The time elapsed in its current form.
      This is used  to keep track of the total and nested loop timing and necessary waits.


   .. py:attribute:: _acq_bin_registers
      :type:  dict[str, list[_AcqBinRegister]]

      For acquisition loop averaging and appending,
      we keep track of the acquisition bin registers, and their metadata
      to properly increment/decrement them in loops.
      The keys are the registers, and the values are a list of bin register data.
      Each element in the list corresponds to a loop depth,
      for example the 2nd element in that list is for an inner-inner loop.


   .. py:property:: elapsed_time
      :type: int


      Current elapsed time of all the instructions in ns.
      It needs to be manually adjusted after each modifications of the QASM program.
      If the QASM program is in a loop,
      only one repetition's worth of elapsed time should be registered.
      After a loop is ended, ``QASMProgram`` will automatically adjust the correct
      elapsed time with all repetitions.


   .. py:method:: get_instruction_as_list(instruction: str, *args: int | str, label: str | None = None, comment: str | None = None) -> list[str]
      :staticmethod:


      Takes an instruction with arguments, label and comment and turns it into the
      list required by the class.

      :param instruction: The instruction to use. This should be one specified in
                          :mod:`~qblox_scheduler.backends.qblox.q1asm_instructions`
                          or the assembler will raise an exception.
      :param args: Arguments to be passed.
      :param label: Adds a label to the line. Used for jumps and loops.
      :param comment: Optionally add a comment to the instruction.

      :returns: :
                    List that contains all the passed information in the valid format for the
                    program.

      :raises SyntaxError: More arguments passed than the sequencer allows.



   .. py:method:: emit(*args, **kwargs) -> list[str]

      Wrapper around the ``get_instruction_as_list`` which adds it to this program.

      :param args: All arguments to pass to `get_instruction_as_list`.
      :param \*\*kwargs: All keyword arguments to pass to `get_instruction_as_list`.

      :returns: :
                    A list containing instructions.




   .. py:method:: set_latch(op_strategies: collections.abc.Sequence[qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy]) -> None

      Set the latch that is needed for conditional playback.

      This assumes that the latch address is present inside the pulses'
      `operation_info`. If no latch address is found, nothing is emitted.

      :param op_strategies: The op_strategies containing the pulses to search the latch address in.



   .. py:method:: auto_wait(wait_time: int, count_as_elapsed_time: bool = True, comment: str | None = None) -> None

      Automatically emits a correct wait command. If the wait time is longer than
      allowed by the sequencer it correctly breaks it up into multiple wait
      instructions. If the number of wait instructions is too high (>4), a loop will
      be used.

      :param wait_time: Time to wait in ns.
      :param count_as_elapsed_time: If true, this wait time is taken into account when keeping track of timing.
                                    Otherwise, the wait instructions are added but this wait time is ignored in
                                    the timing calculations in the rest of the program.
      :param comment: Allows to override the default comment.

      :raises ValueError: If ``wait_time <= 0``.



   .. py:method:: wait_till_start_operation(operation: qblox_scheduler.backends.types.qblox.OpInfo) -> None

      Waits until the start of a pulse or acquisition.

      :param operation: The pulse or acquisition that we want to wait for.

      :raises ValueError: If wait time < 0.



   .. py:method:: _process_awg_instruction_args(path_I: float | qblox_scheduler.operations.variables.Variable, path_Q: float | qblox_scheduler.operations.variables.Variable, param_name: str, operation: qblox_scheduler.backends.types.qblox.OpInfo) -> tuple[int | str, int | str]


   .. py:method:: set_gain_from_amplitude(amplitude_path_I: float | qblox_scheduler.operations.variables.Variable, amplitude_path_Q: float | qblox_scheduler.operations.variables.Variable, operation: qblox_scheduler.backends.types.qblox.OpInfo) -> None

      Sets the gain such that a 1.0 in waveform memory corresponds to the full awg gain.

      :param amplitude_path_I: Voltage to set on path_I.
      :param amplitude_path_Q: Voltage to set on path_Q.
      :param operation: The operation for which this is done. Used for the exception messages.



   .. py:method:: set_offset_from_float_or_variable(offset_path_I: float | qblox_scheduler.operations.variables.Variable, offset_path_Q: float | qblox_scheduler.operations.variables.Variable, operation: qblox_scheduler.backends.types.qblox.OpInfo) -> None

      Sets the offset such that a 1.0 float value corresponds to the maximum offset.

      :param offset_path_I: Voltage to set on path_I.
      :param offset_path_Q: Voltage to set on path_Q.
      :param operation: The operation for which this is done. Used for the exception messages.



   .. py:method:: merge_some_arithmetic_instructions() -> None

      Merges all add and sub instructions that happen after each other,
      and are only applied in a form "add RX,NUMBER,RX.
      This is useful especially to merge instructions
      that increment and decrement bin indices for averaging,
      because they can happen right after each other for the same register,
      which is not allowed in Q1ASM.



   .. py:method:: conditional(operation: qblox_scheduler.backends.qblox.operation_handling.virtual.ConditionalStrategy) -> collections.abc.Generator[None, None, None]

      Defines a conditional block in the QASM program.

      When this context manager is entered/exited it will insert additional
      ``set_cond`` QASM instructions in the program that specify the
      conditionality of a set of instructions.

      The following example should make it clear what is happening.

      .. code-block:: none

          set_cond set_enable=1, mask=0, operator=OR, else_duration=4
          <50 ns duration of instructions that contains 3 real time instructions>

          set_cond set_enable=1, mask=0, operator=NOR, else_duration=4
          wait 50-3*4+4 = 42 ns # adding an additional 4 ns to make math work out

          set_cond set_enable=0, mask=0, operator=OR, else_duration=4

      The `else_duration` is the wait time per real time instruction in the
      conditional block. If a trigger happened, the first block runs normally for
      50 ns, the second block runs for 4 ns. If there is no trigger, the first
      block runs for 3*4 = 12 ns, second block for 42 ns. So the duration in
      both cases is 42 ns. Note that `set_cond` itself has zero duration.

      The exact values that need to be passed to the ``set_cond``
      instructions are determined while the qasm program is generated with the
      help of
      :class:`~qblox_scheduler.backends.qblox.conditional.FeedbackTriggerCondition`
      and
      :class:`~qblox_scheduler.backends.qblox.conditional.ConditionalManager`.

      :param operation: The conditional strategy that defines the start of a conditional block.
      :type operation: ConditionalStrategy



   .. py:method:: loop(label: str, repetitions: int, domain: dict[qblox_scheduler.operations.variables.Variable, qblox_scheduler.operations.loop_domains.LinearDomain] | None = None) -> collections.abc.Generator[None, None, None]

      Defines a context manager that can be used to generate a loop in the QASM
      program.

      :param label: The label to use for the jump.
      :param repetitions: The amount of iterations to perform.
      :param domain: A dictionary of domains to sweep over (in a zip-fashion), keyed by variable. If None, a
                     simple repetition loop is generated. By default None.

      .. rubric:: Examples

      This adds a loop to the program that loops 10 times over a wait of 100 ns.

      .. jupyter-execute::

          from qblox_scheduler.backends.qblox.qasm_program import QASMProgram
          from qblox_scheduler.backends.qblox.instrument_compilers import QCMCompiler
          from qblox_scheduler.backends.qblox import register_manager
          from qblox_scheduler.backends.types.qblox import QCMDescription

          qasm = QASMProgram(
              static_hw_properties=QCMCompiler.static_hw_properties,
              register_manager=register_manager.RegisterManager(),
              align_fields=True,
          )

          with qasm.loop(label="repeat", repetitions=10):
              qasm.auto_wait(100)

          qasm.instructions



   .. py:method:: _initialize_sweep_registers(domain: dict[qblox_scheduler.operations.variables.Variable, qblox_scheduler.operations.loop_domains.LinearDomain]) -> None


   .. py:method:: _update_sweep_registers(domain: dict[qblox_scheduler.operations.variables.Variable, qblox_scheduler.operations.loop_domains.LinearDomain]) -> None


   .. py:method:: _free_sweep_registers(domain: dict[qblox_scheduler.operations.variables.Variable, qblox_scheduler.operations.loop_domains.LinearDomain]) -> None


   .. py:method:: temp_registers(amount: int = 1) -> collections.abc.Iterator[list[str]]

      Context manager for using a register temporarily. Frees up the register
      afterwards.

      :param amount: The amount of registers to temporarily use.

      :Yields: Either a single register or a list of registers.



   .. py:method:: parse_program_line(program_line: str) -> tuple[str, list[str], str | None, str]
      :staticmethod:


      Parses a single line of a Q1ASM program and extracts its components.

      This function processes a line of Q1ASM code;
      handling labels, instructions, arguments, and comments.

      :param program_line: A single line of Q1ASM code to be parsed.

      :returns: instruction
                    The instruction part of the Q1ASM line, empty string if no instruction present.
                arguments
                    A list of arguments associated with the instruction, empty list if no arguments present.
                label
                    The processed label extracted from the line, or None if no label is present.
                comment
                    The comment extracted from the line; empty string if no comment is present.

      :raises ValueError: If the program line is not a valid q1asm format

      .. rubric:: Examples

      >>> QASMProgram.parse_program_line("example_label: move 10, R1  # Initialize R1")
      ('move', ['10', 'R1'], 'example_label', 'Initialize R1')



   .. py:method:: update_and_adjust_acq_bin_register(register: str, loop_bin_modes: list[qblox_scheduler.enums.BinMode], acq_channel: collections.abc.Hashable) -> None

      Increment the acquisition bin register,
      and store metadata regarding the bin modes of any nested
      loops the acquisition may be contained in
      to adjust the acquisition bin register when necessary.



   .. py:method:: _adjust_acq_bin_registers_end_loop() -> None


   .. py:method:: _adjust_acq_bin_registers_start_loop() -> None


   .. py:method:: _adjust_acq_bin_registers_after_loop(repetitions: int) -> None


   .. py:method:: fix_missing_nops() -> None

      Insert NOP instructions where needed.



