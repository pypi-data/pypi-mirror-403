pulse_scheme
============

.. py:module:: qblox_scheduler.schedules._visualization.pulse_scheme 

.. autoapi-nested-parse::

   Module containing functions for drawing pulse schemes and circuit diagrams
   using matplotlib.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules._visualization.pulse_scheme.new_pulse_fig
   qblox_scheduler.schedules._visualization.pulse_scheme.new_pulse_subplot
   qblox_scheduler.schedules._visualization.pulse_scheme.mw_pulse
   qblox_scheduler.schedules._visualization.pulse_scheme.flux_pulse
   qblox_scheduler.schedules._visualization.pulse_scheme.ram_Z_pulse
   qblox_scheduler.schedules._visualization.pulse_scheme.interval
   qblox_scheduler.schedules._visualization.pulse_scheme.meter
   qblox_scheduler.schedules._visualization.pulse_scheme.box_text



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules._visualization.pulse_scheme.logger


.. py:data:: logger

.. py:function:: new_pulse_fig(figsize: tuple[int, int] | None = None, ax: matplotlib.axes.Axes | None = None) -> tuple[matplotlib.figure.Figure | None, matplotlib.axes.Axes]

   Open a new figure and configure it to plot pulse schemes.

   :param figsize: Size of the figure.
   :param ax: Axis to use for plotting. If ``None``, then creates a new one.

   :returns: :
                 Tuple of figure handle and axis handle.



.. py:function:: new_pulse_subplot(fig: matplotlib.figure.Figure, *args, **kwargs) -> matplotlib.axes.Axes

   Add a new subplot configured for plotting pulse schemes to a figure.

   All `*args` and `**kwargs` are passed to fig.add_subplot.

   :param fig: Figure to add the subplot to.
   :param \*args: Positional arguments to pass to fig.add_subplot.
   :param \*\*kwargs: Keyword arguments to pass to fig.add_subplot.

   :returns: :



.. py:function:: mw_pulse(ax: matplotlib.axes.Axes, pos: float, y_offs: float = 0.0, width: float = 1.5, amp: float = 1, label: str | None = None, phase: float = 0, label_height: float = 1.3, color: str = constants.COLOR_ORANGE, modulation: str = 'normal', **plot_kws) -> float

   Draw a microwave pulse: Gaussian envelope with modulation.

   :param ax: Axis to plot on.
   :param pos: Position of the pulse.
   :param y_offs: Vertical offset of the pulse.
   :param width: Width of the pulse.
   :param amp: Amplitude
   :param label: Label to add to the pulse.
   :param label_height: Height of the label.
   :param color: Color of the pulse.
   :param modulation: Modulation

   :returns: :



.. py:function:: flux_pulse(ax: matplotlib.axes.Axes, pos: float, y_offs: float = 0.0, width: float = 2.5, s: float = 0.1, amp: float = 1.5, label: str | None = None, label_height: float = 1.7, color: str = constants.COLOR_ORANGE, **plot_kws) -> float

   Draw a smooth flux pulse, where the rising and falling edges are given by
   Fermi-Dirac functions.

   :param ax: Axis to plot on.
   :param pos: Position of the pulse.
   :param y_offs: Vertical offset of the pulse.
   :param width: Width of the pulse.
   :param s: smoothness of edge
   :param amp: Amplitude
   :param label: Label to add to the pulse.
   :param label_height: Height of the label.
   :param color: Color of the pulse.

   :returns: :



.. py:function:: ram_Z_pulse(ax: matplotlib.axes.Axes, pos: float, y_offs: float = 0.0, width: float = 2.5, s: float = 0.1, amp: float = 1.5, sep: float = 1.5, color: str = constants.COLOR_ORANGE) -> float

   Draw a Ram-Z flux pulse, i.e. only part of the pulse is shaded, to indicate
   cutting off the pulse at some time.

   :param ax: Axis to plot on.
   :param pos: Position of the pulse.
   :param y_offs: Vertical offset of the pulse.
   :param width: Width of the pulse.
   :param s: smoothness of edge
   :param amp: Amplitude
   :param sep: Separation between pulses.
   :param color: Color of the pulse.

   :returns: :



.. py:function:: interval(ax: matplotlib.axes.Axes, start: float, stop: float, y_offs: float = 0.0, height: float = 1.5, label: str | None = None, label_height: str | None = None, vlines: bool = True, color: str = 'k', arrowstyle: str = '<|-|>', **plot_kws) -> None

   Draw an arrow to indicate an interval.

   :param ax: Axis to plot on.
   :param pos: Position of the pulse.
   :param y_offs: Vertical offset of the pulse.
   :param width: Width of the pulse.
   :param s: smoothness of edge
   :param amp: Amplitude
   :param sep: Separation between pulses.
   :param color: Color of the pulse.
   :param arrow_style:

   :returns: :



.. py:function:: meter(ax: matplotlib.axes.Axes, x0: float, y0: float, y_offs: float = 0.0, width: float = 1.1, height: float = 0.8, color: str = 'black', framewidth: float = 0.0, fillcolor: str | None = None) -> None

   Draws a measurement meter on the specified position.

   :param ax:
   :param x0:
   :param y0:
   :param y_offs:
   :param width:
   :param height:
   :param color:
   :param framewidth:
   :param fillcolor:

   :returns: :



.. py:function:: box_text(ax: matplotlib.axes.Axes, x0: float, y0: float, text: str = '', width: float = 1.1, height: float = 0.8, color: str = 'black', fillcolor: str | None = None, textcolor: str = 'black', fontsize: int | None = None) -> None

   Draws a box filled with text at the specified position.

   :param ax:
   :param x0:
   :param y0:
   :param text:
   :param width:
   :param height:
   :param color:
   :param fillcolor:
   :param textcolor:
   :param fontsize:

   :returns: :



