hardware
========

.. py:module:: qblox_scheduler.backends.types.qblox.hardware 

.. autoapi-nested-parse::

   Python dataclasses for compilation to Qblox hardware.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.qblox.hardware.QbloxBaseDescription
   qblox_scheduler.backends.types.qblox.hardware.ClusterDescription




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.qblox.hardware.QbloxHardwareDescription


.. py:class:: QbloxBaseDescription(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.backends.types.common.HardwareDescription`


   Base class for a Qblox hardware description.


   .. py:attribute:: ref
      :type:  Literal['internal', 'external']

      The reference source for the instrument.


   .. py:attribute:: sequence_to_file
      :type:  bool
      :value: False


      Write sequencer programs to files for (all modules in this) instrument.


.. py:class:: ClusterDescription(/, **data: Any)

   Bases: :py:obj:`QbloxBaseDescription`


   Information needed to specify a Cluster in the :class:`~.CompilationConfig`.


   .. py:attribute:: instrument_type
      :type:  Literal['Cluster']
      :value: 'Cluster'


      The instrument type, used to select this datastructure
      when parsing a :class:`~.CompilationConfig`.


   .. py:attribute:: modules
      :type:  dict[int, qblox_scheduler.backends.types.qblox.modules.ClusterModuleDescription]

      Description of the modules of this Cluster, using slot index as key.


   .. py:attribute:: ip
      :type:  Optional[str]
      :value: None


      Unique identifier (typically the ip address) used to connect to the cluster


   .. py:attribute:: sync_on_external_trigger
      :type:  Optional[qblox_scheduler.backends.types.qblox.settings.ExternalTriggerSyncSettings]
      :value: None


      Settings for synchronizing the cluster on an external trigger.


.. py:data:: QbloxHardwareDescription

   Specifies a piece of Qblox hardware and its instrument-specific settings.

