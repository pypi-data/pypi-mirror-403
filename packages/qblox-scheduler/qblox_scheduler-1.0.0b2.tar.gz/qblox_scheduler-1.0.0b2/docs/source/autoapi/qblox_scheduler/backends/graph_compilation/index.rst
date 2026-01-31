graph_compilation
=================

.. py:module:: qblox_scheduler.backends.graph_compilation 

.. autoapi-nested-parse::

   Graph compilation backend of qblox-scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.graph_compilation.SimpleNodeConfig
   qblox_scheduler.backends.graph_compilation.OperationCompilationConfig
   qblox_scheduler.backends.graph_compilation.DeviceCompilationConfig
   qblox_scheduler.backends.graph_compilation.CompilationConfig
   qblox_scheduler.backends.graph_compilation.CompilationNode
   qblox_scheduler.backends.graph_compilation.SimpleNode
   qblox_scheduler.backends.graph_compilation.ScheduleCompiler
   qblox_scheduler.backends.graph_compilation.SerialCompiler
   qblox_scheduler.backends.graph_compilation.SerialCompilationConfig




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.graph_compilation.ConcreteHardwareCompilationConfig


.. py:data:: ConcreteHardwareCompilationConfig

.. py:exception:: CompilationError

   Bases: :py:obj:`RuntimeError`


   Custom exception class for failures in compilation of qblox-scheduler schedules.


.. py:class:: SimpleNodeConfig(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Datastructure specifying the structure of a simple compiler pass config.

   See also :class:`~.SimpleNode`.


   .. py:attribute:: name
      :type:  str

      The name of the compilation pass.


   .. py:attribute:: compilation_func
      :type:  collections.abc.Callable[[qblox_scheduler.schedules.schedule.TimeableSchedule, CompilationConfig], qblox_scheduler.schedules.schedule.TimeableScheduleBase]

      The function to perform the compilation pass as an
      importable string (e.g., "package_name.my_module.function_name").


   .. py:method:: _serialize_compilation_func(v: object) -> str


   .. py:method:: _import_compilation_func_if_str(fun: collections.abc.Callable[[qblox_scheduler.schedules.schedule.TimeableSchedule, Any], qblox_scheduler.schedules.schedule.TimeableSchedule]) -> collections.abc.Callable[[qblox_scheduler.schedules.schedule.TimeableSchedule, Any], qblox_scheduler.schedules.schedule.TimeableSchedule]
      :classmethod:



.. py:class:: OperationCompilationConfig(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Information required to compile an individual operation to the quantum-device layer.

   From a point of view of :ref:`sec-compilation` this information is needed
   to convert an operation defined on a quantum-circuit layer to an operation
   defined on a quantum-device layer.


   .. py:attribute:: factory_func
      :type:  collections.abc.Callable[Ellipsis, qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule] | None

      A callable designating a factory function used to create the representation
      of the operation at the quantum-device level.


   .. py:attribute:: factory_kwargs
      :type:  dict[str, Any]

      A dictionary containing the keyword arguments and corresponding values to use
      when creating the operation by evaluating the factory function.


   .. py:attribute:: gate_info_factory_kwargs
      :type:  list[str] | None
      :value: None


      A list of keyword arguments of the factory function for which the value must
      be retrieved from the ``gate_info`` of the operation.


   .. py:method:: _serialize_factory_func(v: object) -> str | None


   .. py:method:: _import_factory_func_if_str(fun: str | collections.abc.Callable[Ellipsis, qblox_scheduler.operations.operation.Operation]) -> collections.abc.Callable[Ellipsis, qblox_scheduler.operations.operation.Operation]
      :classmethod:



.. py:class:: DeviceCompilationConfig(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Information required to compile a schedule to the quantum-device layer.

   From a point of view of :ref:`sec-compilation` this information is needed
   to convert a schedule defined on a quantum-circuit layer to a schedule
   defined on a quantum-device layer.

   .. admonition:: Examples
       :class: dropdown

       The DeviceCompilationConfig is structured such that it should allow the
       specification of the circuit-to-device compilation for many different qubit
       platforms.
       Here we show a basic configuration for a two-transmon quantum device.
       In this example, the DeviceCompilationConfig is created by parsing a dictionary
       containing the relevant information.

       .. important::

           Although it is possible to manually create a configuration using
           dictionaries, this is not recommended. The
           :class:`~qblox_scheduler.device_under_test.quantum_device.QuantumDevice`
           is responsible for managing and generating configuration files.

       .. jupyter-execute::

           import pprint
           from qblox_scheduler.backends.graph_compilation import (
               DeviceCompilationConfig
           )
           from qblox_scheduler.schemas.examples.device_example_cfgs import (
               example_transmon_cfg
           )

           pprint.pprint(example_transmon_cfg)


       The dictionary can be parsed using the :code:`model_validate` method.

       .. jupyter-execute::

           device_cfg = DeviceCompilationConfig.model_validate(example_transmon_cfg)
           device_cfg


   .. py:attribute:: clocks
      :type:  dict[str, float]

      A dictionary specifying the clock frequencies available on the device e.g.,
      :code:`{"q0.01": 6.123e9}`.


   .. py:attribute:: elements
      :type:  dict[str, dict[str, OperationCompilationConfig]]

      A dictionary specifying the elements on the device, what operations can be
      applied to them and how to compile these.


   .. py:attribute:: edges
      :type:  dict[str, dict[str, OperationCompilationConfig]]

      A dictionary specifying the edges, links between elements on the device to which
      operations can be applied, and the operations that can be applied to them and how
      to compile these.


   .. py:attribute:: scheduling_strategy
      :type:  qblox_scheduler.enums.SchedulingStrategy

      The scheduling strategy used when determining the absolute timing of each
      operation of the schedule.


   .. py:attribute:: compilation_passes
      :type:  list[SimpleNodeConfig]
      :value: None


      The list of compilation nodes that should be called in succession to compile a
      schedule to the quantum-device layer.


.. py:class:: CompilationConfig(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`


   Base class for a compilation config.

   Subclassing is generally required to create useful compilation configs, here extra
   fields can be defined.


   .. py:attribute:: name
      :type:  str

      The name of the compiler.


   .. py:attribute:: version
      :type:  str
      :value: 'v0.6'


      The version of the ``CompilationConfig`` to facilitate backwards compatibility.


   .. py:attribute:: keep_original_schedule
      :type:  bool
      :value: True


      If ``True``, the compiler will not modify the schedule argument.
      If ``False``, the compilation modifies the schedule, thereby
      making the original schedule unusable for further usage; this
      improves compilation time. Warning: if ``False``, the returned schedule
      references objects from the original schedule, please refrain from modifying
      the original schedule after compilation in this case!


   .. py:attribute:: backend
      :type:  type[ScheduleCompiler]

      A reference string to the :class:`~ScheduleCompiler` class used in the compilation.


   .. py:attribute:: device_compilation_config
      :type:  DeviceCompilationConfig | None
      :value: None


      The :class:`~DeviceCompilationConfig` used in the compilation from the quantum-circuit
      layer to the quantum-device layer.


   .. py:attribute:: hardware_compilation_config
      :type:  ConcreteHardwareCompilationConfig | None
      :value: None


      The ``HardwareCompilationConfig`` used in the compilation from the quantum-device
      layer to the control-hardware layer.


   .. py:attribute:: debug_mode
      :type:  bool
      :value: False


      Debug mode can modify the compilation process,
      so that debugging of the compilation process is easier.


   .. py:method:: _serialize_backend_func(v: object) -> str


   .. py:method:: _import_backend_if_str(class_: type[ScheduleCompiler] | str) -> type[ScheduleCompiler]
      :classmethod:



.. py:class:: CompilationNode(name: str)

   A node representing a compiler pass.

   .. note::

       To compile, the :meth:`~.CompilationNode.compile` method should be used.

   :param name: The name of the node. Should be unique if it is added to a (larger)
                compilation
                graph.


   .. py:attribute:: name


   .. py:method:: _compilation_func(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.structure.model.DataStructure, config: qblox_scheduler.structure.model.DataStructure) -> qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.structure.model.DataStructure
      :abstractmethod:


      Private compilation method of this CompilationNode.

      It should be completely stateless whenever inheriting from the CompilationNode,
      this is the object that should be modified.



   .. py:method:: compile(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.structure.model.DataStructure, config: qblox_scheduler.structure.model.DataStructure) -> qblox_scheduler.schedules.schedule.TimeableSchedule | qblox_scheduler.structure.model.DataStructure

      Execute a compilation pass.

      This method takes a :class:`~.TimeableSchedule` and returns a new (updated)
      :class:`~.TimeableSchedule` using the information provided in the config.



.. py:class:: SimpleNode(name: str, compilation_func: collections.abc.Callable)

   Bases: :py:obj:`CompilationNode`


   A node representing a single compilation pass.

   .. note::

       To compile, the :meth:`~.CompilationNode.compile` method should be used.

   :param name: The name of the node. Should be unique if it is added to a (larger)
                compilation graph.
   :param compilation_func: A Callable that will be wrapped in this object. A compilation function
                            should take the intermediate representation (commonly :class:`~.TimeableSchedule`)
                            and a config as inputs and returns a new (modified) intermediate
                            representation.


   .. py:attribute:: compilation_func


   .. py:method:: _compilation_func(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, config: qblox_scheduler.structure.model.DataStructure | dict) -> qblox_scheduler.schedules.schedule.TimeableSchedule

      Private compilation method of this CompilationNode.

      It should be completely stateless whenever inheriting from the CompilationNode,
      this is the object that should be modified.



.. py:class:: ScheduleCompiler(name: str = 'compiler', quantum_device: qblox_scheduler.device_under_test.quantum_device.QuantumDevice | None = None)

   Bases: :py:obj:`CompilationNode`


   A compiler for qblox-scheduler :class:`~.TimeableSchedule` s.

   The compiler defines a directed acyclic graph containing
   :class:`~.CompilationNode` s. In this graph, nodes represent
   modular compilation passes.

   :param name: name of the compiler instance, by default "compiler"
   :param quantum_device: quantum_device from which a :class:`~.CompilationConfig` will be generated
                          if None is provided for the compile step


   .. py:attribute:: _task_graph
      :type:  networkx.DiGraph
      :value: None



   .. py:attribute:: _input_node
      :value: None



   .. py:attribute:: _output_node
      :value: None



   .. py:attribute:: quantum_device
      :value: None



   .. py:method:: compile(schedule: qblox_scheduler.schedule.Schedule | qblox_scheduler.schedules.schedule.TimeableSchedule, config: CompilationConfig | None = None) -> qblox_scheduler.schedules.schedule.CompiledSchedule

      Compile a :class:`~.TimeableSchedule` using the information provided in the config.

      :param schedule: the schedule to compile.
      :param config: describing the information required to compile the schedule.
                     If not specified, self.quantum_device will be used to generate
                     the config.

      :returns: CompiledSchedule:
                    a compiled schedule containing the compiled instructions suitable
                    for execution on a (hardware) backend.




   .. py:property:: input_node
      :type: SimpleNode


      Node designated as the default input for compilation.

      If not specified will return None.


   .. py:property:: output_node
      :type: SimpleNode | None


      Node designated as the default output for compilation.

      If not specified will return None.


   .. py:method:: construct_graph(config: CompilationConfig) -> NoReturn
      :abstractmethod:


      Construct the compilation graph based on a provided config.



   .. py:method:: draw(ax: matplotlib.axes.Axes = None, figsize: tuple[float, float] = (20, 10), **options) -> matplotlib.axes.Axes

      Draws the graph defined by this backend using matplotlib.

      Will attempt to position the nodes using the "dot" algorithm for directed
      acyclic graphs from graphviz if available.
      See https://pygraphviz.github.io/documentation/stable/install.html for
      installation instructions of pygraphviz and graphviz.

      If not available will use the Kamada Kawai positioning algorithm.


      :param ax: Matplotlib axis to plot the figure on
      :param figsize: Optional figure size, defaults to something slightly larger that fits the
                      size of the nodes.
      :param options: optional keyword arguments that are passed to
                      :code:`networkx.draw_networkx`.



.. py:class:: SerialCompiler(name: str = 'compiler', quantum_device: qblox_scheduler.device_under_test.quantum_device.QuantumDevice | None = None)

   Bases: :py:obj:`ScheduleCompiler`


   A compiler that executes compilation passes sequentially.


   .. py:method:: construct_graph(config: SerialCompilationConfig) -> None

      Construct the compilation graph based on a provided config.

      For a serial backend, it is just a list of compilation passes.



   .. py:method:: _compilation_func(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, config: SerialCompilationConfig) -> qblox_scheduler.schedules.schedule.CompiledSchedule

      Compile a schedule using the backend and the information provided in the config.

      :param schedule: The schedule to compile.
      :param config: A dictionary containing the information needed to compile the schedule.
                     Nodes in this compiler specify what key they need information from in this
                     dictionary.



.. py:class:: SerialCompilationConfig(/, **data: Any)

   Bases: :py:obj:`CompilationConfig`


   A compilation config for a simple serial compiler.

   Specifies compilation as a list of compilation passes.


   .. py:attribute:: backend
      :type:  type[SerialCompiler]

      A reference string to the :class:`~ScheduleCompiler` class used in the compilation.


   .. py:method:: _serialize_backend_func(v: object) -> str


   .. py:method:: _import_backend_if_str(class_: type[SerialCompiler] | str) -> type[SerialCompiler]
      :classmethod:



