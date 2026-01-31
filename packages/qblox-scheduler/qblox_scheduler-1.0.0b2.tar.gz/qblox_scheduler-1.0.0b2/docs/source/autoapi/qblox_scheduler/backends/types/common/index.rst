common
======

.. py:module:: qblox_scheduler.backends.types.common 

.. autoapi-nested-parse::

   Common python dataclasses for multiple backends.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.common.SoftwareDistortionCorrection
   qblox_scheduler.backends.types.common.HardwareDistortionCorrection
   qblox_scheduler.backends.types.common.ModulationFrequencies
   qblox_scheduler.backends.types.common.MixerCorrections
   qblox_scheduler.backends.types.common.HardwareOptions
   qblox_scheduler.backends.types.common.LocalOscillatorDescription
   qblox_scheduler.backends.types.common.IQMixerDescription
   qblox_scheduler.backends.types.common.OpticalModulatorDescription
   qblox_scheduler.backends.types.common.HardwareDescription
   qblox_scheduler.backends.types.common.Connectivity
   qblox_scheduler.backends.types.common.HardwareCompilationConfig
   qblox_scheduler.backends.types.common.ThresholdedTriggerCountMetadata
   qblox_scheduler.backends.types.common.PartialChannelPath
   qblox_scheduler.backends.types.common.ChannelPath




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.common.LatencyCorrection


.. py:exception:: ValidationWarning

   Bases: :py:obj:`UserWarning`


   Warning type for dubious arguments passed to pydantic models.


.. py:data:: LatencyCorrection

   Latency correction in seconds for a port-clock combination.

   Positive values delay the operations on the corresponding port-clock combination,
   while negative values shift the operation backwards in time with respect to other
   operations in the schedule.

   .. note::

       If the port-clock combination of a signal is not specified in the corrections,
       it is set to zero in compilation. The minimum correction over all port-clock
       combinations is then subtracted to allow for negative latency corrections and to
       ensure minimal wait time (see
       :meth:`~qblox_scheduler.backends.corrections.determine_relative_latency_corrections`).

   .. admonition:: Example
       :class: dropdown

       Let's say we have specified two latency corrections in the CompilationConfig:

       .. code-block:: python

           compilation_config.hardware_options.latency_corrections = {
               "q0:res-q0.ro": LatencyCorrection(-20e-9),
               "q0:mw-q0.01": LatencyCorrection(120e9),
           }

       In this case, all operations on port ``"q0:mw"`` and clock ``"q0.01"`` will
       be delayed by 140 ns with respect to operations on port ``"q0:res"`` and
       clock ``"q0.ro"``.

.. py:class:: SoftwareDistortionCorrection(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Software distortion correction information for a port-clock combination.

   .. admonition:: Example
       :class: dropdown

       .. jupyter-execute::

           from qblox_scheduler.backends.types.common import (
               SoftwareDistortionCorrection
           )

           distortion_corrections = {
               "q0:fl-cl0.baseband": SoftwareDistortionCorrection(
                   filter_func="scipy.signal.lfilter",
                   input_var_name="x",
                   kwargs={
                       "b": [0, 0.25, 0.5],
                       "a": [1]
                   },
                   clipping_values=[-2.5, 2.5]
               )
           }


   .. py:attribute:: filter_func
      :type:  str

      The function applied to the waveforms.


   .. py:attribute:: input_var_name
      :type:  str

      The argument to which the waveforms will be passed in the filter_func.


   .. py:attribute:: kwargs
      :type:  dict[str, list | qblox_scheduler.structure.types.NDArray]

      The keyword arguments that are passed to the filter_func.


   .. py:attribute:: clipping_values
      :type:  list | None
      :value: None


      The optional boundaries to which the corrected pulses will be clipped,
      upon exceeding.


   .. py:attribute:: sampling_rate
      :type:  float
      :value: 1000000000.0


      The sample rate of the corrected pulse, in Hz.


   .. py:method:: _only_two_clipping_values(clipping_values) -> list | None | ValueError
      :classmethod:



.. py:class:: HardwareDistortionCorrection(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Parent class for hardware distortion correction.


.. py:class:: ModulationFrequencies(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Modulation frequencies for a port-clock combination.

   .. admonition:: Example
       :class: dropdown

       .. jupyter-execute::

           from qblox_scheduler.backends.types.common import (
               ModulationFrequencies
           )

           modulation_frequencies = {
               "q0:res-q0.ro": ModulationFrequencies(
                   interm_freq=None,
                   lo_freq=6e9,
               )
           }


   .. py:attribute:: interm_freq
      :type:  float | None
      :value: None


      The intermodulation frequency (IF) used for this port-clock combination.


   .. py:attribute:: lo_freq
      :type:  float | None
      :value: None


      The local oscillator frequency (LO) used for this port-clock combination.


.. py:class:: MixerCorrections(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Mixer corrections for a port-clock combination.

   .. admonition:: Example
       :class: dropdown

       .. jupyter-execute::

           from qblox_scheduler.backends.types.common import (
               MixerCorrections
           )

           mixer_corrections = {
               "q0:mw-q0.01": MixerCorrections(
                   dc_offset_i = -0.0542,
                   dc_offset_q = -0.0328,
                   amp_ratio = 0.95,
                   phase_error= 0.07,
               )
           }


   .. py:attribute:: dc_offset_i
      :type:  float
      :value: 0.0


      The DC offset on the I channel used for this port-clock combination.


   .. py:attribute:: dc_offset_q
      :type:  float
      :value: 0.0


      The DC offset on the Q channel used for this port-clock combination.


   .. py:attribute:: amp_ratio
      :type:  float
      :value: 1.0


      The mixer gain ratio used for this port-clock combination.


   .. py:attribute:: phase_error
      :type:  float
      :value: 0.0


      The mixer phase error used for this port-clock combination.


.. py:class:: HardwareOptions(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Datastructure containing the hardware options for each port-clock combination.

   This datastructure contains the HardwareOptions that are currently shared among
   the existing backends. Subclassing is required to add backend-specific options,
   see e.g.,
   :class:`~qblox_scheduler.backends.types.qblox.QbloxHardwareOptions`,


   .. py:attribute:: crosstalk
      :type:  dict[str, dict[str, float | complex]] | None
      :value: None


      Dictionary containing the crosstalk values between ports on the quantum device.
      The crosstalk values are given as a dictionary of dictionaries, where the outer
      dictionary keys are the source ports and the inner dictionary keys are the target
      ports.


   .. py:attribute:: latency_corrections
      :type:  dict[str, LatencyCorrection] | None
      :value: None


      Dictionary containing the latency corrections (values) that should be applied
      to operations on a certain port-clock combination (keys).


   .. py:attribute:: distortion_corrections
      :type:  dict[str, SoftwareDistortionCorrection] | None
      :value: None


      Dictionary containing the distortion corrections (values) that should be applied
      to waveforms on a certain port-clock combination (keys).


   .. py:attribute:: modulation_frequencies
      :type:  dict[str, ModulationFrequencies] | None
      :value: None


      Dictionary containing the modulation frequencies (values) that should be used
      for signals on a certain port-clock combination (keys).


   .. py:attribute:: mixer_corrections
      :type:  dict[str, MixerCorrections] | None
      :value: None


      Dictionary containing the mixer corrections (values) that should be used
      for signals on a certain port-clock combination (keys).


.. py:class:: LocalOscillatorDescription(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Information needed to specify a Local Oscillator in the :class:`~.CompilationConfig`.


   .. py:attribute:: instrument_type
      :type:  Literal['LocalOscillator']
      :value: 'LocalOscillator'


      The field discriminator for this HardwareDescription datastructure.


   .. py:attribute:: instrument_name
      :type:  str | None
      :value: None


      The QCoDeS instrument name corresponding to this Local Oscillator.


   .. py:attribute:: generic_icc_name
      :type:  str | None
      :value: None


      The name of the :class:`~.GenericInstrumentCoordinatorComponent`
      corresponding to this Local Oscillator.


   .. py:attribute:: frequency_param
      :type:  str
      :value: 'frequency'


      The QCoDeS parameter that is used to set the LO frequency.


   .. py:attribute:: power_param
      :type:  str
      :value: 'power'


      The QCoDeS parameter that is used to set the LO power.


   .. py:attribute:: power
      :type:  int | None
      :value: None


      The power setting for this Local Oscillator.


   .. py:method:: _only_default_generic_icc_name(generic_icc_name) -> str | None
      :classmethod:



.. py:class:: IQMixerDescription(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Information needed to specify an IQ Mixer in the :class:`~.CompilationConfig`.


   .. py:attribute:: instrument_type
      :type:  Literal['IQMixer']
      :value: 'IQMixer'


      The field discriminator for this HardwareDescription datastructure.


.. py:class:: OpticalModulatorDescription(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Information needed to specify an optical modulator in the :class:`~.CompilationConfig`.


   .. py:attribute:: instrument_type
      :type:  Literal['OpticalModulator']
      :value: 'OpticalModulator'


      The field discriminator for this HardwareDescription datastructure.


.. py:class:: HardwareDescription(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Specifies a piece of hardware and its instrument-specific settings.

   Each supported instrument type should have its own datastructure that inherits from
   this class.
   For examples, see :class:`~qblox_scheduler.backends.types.qblox.ClusterDescription`,
   :class:`~.LocalOscillatorDescription`.

   This datastructure is used to specify the control-hardware ports that
   are included in the :class:`~.Connectivity` graph.


   .. py:attribute:: instrument_type
      :type:  str

      The instrument type.


.. py:class:: Connectivity(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Connectivity between ports on the quantum device and control hardware inputs/outputs.

   The connectivity graph can be parsed from a list of edges, which are given by a
   set of two strings that each correspond to an input/output on an instrument or a port
   on the quantum device.

   .. note::
       To specify connections between more than one pair of ports at once, one can
       also specify a list of ports within the edge input (see example below, and also
       see :ref:`sec-connectivity-examples`).

   The connectivity graph can be drawn using :meth:`~.draw`, which groups the nodes
   according to the instrument name (specified by the string before the first ``"."``
   in the node name; the name is omitted for the quantum device).

   .. admonition:: Example
       :class: dropdown

       .. jupyter-execute::

           from qblox_scheduler.backends.types.common import (
               Connectivity
           )

           connectivity_dict = {
               "graph": [
                   ("awg0.channel_0", "q0:mw"),
                   ("awg0.channel_1", "q1:mw"),
                   ("rom0.channel_0", ["q0:res", "q1:res"]),
               ]
           }

           connectivity = Connectivity.model_validate(connectivity_dict)
           connectivity.draw()


   .. py:attribute:: graph
      :type:  qblox_scheduler.structure.types.Graph

      The connectivity graph consisting of i/o ports (nodes) on the quantum device and on
      the control hardware, and their connections (edges).


   .. py:method:: _unroll_lists_of_ports_in_edges_input(graph) -> list[tuple[Any, Any]]
      :classmethod:



   .. py:method:: serialize_graph(graph: qblox_scheduler.structure.types.Graph) -> list[tuple[Any, Any]]

      Serialize the graph as a list of edges.



   .. py:method:: draw(ax: matplotlib.axes.Axes | None = None, figsize: tuple[float, float] = (20, 10), **options) -> matplotlib.axes.Axes

      Draw the connectivity graph using matplotlib.

      The nodes are positioned using a multipartite layout, where the nodes
      are grouped by instrument (identified by the first part of the node name).


      :param ax: Matplotlib axis to plot the figure on.
      :param figsize: Optional figure size, defaults to something slightly larger that fits the
                      size of the nodes.
      :param options: optional keyword arguments that are passed to
                      :code:`networkx.draw_networkx`.

      :returns: :
                    Matplotlib axis on which the figure is plotted.




.. py:class:: HardwareCompilationConfig(/, **data: Any)

   Bases: :py:obj:`abc.ABC`, :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Information required to compile a schedule to the control-hardware layer.

   From a point of view of :ref:`sec-compilation` this information is needed
   to convert a schedule defined on a quantum-device layer to compiled instructions
   that can be executed on the control hardware.

   This datastructure defines the overall structure of a ``HardwareCompilationConfig``.
   Specific hardware backends should customize fields within this structure by inheriting
   from this class and specifying their own `"config_type"`, see e.g.,
   :class:`~qblox_scheduler.backends.qblox_backend.QbloxHardwareCompilationConfig`,


   .. py:attribute:: config_type
      :type:  str

      A reference to the ``HardwareCompilationConfig`` DataStructure for the backend
      that is used.


   .. py:attribute:: hardware_description
      :type:  dict[str, HardwareDescription]

      Datastructure describing the control hardware instruments in the setup and their
      high-level settings.


   .. py:attribute:: hardware_options
      :type:  HardwareOptions

      The :class:`~qblox_scheduler.backends.types.common.HardwareOptions` used in the
      compilation from the quantum-device layer to the control-hardware layer.


   .. py:attribute:: connectivity
      :type:  Connectivity | dict

      Datastructure representing how ports on the quantum device are connected to ports
      on the control hardware.


   .. py:attribute:: compilation_passes
      :type:  list[qblox_scheduler.backends.graph_compilation.SimpleNodeConfig]
      :value: None


      The list of compilation nodes that should be called in succession to compile a
      schedule to instructions for the control hardware.


   .. py:method:: _check_connectivity_graph_nodes_format()


   .. py:method:: _connectivity_old_style_hw_cfg_empty_hw_options_and_descriptions()


.. py:class:: ThresholdedTriggerCountMetadata

   Metadata specifically for the ThresholdedTriggerCount acquisition.


   .. py:attribute:: threshold
      :type:  int

      The threshold of the ThresholdedTriggerCount acquisition.


   .. py:attribute:: condition
      :type:  qblox_scheduler.enums.TriggerCondition

      The comparison condition (greater-equal, less-than) for the ThresholdedTriggerCount acquisition.


.. py:class:: PartialChannelPath

   Path of a sequencer channel (partial version).


   .. py:attribute:: re_channel_path
      :type:  ClassVar[re.Pattern]


   .. py:attribute:: cluster_name
      :type:  str


   .. py:attribute:: module_name
      :type:  str


   .. py:attribute:: channel_name
      :type:  str | None


   .. py:method:: from_path(path: str) -> typing_extensions.Self
      :classmethod:


      Instantiate a `ChannelPath` object from a path string.



   .. py:property:: module_idx
      :type: int


      The module index in the module name.


   .. py:property:: channel_idx
      :type: int


      The channel index in the channel name.

      A channel name is always formatted as "type_direction_#" where # is the channel index. This
      property extracts the channel index.


.. py:class:: ChannelPath

   Bases: :py:obj:`PartialChannelPath`


   Path of a sequencer channel (full version).


   .. py:attribute:: re_channel_path
      :type:  ClassVar[re.Pattern]


   .. py:attribute:: channel_name
      :type:  str


   .. py:attribute:: channel_name_measure
      :type:  None | set[str]
      :value: None



   .. py:method:: add_channel_name_measure(channel_name_measure: str) -> None

      Add an extra input channel name for measure operation.



