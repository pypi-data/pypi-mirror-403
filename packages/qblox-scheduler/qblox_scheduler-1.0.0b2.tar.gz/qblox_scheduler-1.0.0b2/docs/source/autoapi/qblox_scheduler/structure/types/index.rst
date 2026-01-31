types
=====

.. py:module:: qblox_scheduler.structure.types 

.. autoapi-nested-parse::

   Types that support validation in Pydantic.

   Pydantic recognizes magic method ``__get_validators__`` to receive additional
   validators, that can be used, i.e., for custom serialization and deserialization.
   We implement several custom types here to tune behavior of our models.

   See `Pydantic documentation`_ for more information about implementing new types.

   .. _Pydantic documentation: https://docs.pydantic.dev/latest/usage/types/custom/



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.structure.types.Graph




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.structure.types.Amplitude
   qblox_scheduler.structure.types.Delay
   qblox_scheduler.structure.types.Duration
   qblox_scheduler.structure.types.Frequency
   qblox_scheduler.structure.types.NDArray


.. py:data:: Amplitude

   Type alias for a float that can be NaN.

.. py:data:: Delay

   Type alias for a float that can't be NaN.

.. py:data:: Duration

   Type alias for a float that must be >= 0 and not NaN.

.. py:data:: Frequency

   Type alias for a float that must be >= 0 but can be NaN.

.. py:data:: NDArray

.. py:class:: Graph(incoming_graph_data=None, **attr)

   Bases: :py:obj:`networkx.Graph`


   Pydantic-compatible version of :class:`networkx.Graph`.


   .. py:method:: validate(v: Any) -> Graph
      :classmethod:


      Validate the data and cast from all known representations.



