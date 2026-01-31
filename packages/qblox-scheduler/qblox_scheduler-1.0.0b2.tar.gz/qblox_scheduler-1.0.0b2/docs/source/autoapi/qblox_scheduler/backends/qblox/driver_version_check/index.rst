driver_version_check
====================

.. py:module:: qblox_scheduler.backends.qblox.driver_version_check 

.. autoapi-nested-parse::

   Helper functions to perform the version check for qblox_instruments.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.driver_version_check.verify_qblox_instruments_version



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.driver_version_check.logger
   qblox_scheduler.backends.qblox.driver_version_check.driver_version
   qblox_scheduler.backends.qblox.driver_version_check.SUPPORTED_DRIVER_VERSIONS
   qblox_scheduler.backends.qblox.driver_version_check.raise_on_version_mismatch


.. py:data:: logger

.. py:data:: driver_version
   :value: None


.. py:data:: SUPPORTED_DRIVER_VERSIONS

   Tuple containing all the version supported by this version of the backend.

.. py:data:: raise_on_version_mismatch
   :type:  bool
   :value: True


   Can be set to false to override version check.

.. py:exception:: DriverVersionError

   Bases: :py:obj:`Exception`


   Raise when the installed driver version is not supported.


.. py:function:: verify_qblox_instruments_version(version: str | None = driver_version, match_versions: packaging.requirements.Requirement = SUPPORTED_DRIVER_VERSIONS) -> None

   Verifies whether the installed version is supported by the qblox_backend.

   :param version: The Qblox driver versions (``qblox-instruments`` python package).
   :param match_versions: A tuple of version strings (can be `major`, `major.minor`, and/or `major.minor.patch`).

   :raises DriverVersionError: When an incorrect or no installation of qblox-instruments was found.


