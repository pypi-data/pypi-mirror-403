structure
=========

.. py:module:: qblox_scheduler.structure 

.. autoapi-nested-parse::

   Validated and serializable data structures using :mod:`pydantic`.

   In this module we provide :class:`pre-configured Pydantic model <.DataStructure>` and
   :mod:`custom field types <.types>` that allow serialization of typical data objects
   that we frequently use in ``qblox-scheduler``, like functions and arrays.



Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   model/index.rst
   types/index.rst


Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.structure.DataStructure
   qblox_scheduler.structure.Graph




Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.structure.NDArray


.. py:class:: DataStructure(/, **data: Any)

   Bases: :py:obj:`_SerializableBaseModel`


   A parent for all data structures.

   Data attributes are generated from the class' type annotations, similarly to
   `dataclasses <https://docs.python.org/3/library/dataclasses.html>`_. If data
   attributes are JSON-serializable, data structure can be serialized using
   ``json()`` method. This string can be deserialized using ``parse_raw()`` classmethod
   of a correspondent child class.

   If required, data fields can be validated, see examples for more information.
   It is also possible to define custom field types with advanced validation.

   This class is a pre-configured `pydantic <https://docs.pydantic.dev/>`_
   model. See its documentation for details of usage information.

   .. admonition:: Examples
       :class: dropdown

       .. include:: /examples/structure.DataStructure.rst


   .. py:attribute:: model_config

      Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].


.. py:class:: Graph(incoming_graph_data=None, **attr)

   Bases: :py:obj:`networkx.Graph`


   Pydantic-compatible version of :class:`networkx.Graph`.


   .. py:method:: validate(v: Any) -> Graph
      :classmethod:


      Validate the data and cast from all known representations.



.. py:data:: NDArray

