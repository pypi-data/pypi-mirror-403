circuit_to_device
=================

.. py:module:: qblox_scheduler.backends.circuit_to_device 

.. autoapi-nested-parse::

   Compilation backend for quantum-circuit to quantum-device layer.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.circuit_to_device.compile_circuit_to_device_with_config_validation
   qblox_scheduler.backends.circuit_to_device._compile_circuit_to_device
   qblox_scheduler.backends.circuit_to_device.set_pulse_and_acquisition_clock
   qblox_scheduler.backends.circuit_to_device._extract_clock_freqs
   qblox_scheduler.backends.circuit_to_device._extract_clocks_used
   qblox_scheduler.backends.circuit_to_device._set_pulse_and_acquisition_clock
   qblox_scheduler.backends.circuit_to_device._valid_clock_in_schedule
   qblox_scheduler.backends.circuit_to_device._clocks_compatible
   qblox_scheduler.backends.circuit_to_device._assert_operation_valid_device_level
   qblox_scheduler.backends.circuit_to_device._compile_multiplexed
   qblox_scheduler.backends.circuit_to_device._compile_single_device_element
   qblox_scheduler.backends.circuit_to_device._compile_two_device_elements
   qblox_scheduler.backends.circuit_to_device._compile_circuit_to_device_pulse_compensation
   qblox_scheduler.backends.circuit_to_device._get_device_repr_from_cfg
   qblox_scheduler.backends.circuit_to_device._get_device_repr_from_cfg_multiplexed



.. py:function:: compile_circuit_to_device_with_config_validation(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, config: qblox_scheduler.backends.graph_compilation.CompilationConfig) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Add pulse information to all gates in the schedule.

   Before calling this function, the schedule can contain abstract operations (gates or
   measurements). This function adds pulse and acquisition information with respect to
   ``config`` as they are expected to arrive to device (latency or distortion corrections
   are not taken into account).

   From a point of view of :ref:`sec-compilation`, this function converts a schedule
   defined on a quantum-circuit layer to a schedule defined on a quantum-device layer.

   :param schedule: The schedule to be compiled.
   :param config: Compilation config for
                  :class:`~qblox_scheduler.backends.graph_compilation.ScheduleCompiler`, of
                  which only the :attr:`.CompilationConfig.device_compilation_config`
                  is used in this compilation step.

   :returns: :
                 The modified `.TimeableSchedule`` with pulse information added to all gates,
                 or the unmodified schedule if circuit to device compilation is not necessary.



.. py:function:: _compile_circuit_to_device(operation: qblox_scheduler.schedules.schedule.TimeableSchedule, device_cfg: qblox_scheduler.backends.graph_compilation.DeviceCompilationConfig, device_overrides: dict) -> qblox_scheduler.schedules.schedule.TimeableSchedule
                 _compile_circuit_to_device(operation: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule, device_cfg: qblox_scheduler.backends.graph_compilation.DeviceCompilationConfig, device_overrides: dict) -> qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule

.. py:function:: set_pulse_and_acquisition_clock(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, config: qblox_scheduler.backends.graph_compilation.CompilationConfig) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Ensures that each pulse/acquisition-level clock resource is added to the schedule,
   and validates the given configuration.

   If a pulse/acquisition-level clock resource has not been added
   to the schedule and is present in device_cfg, it is added to the schedule.

   A warning is given when a clock resource has conflicting frequency
   definitions, and an error is raised if the clock resource is unknown.

   :param schedule: The schedule to be compiled.
   :param config: Compilation config for
                  :class:`~qblox_scheduler.backends.graph_compilation.ScheduleCompiler`, of
                  which only the :attr:`.CompilationConfig.device_compilation_config`
                  is used in this compilation step.

   :returns: :
                 The modified `.TimeableSchedule`` with all clock resources added, or the unmodified
                 schedule if circuit to device compilation is not necessary.

   :Warns: **RuntimeWarning** -- When clock has conflicting frequency definitions.

   :raises RuntimeError: When operation is not at pulse/acquisition-level.
   :raises ValueError: When clock frequency is unknown.
   :raises ValueError: When clock frequency is NaN.


.. py:function:: _extract_clock_freqs(operation: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule, all_clock_freqs: dict[str, float]) -> None

.. py:function:: _extract_clocks_used(operation: qblox_scheduler.operations.operation.Operation) -> set[str]

.. py:function:: _set_pulse_and_acquisition_clock(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, operation: qblox_scheduler.schedules.schedule.TimeableSchedule, all_clock_freqs: dict[str, float], verified_clocks: list) -> qblox_scheduler.schedules.schedule.TimeableSchedule
                 _set_pulse_and_acquisition_clock(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, operation: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule, all_clock_freqs: dict[str, float], verified_clocks: list) -> qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule

   Ensures that each pulse/acquisition-level clock resource is added to the schedule.

   :param schedule: The resources from ``operation`` are added to `.TimeableSchedule``
                    if ``operation`` is not a `.TimeableSchedule``.
   :param operation: The ``operation`` to collect resources from.
   :param all_clock_freqs: All clock frequencies.
   :param verified_clocks: Already verified clocks.

   :returns: :
                 The modified ``operation`` with all clock resources added.



.. py:function:: _valid_clock_in_schedule(clock: str, all_clock_freqs: dict[str, float], schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, operation: qblox_scheduler.operations.operation.Operation) -> bool

   Asserts that valid clock is present. Returns whether clock is already in schedule.

   :param clock: Name of the clock
   :param all_clock_freqs: All clock frequencies
   :param schedule: TimeableSchedule that potentially has the clock in its resources
   :param operation: Quantify operation, to which the clock belongs. Only used for error message.

   :raises ValueError: Returns ValueError if (i) the device config is the only defined clock and
       contains nan values or (ii) no clock is defined.


.. py:function:: _clocks_compatible(clock: str, device_cfg: qblox_scheduler.backends.graph_compilation.DeviceCompilationConfig, schedule_clock_resources: dict[str, float]) -> bool

   Compare device config and schedule resources for compatibility of their clocks.

   Clocks can be defined in the device_cfg and in the schedule. They are consistent if

   - they have the same value
   - if the clock in the device config is nan (not the other way around)

   These conditions are also generalized to numpy arrays. Arrays of different length
   are only equal if all frequencies in the device config are nan.

   If the clocks are inconsistent, a warning message is emitted.

   :param clock: Name of the clock found in the device config and schedule
   :param device_cfg: Device config containing the ``clock``
   :param schedule_clock_resources: All clock resources in the schedule

   :returns: True if the clock frequencies are consistent.



.. py:function:: _assert_operation_valid_device_level(operation: qblox_scheduler.operations.operation.Operation) -> None

   Verifies that the operation has been compiled to device level.

   :param operation: Quantify operation


.. py:function:: _compile_multiplexed(operation: qblox_scheduler.operations.operation.Operation, device_elements: collections.abc.Sequence[str], operation_type: str, device_cfg: qblox_scheduler.backends.graph_compilation.DeviceCompilationConfig, device_overrides: dict) -> qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule

   Compiles gate with multiple device elements.

   Note: it updates the `operation`, if it can directly add pulse representation.


.. py:function:: _compile_single_device_element(operation: qblox_scheduler.operations.operation.Operation, device_element: str, operation_type: str, device_cfg: qblox_scheduler.backends.graph_compilation.DeviceCompilationConfig, device_overrides: dict) -> qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule

   Compiles gate with single device_element.

   Note: it updates the `operation`, if it can directly add pulse representation.


.. py:function:: _compile_two_device_elements(operation: qblox_scheduler.operations.operation.Operation, device_elements: collections.abc.Sequence[str], operation_type: str, device_cfg: qblox_scheduler.backends.graph_compilation.DeviceCompilationConfig, device_overrides: dict) -> qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule

   Compiles gate with multiple device elements.

   Note: it updates the `operation`, if it can directly add pulse representation.


.. py:function:: _compile_circuit_to_device_pulse_compensation(operation: qblox_scheduler.operations.pulse_compensation_library.PulseCompensation, device_cfg: qblox_scheduler.backends.graph_compilation.DeviceCompilationConfig, device_overrides: dict) -> qblox_scheduler.operations.pulse_compensation_library.PulseCompensation

   Compiles circuit-level pulse compensation operation to device-level.


.. py:function:: _get_device_repr_from_cfg(operation: qblox_scheduler.operations.operation.Operation, operation_cfg: qblox_scheduler.backends.graph_compilation.OperationCompilationConfig, device_overrides: dict) -> qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule

.. py:function:: _get_device_repr_from_cfg_multiplexed(operation: qblox_scheduler.operations.operation.Operation, operation_cfg: qblox_scheduler.backends.graph_compilation.OperationCompilationConfig, mux_idx: int, device_overrides: dict) -> qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule

.. py:exception:: ConfigKeyError(kind: str, missing: str, allowed: list[str])

   Bases: :py:obj:`KeyError`


   Custom exception for when a key is missing in a configuration file.


   .. py:attribute:: value
      :value: 'Uninferable "Uninferable" is not present in the configuration file; Uninferable must be one of...



.. py:exception:: MultipleKeysError(operation: str, matches: list[str])

   Bases: :py:obj:`KeyError`


   Custom exception for when symmetric keys are found in a configuration file.


   .. py:attribute:: value
      :value: 'Symmetric Operation Uninferable matches the following edges Uninferable in the QuantumDevice....



