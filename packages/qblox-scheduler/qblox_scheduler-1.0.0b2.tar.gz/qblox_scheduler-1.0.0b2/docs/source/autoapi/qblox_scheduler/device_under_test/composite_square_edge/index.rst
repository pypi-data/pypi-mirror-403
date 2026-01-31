composite_square_edge
=====================

.. py:module:: qblox_scheduler.device_under_test.composite_square_edge 

.. autoapi-nested-parse::

   The module provides classes related CZ operations.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.device_under_test.composite_square_edge.CZ
   qblox_scheduler.device_under_test.composite_square_edge.CompositeSquareEdge




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



.. py:class:: CompositeSquareEdge(parent_element: qblox_scheduler.device_under_test.device_element.DeviceElement | str | None = None, child_element: qblox_scheduler.device_under_test.device_element.DeviceElement | str | None = None, **data: Any)

   Bases: :py:obj:`qblox_scheduler.device_under_test.edge.Edge`


   An example Edge implementation which connects two BasicTransmonElements.

   This edge implements a square flux pulse and two virtual z
   phase corrections for the CZ operation between the two BasicTransmonElements.


   .. py:attribute:: edge_type
      :type:  Literal['CompositeSquareEdge']
      :value: 'CompositeSquareEdge'



   .. py:attribute:: _parent_device_element
      :type:  qblox_scheduler.device_under_test.transmon_element.BasicTransmonElement | None
      :value: None



   .. py:attribute:: _child_device_element
      :type:  qblox_scheduler.device_under_test.transmon_element.BasicTransmonElement | None
      :value: None



   .. py:attribute:: cz
      :type:  CZ


   .. py:method:: generate_edge_config() -> dict[str, dict[str, qblox_scheduler.backends.graph_compilation.OperationCompilationConfig]]

      Generate valid device config.

      Fills in the edges information to produce a valid device config for the
      qblox-scheduler making use of the
      :func:`~.circuit_to_device.compile_circuit_to_device_with_config_validation` function.



