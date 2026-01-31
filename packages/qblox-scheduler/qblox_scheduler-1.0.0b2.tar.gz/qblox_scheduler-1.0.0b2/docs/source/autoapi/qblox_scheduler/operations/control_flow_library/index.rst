control_flow_library
====================

.. py:module:: qblox_scheduler.operations.control_flow_library 

.. autoapi-nested-parse::

   Standard control flow operations for use with the qblox_scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.control_flow_library.ControlFlowOperation
   qblox_scheduler.operations.control_flow_library.LoopStrategy
   qblox_scheduler.operations.control_flow_library.LoopOperation
   qblox_scheduler.operations.control_flow_library.ConditionalOperation
   qblox_scheduler.operations.control_flow_library.ControlFlowSpec
   qblox_scheduler.operations.control_flow_library.Loop
   qblox_scheduler.operations.control_flow_library.Conditional




.. py:class:: ControlFlowOperation(name: str)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Control flow operation that can be used as an ``Operation`` in ``.TimeableSchedule``.

   This is an abstract class. Each concrete implementation
   of the control flow operation decides how and when
   their ``body`` operation is executed.


   .. py:property:: body
      :type: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule

      :abstractmethod:


      Body of a control flow.


   .. py:method:: get_used_port_clocks() -> set[tuple[str, str]]

      Extracts which port-clock combinations are used in this control flow operation.

      :returns: :
                    All (port, clock) combinations that operations
                    in the body of this control flow operation uses.




.. py:class:: LoopStrategy

   Bases: :py:obj:`qblox_scheduler.enums.StrEnum`


   Strategy to use for implementing loops.

   REALTIME: Use native loops.
   UNROLLED: Unroll loop at compilation time into separate instructions.


   .. py:attribute:: REALTIME
      :value: 'realtime'



   .. py:attribute:: UNROLLED
      :value: 'unrolled'



.. py:class:: LoopOperation(body: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.schedule.Schedule, *, repetitions: int | None = None, domain: dict[qblox_scheduler.operations.variables.Variable, qblox_scheduler.operations.loop_domains.LinearDomain] | None = None, t0: float = 0.0, strategy: LoopStrategy | None = None)

   Bases: :py:obj:`ControlFlowOperation`


   Loop over another operation predefined times.

   Repeats the operation defined in ``body`` ``repetitions`` times.
   The actual implementation depends on the backend.

   One of ``domain`` or ``repetitions`` must be specified.

   :param body: Operation to be repeated
   :param repetitions: Number of repetitions, by default None
   :param domain: Linear domain to loop over, by default None
   :param t0: Time offset, by default 0
   :param strategy: Strategy to use for implementing this loop, by default None to make own decision


   .. py:property:: body
      :type: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule


      Body of a control flow.


   .. py:property:: duration
      :type: float


      Duration of a control flow.


   .. py:property:: domain
      :type: dict[qblox_scheduler.operations.variables.Variable, qblox_scheduler.operations.loop_domains.LinearDomain]


      Linear domain to loop over.


   .. py:property:: repetitions
      :type: int


      Number of times the body will execute.


   .. py:property:: strategy
      :type: LoopStrategy | None


      What strategy to use for implementing this loop.


.. py:class:: ConditionalOperation(body: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.schedule.Schedule, qubit_name: str, t0: float = 0.0, hardware_buffer_time: float = constants.MIN_TIME_BETWEEN_OPERATIONS * 1e-09)

   Bases: :py:obj:`ControlFlowOperation`


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



   .. py:property:: body
      :type: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule


      Body of a control flow.


   .. py:property:: duration
      :type: float


      Duration of a control flow.


.. py:class:: ControlFlowSpec

   Control flow specification to be used at ``Schedule.add``.

   The users can specify any concrete control flow with
   the ``control_flow`` argument to ``Schedule.add``.
   The ``ControlFlowSpec`` is only a type which by itself
   cannot be used for the ``control_flow`` argument,
   use any concrete control flow derived from it.


   .. py:method:: create_operation(body: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule) -> qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule
      :abstractmethod:


      Transform the control flow specification to an operation or schedule.



.. py:class:: Loop(repetitions: int, t0: float = 0.0, strategy: LoopStrategy | None = None)

   Bases: :py:obj:`ControlFlowSpec`


   Loop control flow specification to be used at ``Schedule.add``.

   For more information, see ``LoopOperation``.

   :param repetitions: Number of repetitions
   :param t0: Time offset, by default 0
   :param strategy: Strategy to use for implementing the loop, by default None


   .. py:attribute:: repetitions


   .. py:attribute:: t0
      :value: 0.0



   .. py:attribute:: strategy
      :value: None



   .. py:method:: create_operation(body: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule) -> LoopOperation

      Transform the control flow specification to an operation or schedule.



.. py:class:: Conditional(qubit_name: str, t0: float = 0.0)

   Bases: :py:obj:`ControlFlowSpec`


   Conditional control flow specification to be used at ``Schedule.add``.

   For more information, see ``ConditionalOperation``.

   :param qubit_name: Target device element.
   :param t0: Time offset, by default 0


   .. py:attribute:: device_element_name


   .. py:attribute:: t0
      :value: 0.0



   .. py:method:: create_operation(body: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule) -> ConditionalOperation

      Transform the control flow specification to an operation or schedule.



