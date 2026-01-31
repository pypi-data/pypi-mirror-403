register_manager
================

.. py:module:: qblox_scheduler.backends.qblox.register_manager 

.. autoapi-nested-parse::

   Utility class for dynamically allocating registers for Qblox sequencers.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.register_manager.RegisterManager



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.register_manager._verify_valid_register



.. py:class:: RegisterManager

   Utility class that keeps track of all the registers that are still available.


   .. py:attribute:: _available_registers
      :type:  list[str]


   .. py:attribute:: _variable_mapping
      :type:  dict[qblox_scheduler.operations.variables.Variable, str]


   .. py:method:: allocate_register() -> str

      Allocates a register to be used within the q1asm program.

      :returns: :
                    A register that can be used.

      :raises IndexError: When the RegisterManager runs out of registers to allocate.



   .. py:method:: allocate_register_for_variable(variable: qblox_scheduler.operations.variables.Variable) -> str

      Allocate one or two registers for a variable.

      :param variable: The variable to which the register(s) are linked.

      :returns: str
                    The allocated register(s).




   .. py:method:: free_register_of_variable(variable: qblox_scheduler.operations.variables.Variable) -> None

      Mark the register associated with the variable ready for re-use.

      :param variable: The variable that is no longer needed.



   .. py:method:: free_register(register: str) -> None

      Frees up a register to be reused.

      :param register: The register to free up.

      :raises ValueError: The value provided is not a valid register.
      :raises RuntimeError: Attempting to free a register that is already free.



   .. py:property:: available_registers
      :type: list[str]


      Getter for the available registers.

      :returns: :
                    A copy of the list containing all the available registers.


   .. py:method:: get_register_of_variable(variable: qblox_scheduler.operations.variables.Variable) -> str

      Get the register(s) associated with the variable.

      :param variable: The variable.

      :returns: str
                    The registers.




.. py:function:: _verify_valid_register(register_name: str) -> None

   Verifies whether the passed name is a valid register name.

   Raises on any of the conditions:

   1. ``register_name`` does not start with "R" or
   2. ``register_name`` does not have an integer next
   3. the integer is higher than the number of registers in the sequence processor
   4. the integer is negative valued

   :param register_name: The register to verify.

   :raises ValueError: Invalid register name passed.


