compilation
===========

.. py:module:: qblox_scheduler.compilation 

.. autoapi-nested-parse::

   Compiler for the qblox_scheduler.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.compilation._determine_absolute_timing
   qblox_scheduler.compilation._determine_absolute_timing_schedule
   qblox_scheduler.compilation._determine_scheduling_strategy
   qblox_scheduler.compilation._validate_schedulable_references
   qblox_scheduler.compilation._populate_references_graph
   qblox_scheduler.compilation._make_timing_constraints_explicit
   qblox_scheduler.compilation._make_timing_constraints_explicit_for_schedulable
   qblox_scheduler.compilation._determine_default_ref_pt
   qblox_scheduler.compilation._determine_default_ref_pt_new
   qblox_scheduler.compilation._determine_default_ref_schedulables_by_schedulable
   qblox_scheduler.compilation._get_start_time
   qblox_scheduler.compilation._normalize_absolute_timing
   qblox_scheduler.compilation._unroll_loops
   qblox_scheduler.compilation._unroll_single_loop
   qblox_scheduler.compilation.validate_config
   qblox_scheduler.compilation.plot_schedulable_references_graph



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.compilation.logger


.. py:data:: logger

.. py:function:: _determine_absolute_timing(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, time_unit: Literal['physical', 'ideal', None] = 'physical', config: qblox_scheduler.backends.graph_compilation.CompilationConfig | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule
                 _determine_absolute_timing(schedule: qblox_scheduler.operations.operation.Operation, time_unit: Literal['physical', 'ideal', None] = 'physical', config: qblox_scheduler.backends.graph_compilation.CompilationConfig | None = None) -> qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule

   Determine the absolute timing of a schedule based on the timing constraints.

   This function determines absolute timings for every operation in the
   :attr:`~.TimeableScheduleBase.schedulables`. It does this by:

       1. iterating over all and elements in the :attr:`~.TimeableScheduleBase.schedulables`.
       2. determining the absolute time of the reference operation
          - reference point :code:`"ref_pt"` of the reference operation defaults to
          :code:`"end"` in case it is not set (i.e., is :code:`None`).
       3. determining the start of the operation based on the :code:`rel_time` and
          :code:`duration` of operations
          - reference point :code:`"ref_pt_new"` of the added operation defaults to
          :code:`"start"` in case it is not set.


   :param schedule: The schedule for which to determine timings.
   :param config: Compilation config for
                  :class:`~qblox_scheduler.backends.graph_compilation.ScheduleCompiler`.
   :param time_unit: Whether to use physical units to determine the absolute time or ideal time.
                     When :code:`time_unit == "physical"` the duration attribute is used.
                     When :code:`time_unit == "ideal"` the duration attribute is ignored and treated
                     as if it is :code:`1`.
                     When :code:`time_unit == None` it will revert to :code:`"physical"`.

   :returns: :
                 The modified `.TimeableSchedule`` where the absolute time for each operation has been
                 determined.

   :raises NotImplementedError: If the scheduling strategy is not SchedulingStrategy.ASAP


.. py:function:: _determine_absolute_timing_schedule(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, time_unit: Literal['physical', 'ideal', None], config: qblox_scheduler.backends.graph_compilation.CompilationConfig | None) -> qblox_scheduler.schedules.schedule.TimeableSchedule

.. py:function:: _determine_scheduling_strategy(config: qblox_scheduler.backends.graph_compilation.CompilationConfig | None = None) -> qblox_scheduler.enums.SchedulingStrategy

.. py:function:: _validate_schedulable_references(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, references_graph: networkx.DiGraph) -> None

   Check the schedulable references for circular references.


.. py:function:: _populate_references_graph(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule) -> networkx.DiGraph

   Add nodes and edges to the graph containing schedulable references.


.. py:function:: _make_timing_constraints_explicit(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, strategy: qblox_scheduler.enums.SchedulingStrategy) -> None

.. py:function:: _make_timing_constraints_explicit_for_schedulable(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, schedulable_name: str, default_reference_schedulable_name: str | None, strategy: qblox_scheduler.enums.SchedulingStrategy) -> None

.. py:function:: _determine_default_ref_pt(strategy: qblox_scheduler.enums.SchedulingStrategy) -> Literal['start', 'end']

.. py:function:: _determine_default_ref_pt_new(strategy: qblox_scheduler.enums.SchedulingStrategy) -> Literal['start', 'end']

.. py:function:: _determine_default_ref_schedulables_by_schedulable(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, strategy: qblox_scheduler.enums.SchedulingStrategy) -> list[tuple[str, str | None]]

.. py:function:: _get_start_time(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, t_constr: qblox_scheduler.schedules.schedule.TimingConstraint, curr_op: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule, time_unit: Literal['physical', 'ideal', None]) -> float

.. py:function:: _normalize_absolute_timing(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, config: qblox_scheduler.backends.graph_compilation.CompilationConfig | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule

.. py:function:: _unroll_loops(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, config: qblox_scheduler.backends.graph_compilation.CompilationConfig | None = None) -> qblox_scheduler.schedules.schedule.TimeableSchedule
                 _unroll_loops(schedule: qblox_scheduler.operations.operation.Operation, config: qblox_scheduler.backends.graph_compilation.CompilationConfig | None = None) -> qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule

.. py:function:: _unroll_single_loop(op: qblox_scheduler.operations.control_flow_library.LoopOperation) -> qblox_scheduler.schedules.schedule.TimeableSchedule

.. py:function:: validate_config(config: dict, scheme_fn: str) -> bool

   Validate a configuration using a schema.

   :param config: The configuration to validate
   :param scheme_fn: The name of a json schema in the qblox_scheduler.schemas folder.

   :returns: :
                 True if valid



.. py:function:: plot_schedulable_references_graph(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule) -> None

   Show the schedulable reference graph.

   Can be used as a debugging tool to spot any circular references.


