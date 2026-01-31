spin_edge
=========

.. py:module:: qblox_scheduler.device_under_test.spin_edge 

.. autoapi-nested-parse::

   The module provides classes related CZ operations.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.device_under_test.spin_edge.PortSpinEdge
   qblox_scheduler.device_under_test.spin_edge.SpinInit
   qblox_scheduler.device_under_test.spin_edge.CZ
   qblox_scheduler.device_under_test.spin_edge.CNOT
   qblox_scheduler.device_under_test.spin_edge.SpinEdge




.. py:class:: PortSpinEdge(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing the ports.


   .. py:attribute:: _parent
      :type:  SpinEdge | None
      :value: None



   .. py:attribute:: gate
      :type:  str
      :value: ''


      Name of the element's gate port.


   .. py:method:: _fill_defaults() -> None


.. py:class:: SpinInit(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing parameters for performing a SpinInit operation.


.. py:class:: CZ(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing parameters for performing a CZ operation.


   .. py:attribute:: square_amp
      :type:  float
      :value: None



   .. py:attribute:: square_duration
      :type:  float
      :value: None



   .. py:attribute:: parent_phase_correction
      :type:  float
      :value: None



   .. py:attribute:: child_phase_correction
      :type:  float
      :value: None



.. py:class:: CNOT(/, name, *, parent: SchedulerBaseModel | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.SchedulerSubmodule`


   Submodule containing parameters for performing a CNOT operation.


.. py:class:: SpinEdge(parent_element: qblox_scheduler.device_under_test.device_element.DeviceElement | str | None = None, child_element: qblox_scheduler.device_under_test.device_element.DeviceElement | str | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.device_under_test.edge.Edge`


   Spin edge implementation which connects two BasicSpinElements.

   This edge implements some operations between the two BasicSpinElements.


   .. py:attribute:: edge_type
      :type:  Literal['SpinEdge']
      :value: 'SpinEdge'



   .. py:attribute:: _parent_device_element
      :type:  qblox_scheduler.device_under_test.spin_element.BasicSpinElement | None
      :value: None



   .. py:attribute:: _child_device_element
      :type:  qblox_scheduler.device_under_test.spin_element.BasicSpinElement | None
      :value: None



   .. py:attribute:: spin_init
      :type:  SpinInit


   .. py:attribute:: cz
      :type:  CZ


   .. py:attribute:: cnot
      :type:  CNOT


   .. py:attribute:: ports
      :type:  PortSpinEdge


   .. py:method:: generate_edge_config() -> dict[str, dict[str, qblox_scheduler.backends.graph_compilation.OperationCompilationConfig]]

      Generate valid device config.

      Fills in the edges information to produce a valid device config for the
      qblox-scheduler making use of the
      :func:`~.circuit_to_device.compile_circuit_to_device_with_config_validation` function.



