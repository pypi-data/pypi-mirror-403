deprecation
===========

.. py:module:: qblox_scheduler.helpers.deprecation 

.. autoapi-nested-parse::

   Helper functions for code deprecation.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.helpers.deprecation.deprecated_arg_alias
   qblox_scheduler.helpers.deprecation._rename_kwargs



.. py:function:: deprecated_arg_alias(depr_version: str, **aliases: str) -> collections.abc.Callable

   Decorator for deprecated function and method arguments.

   From: https://stackoverflow.com/questions/49802412/how-to-implement-deprecation-in-python-with-argument-alias/49802489#49802489

   Use as follows:

   .. code-block:: python

       @deprecated_arg_alias("0.x.0", old_arg="new_arg")
       def myfunc(new_arg):
           ...

   :param depr_version: The qblox-scheduler version in which the parameter names will be removed.
   :param aliases: Parameter name aliases provided as ``old="new"``.

   :returns: :
                 The same function or method, that raises a FutureWarning if a deprecated
                 argument is passed, or a TypeError if both the new and the deprecated arguments
                 are passed.



.. py:function:: _rename_kwargs(func_name: str, depr_version: str, kwargs: dict[str, Any], aliases: dict[str, str]) -> None

   Helper function for deprecating function arguments.


