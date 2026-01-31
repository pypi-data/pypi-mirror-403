yaml_utils
==========

.. py:module:: qblox_scheduler.yaml_utils 

.. autoapi-nested-parse::

   Module containing scheduler YAML utilities.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.yaml_utils.register_model
   qblox_scheduler.yaml_utils.register_legacy_instruments



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.yaml_utils.yaml


.. py:function:: register_model(cls: type[pydantic.BaseModel], yaml_obj: ruamel.yaml.YAML) -> None

   Register a Pydantic model to be serialized by `ruamel.yaml`, with a YAML tag corresponding
   to the name of the model class.

   The implementation mirrors the original :meth:`~ruamel.yaml.YAML.register_class`,
   but unlike that it doesn't use `to_yaml/from_yaml` on the target class,
   instead relying solely on `__getstate__` and `__setstate__`.


.. py:function:: register_legacy_instruments(yaml_obj: ruamel.yaml.YAML) -> None

   Register `MeasurementControl` and `InstrumentCoordinator` with the global YAML object
   to be de/serialized correctly.


.. py:data:: yaml

