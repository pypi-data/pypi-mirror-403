circuit_diagram
===============

.. py:module:: qblox_scheduler.schedules._visualization.circuit_diagram 

.. autoapi-nested-parse::

   Plotting functions used in the visualization backend of the sequencer.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules._visualization.circuit_diagram._ControlFlowEnd



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules._visualization.circuit_diagram.gate_box
   qblox_scheduler.schedules._visualization.circuit_diagram.pulse_baseband
   qblox_scheduler.schedules._visualization.circuit_diagram.pulse_modulated
   qblox_scheduler.schedules._visualization.circuit_diagram.meter
   qblox_scheduler.schedules._visualization.circuit_diagram.acq_meter
   qblox_scheduler.schedules._visualization.circuit_diagram.acq_meter_text
   qblox_scheduler.schedules._visualization.circuit_diagram.cnot
   qblox_scheduler.schedules._visualization.circuit_diagram.cz
   qblox_scheduler.schedules._visualization.circuit_diagram.reset
   qblox_scheduler.schedules._visualization.circuit_diagram._walk_schedule
   qblox_scheduler.schedules._visualization.circuit_diagram._walk_schedule_only_operations
   qblox_scheduler.schedules._visualization.circuit_diagram._draw_operation
   qblox_scheduler.schedules._visualization.circuit_diagram._get_indices
   qblox_scheduler.schedules._visualization.circuit_diagram._draw_loop
   qblox_scheduler.schedules._visualization.circuit_diagram._draw_conditional
   qblox_scheduler.schedules._visualization.circuit_diagram._get_device_element_and_port_map_from_schedule
   qblox_scheduler.schedules._visualization.circuit_diagram._get_feedback_label_and_device_element_idx
   qblox_scheduler.schedules._visualization.circuit_diagram.circuit_diagram_matplotlib



.. py:function:: gate_box(ax: matplotlib.axes.Axes, time: float, device_element_idxs: list[int], text: str, **kw) -> None

   A box for a single gate containing a label.

   :param ax: The matplotlib Axes.
   :param time: The time of the gate.
   :param device_element_idxs: The device_element indices.
   :param text: The gate name.
   :param kw: Additional keyword arguments to be passed to drawing the gate box.


.. py:function:: pulse_baseband(ax: matplotlib.axes.Axes, time: float, device_element_idxs: list[int], text: str, **kw) -> None

   Adds a visual indicator for a Baseband pulse to the `matplotlib.axes.Axis`
   instance.

   :param ax: The matplotlib Axes.
   :param time: The time of the pulse.
   :param device_element_idxs: The device_element indices.
   :param text: The pulse name.
   :param kw: Additional keyword arguments to be passed to drawing the pulse.


.. py:function:: pulse_modulated(ax: matplotlib.axes.Axes, time: float, device_element_idxs: list[int], text: str, **kw) -> None

   Adds a visual indicator for a Modulated pulse to the `matplotlib.axes.Axis`
   instance.

   :param ax: The matplotlib Axes.
   :param time: The time of the pulse.
   :param device_element_idxs: The device_element indices.
   :param text: The pulse name.
   :param kw: Additional keyword arguments to be passed to drawing the pulse.


.. py:function:: meter(ax: matplotlib.axes.Axes, time: float, device_element_idxs: list[int], text: str, **kw) -> None

   A simple meter to depict a measurement.

   :param ax: The matplotlib Axes.
   :param time: The time of the measurement.
   :param device_element_idxs: The device_element indices.
   :param text: The measurement name.
   :param kw: Additional keyword arguments to be passed to drawing the meter.


.. py:function:: acq_meter(ax: matplotlib.axes.Axes, time: float, device_element_idxs: list[int], text: str, **kw) -> None

   Variation of the meter to depict a acquisition.

   :param ax: The matplotlib Axes.
   :param time: The time of the measurement.
   :param device_element_idxs: The device_element indices.
   :param text: The measurement name.
   :param kw: Additional keyword arguments to be passed to drawing the acq meter.


.. py:function:: acq_meter_text(ax: matplotlib.axes.Axes, time: float, device_element_idxs: list[int], text: str, **kw) -> None

   Same as acq_meter, but also displays text.

   :param ax: The matplotlib Axes.
   :param time: The time of the measurement.
   :param device_element_idxs: The device_element indices.
   :param text: The measurement name.
   :param kw: Additional keyword arguments to be passed to drawing the acq meter.


.. py:function:: cnot(ax: matplotlib.axes.Axes, time: float, device_element_idxs: list[int], text: str, **kw) -> None

   Markers to denote a CNOT gate between two device_elements.

   :param ax: The matplotlib Axes.
   :param time: The time of the CNOT.
   :param device_element_idxs: The device_element indices.
   :param text: The CNOT name.
   :param kw: Additional keyword arguments to be passed to drawing the CNOT.


.. py:function:: cz(ax: matplotlib.axes.Axes, time: float, device_element_idxs: list[int], text: str, **kw) -> None

   Markers to denote a CZ gate between two device_elements.

   :param ax: The matplotlib Axes.
   :param time: The time of the CZ.
   :param device_element_idxs: The device_element indices.
   :param text: The CZ name.
   :param kw: Additional keyword arguments to be passed to drawing the CZ.


.. py:function:: reset(ax: matplotlib.axes.Axes, time: float, device_element_idxs: list[int], text: str, **kw) -> None

   A broken line to denote device_element initialization.

   :param ax: matplotlib axis object.
   :param time: x position to draw the reset on
   :param device_element_idxs: indices of the device_elements that the reset is performed on.
   :param text: The reset name.
   :param kw: Additional keyword arguments to be passed to drawing the reset.


.. py:class:: _ControlFlowEnd(*args, **kwds)

   Bases: :py:obj:`enum.Enum`


   Identifier for end of a control-flow scope.


   .. py:attribute:: LOOP_END


   .. py:attribute:: CONDI_END


.. py:function:: _walk_schedule(sched_or_op: qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.operations.operation.Operation, time_offset: int = 0) -> collections.abc.Iterator[tuple[int, qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule | _ControlFlowEnd]]

.. py:function:: _walk_schedule_only_operations(sched_or_op: qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.operations.operation.Operation) -> collections.abc.Iterator[qblox_scheduler.operations.operation.Operation]

.. py:function:: _draw_operation(operation: qblox_scheduler.operations.operation.Operation, device_element_map: dict[str, int], port_map: dict[str, int], ax: matplotlib.axes.Axes, time: int, schedule_resources: dict[str, qblox_scheduler.resources.Resource]) -> None

.. py:function:: _get_indices(sched_or_op: qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.operations.operation.Operation, device_element_map: dict[str, int], port_map: dict[str, int]) -> set[int]

.. py:function:: _draw_loop(ax: matplotlib.axes.Axes, device_element_map: dict[str, int], port_map: dict[str, int], operation: qblox_scheduler.operations.control_flow_library.LoopOperation, start_time: int, end_time: int, x_offset: float = 0.35, y_offset: float = 0.3, fraction: float = 0.2) -> None

.. py:function:: _draw_conditional(ax: matplotlib.axes.Axes, measure_time: int, measure_device_element_idx: int, body: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule, body_start: int, body_end: int, device_element_map: dict[str, int], port_map: dict[str, int]) -> None

.. py:function:: _get_device_element_and_port_map_from_schedule(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule) -> tuple[dict[str, int], dict[str, int]]

.. py:function:: _get_feedback_label_and_device_element_idx(operation: qblox_scheduler.operations.operation.Operation, port_map: dict[str, int], device_element_map: dict[str, int]) -> tuple[str, int] | None

   Check if the operation is an acquisition/measure gate with a feedback trigger label.


.. py:function:: circuit_diagram_matplotlib(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, figsize: tuple[int, int] | None = None, ax: matplotlib.axes.Axes | None = None) -> tuple[matplotlib.figure.Figure | None, matplotlib.axes.Axes]

