_visualization
==============

.. py:module:: qblox_scheduler.schedules._visualization 

.. autoapi-nested-parse::

   Private module containing visualization tools. To integrate a function
   from this module into the API, create a new method in the :class:`.TimeableScheduleBase` class
   that serves as an alias for calling this function.

   .. admonition:: Example
       :class: tip

       The function :py:func:`.circuit_diagram.circuit_diagram_matplotlib`
       is called through its alias :py:meth:`.TimeableScheduleBase.plot_circuit_diagram`



Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   circuit_diagram/index.rst
   constants/index.rst
   pulse_diagram/index.rst
   pulse_scheme/index.rst


