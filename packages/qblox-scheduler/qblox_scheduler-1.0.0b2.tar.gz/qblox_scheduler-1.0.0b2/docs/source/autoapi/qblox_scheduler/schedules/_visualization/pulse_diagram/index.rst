pulse_diagram
=============

.. py:module:: qblox_scheduler.schedules._visualization.pulse_diagram 

.. autoapi-nested-parse::

   Functions for drawing pulse diagrams.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules._visualization.pulse_diagram.SampledPulse
   qblox_scheduler.schedules._visualization.pulse_diagram.SampledAcquisition
   qblox_scheduler.schedules._visualization.pulse_diagram.ScheduledInfo



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules._visualization.pulse_diagram.get_sampled_pulses_from_voltage_offsets
   qblox_scheduler.schedules._visualization.pulse_diagram.get_sampled_pulses
   qblox_scheduler.schedules._visualization.pulse_diagram.get_sampled_acquisitions
   qblox_scheduler.schedules._visualization.pulse_diagram.merge_pulses_and_offsets
   qblox_scheduler.schedules._visualization.pulse_diagram._extract_schedule_infos
   qblox_scheduler.schedules._visualization.pulse_diagram.sample_schedule
   qblox_scheduler.schedules._visualization.pulse_diagram.pulse_diagram_plotly
   qblox_scheduler.schedules._visualization.pulse_diagram.deduplicate_legend_handles_labels
   qblox_scheduler.schedules._visualization.pulse_diagram.plot_single_subplot_mpl
   qblox_scheduler.schedules._visualization.pulse_diagram.plot_multiple_subplots_mpl
   qblox_scheduler.schedules._visualization.pulse_diagram.pulse_diagram_matplotlib
   qblox_scheduler.schedules._visualization.pulse_diagram.get_window_operations
   qblox_scheduler.schedules._visualization.pulse_diagram.plot_window_operations
   qblox_scheduler.schedules._visualization.pulse_diagram.plot_acquisition_operations



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules._visualization.pulse_diagram.logger


.. py:data:: logger

.. py:class:: SampledPulse

   Class containing the necessary information to display pulses in a plot.


   .. py:attribute:: time
      :type:  numpy.ndarray


   .. py:attribute:: signal
      :type:  numpy.ndarray


   .. py:attribute:: label
      :type:  str


.. py:class:: SampledAcquisition

   Class containing the necessary information to display acquisitions in a plot.


   .. py:attribute:: t0
      :type:  float


   .. py:attribute:: duration
      :type:  float


   .. py:attribute:: label
      :type:  str


.. py:class:: ScheduledInfo

   Class containing pulse or acquisition info, with some additional information.

   This class is used in the schedule sampling process to temporarily hold pulse info
   or acquisition info dictionaries, together with some useful information from the
   operation and schedulable that they are a part of.


   .. py:attribute:: op_info
      :type:  dict[str, Any]

      Pulse info or acquisition info.


   .. py:attribute:: time
      :type:  float

      The sum of the ``Schedulable["abs_time"]`` and the ``info["t0"]``.


   .. py:attribute:: op_name
      :type:  str

      The name of the operation containing the pulse or acquisition info.


.. py:function:: get_sampled_pulses_from_voltage_offsets(schedule: qblox_scheduler.TimeableSchedule | qblox_scheduler.CompiledSchedule, offset_infos: dict[str, dict[str, list[ScheduledInfo]]], x_min: float, x_max: float, modulation: Literal['off', 'if', 'clock'] = 'off', modulation_if: float = 0.0, sampling_rate: float = 1000000000.0, sampled_pulses: dict[str, list[SampledPulse]] | None = None) -> dict[str, list[SampledPulse]]

   Generate :class:`.SampledPulse` objects from :class:`.VoltageOffset` pulse_info dicts.

   This function groups all VoltageOffset operations by port-clock combination and
   turns each of those groups of operations into a single SampledPulse. The returned
   dictionary contains these SampledPulse objects grouped by port.

   :param schedule: The schedule to render.
   :param offset_infos: A nested dictionary containing lists of pulse_info dictionaries. The outer
                        dictionary's keys are ports, and the inner dictionary's keys are clocks.
   :param x_min: The left limit of the x-axis of the intended plot.
   :param x_max: The right limit of the x-axis of the intended plot.
   :param modulation: Determines if modulation is included in the visualization.
   :param modulation_if: Modulation frequency used when modulation is set to "if".
   :param sampling_rate: Number of samples per second to draw when drawing modulated pulses.
   :param sampled_pulses: An already existing dictionary (same type as the return value). If provided,
                          this dictionary will be extended with the SampledPulse objects created in this
                          function.

   :returns: dict[str, list[SampledPulse]] :
                 SampledPulse objects grouped by port.



.. py:function:: get_sampled_pulses(schedule: qblox_scheduler.TimeableSchedule | qblox_scheduler.CompiledSchedule, pulse_infos: dict[str, list[ScheduledInfo]], x_min: float, x_max: float, modulation: Literal['off', 'if', 'clock'] = 'off', modulation_if: float = 0.0, sampling_rate: float = 1000000000.0, sampled_pulses: dict[str, list[SampledPulse]] | None = None) -> dict[str, list[SampledPulse]]

   Generate :class:`.SampledPulse` objects from pulse_info dicts.

   This function creates a SampledPulse for each pulse_info dict. The pulse_info must
   contain a valid ``"wf_func"``.

   :param schedule: The schedule to render.
   :param pulse_infos: A dictionary from ports to lists of pulse_info dictionaries.
   :param x_min: The left limit of the x-axis of the intended plot.
   :param x_max: The right limit of the x-axis of the intended plot.
   :param modulation: Determines if modulation is included in the visualization.
   :param modulation_if: Modulation frequency used when modulation is set to "if".
   :param sampling_rate: The time resolution used to sample the schedule in Hz.
   :param sampled_pulses: An already existing dictionary (same type as the return value). If provided,
                          this dictionary will be extended with the SampledPulse objects created in this
                          function.

   :returns: dict[str, list[SampledPulse]] :
                 SampledPulse objects grouped by port.



.. py:function:: get_sampled_acquisitions(acq_infos: dict[str, list[ScheduledInfo]]) -> dict[str, list[SampledAcquisition]]

   Generate :class:`.SampledAcquisition` objects from acquisition_info dicts.

   :param acq_infos: A dictionary from ports to lists of acquisition_info dictionaries.

   :returns: dict[str, list[SampledAcquisition]] :
                 SampledAcquisition objects grouped by port.



.. py:function:: merge_pulses_and_offsets(operations: list[SampledPulse]) -> SampledPulse

   Combine multiple ``SampledPulse`` objects by interpolating the ``signal`` at the
   ``time`` points used by all pulses together, and then summing the result.
   Interpolation outside a ``SampledPulse.time`` array results in 0 for that pulse.


.. py:function:: _extract_schedule_infos(operation: qblox_scheduler.Operation | qblox_scheduler.schedules.schedule.TimeableScheduleBase, port_list: list[str] | None, time_offset: float, offset_infos: dict[str, dict[str, list[ScheduledInfo]]], pulse_infos: dict[str, list[ScheduledInfo]], acq_infos: dict[str, list[ScheduledInfo]]) -> None

.. py:function:: sample_schedule(schedule: qblox_scheduler.TimeableSchedule | qblox_scheduler.CompiledSchedule, port_list: list[str] | None = None, modulation: Literal['off', 'if', 'clock'] = 'off', modulation_if: float = 0.0, sampling_rate: float = 1000000000.0, x_range: tuple[float, float] = (-np.inf, np.inf), combine_waveforms_on_same_port: bool = False) -> dict[str, tuple[list[SampledPulse], list[SampledAcquisition]]]

   Generate :class:`.SampledPulse` and :class:`.SampledAcquisition` objects grouped by
   port.

   This function generates SampledPulse objects for all pulses and voltage offsets
   defined in the TimeableSchedule, and SampledAcquisition for all acquisitions defined in the
   TimeableSchedule.

   :param schedule: The schedule to render.
   :param port_list: A list of ports to show. if set to ``None`` (default), it will use all ports in
                     the TimeableSchedule.
   :param modulation: Determines if modulation is included in the visualization.
   :param modulation_if: Modulation frequency used when modulation is set to "if".
   :param sampling_rate: The time resolution used to sample the schedule in Hz.
   :param x_range: The range of the x-axis that is plotted, given as a tuple (left limit, right
                   limit). This can be used to reduce memory usage when plotting a small section of
                   a long pulse sequence. By default (-np.inf, np.inf).
   :param combine_waveforms_on_same_port: By default False. If True, combines all waveforms on the same port into one
                                          single waveform. The resulting waveform is the sum of all waveforms on that
                                          port (small inaccuracies may occur due to floating point approximation). If
                                          False, the waveforms are shown individually.

   :returns: dict[str, tuple[list[SampledPulse], list[SampledAcquisition]]] :
                 SampledPulse and SampledAcquisition objects grouped by port.



.. py:function:: pulse_diagram_plotly(sampled_pulses_and_acqs: dict[str, tuple[list[SampledPulse], list[SampledAcquisition]]], title: str = 'Pulse diagram', fig_ch_height: float = 300, fig_width: float = 1000) -> plotly.graph_objects.Figure

   Produce a plotly visualization of the pulses used in the schedule.

   :param sampled_pulses_and_acqs: SampledPulse and SampledAcquisition objects grouped by port.
   :param title: Plot title.
   :param fig_ch_height: Height for each channel subplot in px.
   :param fig_width: Width for the figure in px.

   :returns: :class:`plotly.graph_objects.Figure` :
                 the plot



.. py:function:: deduplicate_legend_handles_labels(ax: matplotlib.axes.Axes) -> None

   Remove duplicate legend entries.

   See also: https://stackoverflow.com/questions/13588920/stop-matplotlib-repeating-labels-in-legend/13589144#13589144


.. py:function:: plot_single_subplot_mpl(sampled_schedule: dict[str, list[SampledPulse]], ax: matplotlib.axes.Axes | None = None, title: str = 'Pulse diagram') -> tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]

   Plot all pulses for all ports in the same subplot using Matplotlib.

   Pulses in the same port have the same color and legend entry, and each port
   has its own legend entry.

   :param sampled_schedule: Dictionary mapping port names to lists of SampledPulse objects.
   :param ax: Existing axes to draw on. If None, a new figure and axes will be created.
   :param title: Title of the plot (default is "Pulse diagram").
   :type title: str, Optional

   :returns: fig :
                 The matplotlib figure object.
             ax :
                 The axes used for the subplot.



.. py:function:: plot_multiple_subplots_mpl(sampled_schedule: dict[str, list[SampledPulse]], title: str = 'Pulse diagram') -> tuple[matplotlib.figure.Figure, list[matplotlib.axes.Axes]]

   Plot pulses in a different subplot for each port in the sampled schedule.

   For each subplot, each different type of pulse gets its own color and legend
   entry.

   :param sampled_schedule: Dictionary that maps each used port to the sampled pulses played on that port.
   :param title: Plot title.

   :returns: fig :
                 A matplotlib :class:`matplotlib.figure.Figure` containing the subplots.

             axs :
                 An array of Axes objects belonging to the Figure.



.. py:function:: pulse_diagram_matplotlib(sampled_pulses_and_acqs: dict[str, tuple[list[SampledPulse], list[SampledAcquisition]]], multiple_subplots: bool = False, ax: matplotlib.axes.Axes | None = None, title: str = 'Pulse diagram') -> tuple[matplotlib.figure.Figure, matplotlib.axes.Axes | list[matplotlib.axes.Axes]]

   Plots a schedule using matplotlib.

   :param sampled_pulses_and_acqs: SampledPulse and SampledAcquisition objects grouped by port.
   :param multiple_subplots: Plot the pulses for each port on a different subplot if True, else plot
                             everything in one subplot. By default False. When using just one
                             subplot, the pulses are colored according to the port on which they
                             play. For multiple subplots, each pulse has its own
                             color and legend entry.
   :param ax: Axis onto which to plot. If ``None`` (default), this is created within the
              function. By default None.
   :param title: Plot title.

   :returns: fig :
                 A matplotlib :class:`matplotlib.figure.Figure` containing the subplot(s).

             ax :
                 The Axes object belonging to the Figure, or an array of Axes if
                 ``multiple_subplots=True``.



.. py:function:: get_window_operations(schedule: qblox_scheduler.TimeableSchedule) -> list[tuple[float, float, qblox_scheduler.Operation]]

   Return a list of all :class:`.WindowOperation`\s with start and end time.

   :param schedule: TimeableSchedule to use.

   :returns: :
                 List of all window operations in the schedule.



.. py:function:: plot_window_operations(schedule: qblox_scheduler.TimeableSchedule, ax: matplotlib.axes.Axes | None = None, time_scale_factor: float = 1) -> tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]

   Plot the window operations in a schedule.

   :param schedule: TimeableSchedule from which to plot window operations.
   :param ax: Axis handle to use for plotting.
   :param time_scale_factor: Used to scale the independent data before using as data for the
                             x-axis of the plot.

   :returns: fig
                 The matplotlib figure.
             ax
                 The matplotlib ax.



.. py:function:: plot_acquisition_operations(schedule: qblox_scheduler.TimeableSchedule, ax: matplotlib.axes.Axes | None = None, **kwargs) -> list[Any]

   Plot the acquisition operations in a schedule.

   :param schedule: TimeableSchedule from which to plot window operations.
   :param ax: Axis handle to use for plotting.
   :param kwargs: Passed to matplotlib plotting routine

   :returns: :
                 List of handles



