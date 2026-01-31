inspect
=======

.. py:module:: qblox_scheduler.helpers.inspect 

.. autoapi-nested-parse::

   Python inspect helper functions.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.helpers.inspect.get_classes
   qblox_scheduler.helpers.inspect.make_uml_diagram



.. py:function:: get_classes(*modules: types.ModuleType) -> dict[str, type[Any]]

   Return a dictionary of class names by class types.

   .. code-block::

       from qblox_scheduler.helpers import inspect
       from my_module import foo

       class_dict: dict[str, type] = inspect.get_classes(foo)
       print(class_dict)
       // { 'Bar': my_module.foo.Bar }

   :param modules: Variable length of modules.

   :returns: :
                 A dictionary containing the class names by class reference.



.. py:function:: make_uml_diagram(obj_to_plot: types.ModuleType | type[Any], options: list[str]) -> str | None

   Generate a UML diagram of a given module or class.

   This function is a wrapper of `pylint.pyreverse`.

   :param obj_to_plot: The module or class to visualize
   :param options: A string containing the plotting options for pyreverse

   :returns: :
                 The name of the generated ``png`` image



