types
=====

.. py:module:: qblox_scheduler.analysis.types 

.. autoapi-nested-parse::

   Module containing the types for use with the analysis classes.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.types.AnalysisSettings




.. py:class:: AnalysisSettings(settings: dict = None)

   Bases: :py:obj:`collections.UserDict`


   Analysis settings with built-in schema validations.

   .. jsonschema:: ../../../../../../src/qblox_scheduler/analysis/schemas/analysis_settings.json#/configurations


   .. py:attribute:: schema


   .. py:attribute:: schema_individual
      :type:  ClassVar[dict[str, Any]]


