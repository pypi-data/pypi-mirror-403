"""
Private module containing visualization tools. To integrate a function
from this module into the API, create a new method in the :class:`.TimeableScheduleBase` class
that serves as an alias for calling this function.

.. admonition:: Example
    :class: tip

    The function :py:func:`.circuit_diagram.circuit_diagram_matplotlib`
    is called through its alias :py:meth:`.TimeableScheduleBase.plot_circuit_diagram`
"""
