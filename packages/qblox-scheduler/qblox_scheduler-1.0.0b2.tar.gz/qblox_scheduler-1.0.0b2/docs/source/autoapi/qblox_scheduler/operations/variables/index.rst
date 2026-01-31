variables
=========

.. py:module:: qblox_scheduler.operations.variables 

.. autoapi-nested-parse::

   Variable class and related operations for creating a variable, and dropping a variable
   when it goes out of scope.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.variables.Variable




.. py:class:: Variable(dtype: qblox_scheduler.operations.expressions.DType)

   Bases: :py:obj:`qblox_scheduler.operations.expressions.Expression`


   A variable, representing a location in memory.


   .. py:method:: substitute(substitutions: dict[qblox_scheduler.operations.expressions.Expression, qblox_scheduler.operations.expressions.Expression | int | float | complex]) -> qblox_scheduler.operations.expressions.Expression | int | float | complex

      Substitute matching variable.



   .. py:property:: dtype
      :type: qblox_scheduler.operations.expressions.DType


      Data type of this variable.


   .. py:method:: _update() -> None


   .. py:property:: id_
      :type: uuid.UUID


      The unique ID of this variable.


