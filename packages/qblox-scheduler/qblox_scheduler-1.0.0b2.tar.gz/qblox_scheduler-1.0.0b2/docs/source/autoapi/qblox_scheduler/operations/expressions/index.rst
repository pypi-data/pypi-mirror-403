expressions
===========

.. py:module:: qblox_scheduler.operations.expressions 

.. autoapi-nested-parse::

   Classes that represent expressions, which produce a value when compiled and executed.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.expressions.DType
   qblox_scheduler.operations.expressions.Expression
   qblox_scheduler.operations.expressions.UnaryExpression
   qblox_scheduler.operations.expressions.BinaryExpression



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.expressions.substitute_value_in_arbitrary_container



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.expressions.ContainsExpressionType


.. py:class:: DType

   Bases: :py:obj:`qblox_scheduler.enums.StrEnum`


   Data type of a variable or expression.


   .. py:attribute:: NUMBER
      :value: 'number'


      A number, corresponding to 1, 2, 3, etc.


   .. py:attribute:: AMPLITUDE
      :value: 'amplitude'


      An amplitude, corresponding to 0.1, 0.2, 0.3, etc. in dimensionless units
      ranging from -1 to 1.


   .. py:attribute:: TIME
      :value: 'time'


      A time, corresponding to 20e-9, 40e-9, 60e-9, etc. in seconds.


   .. py:attribute:: FREQUENCY
      :value: 'frequency'


      A frequency, corresponding to 1e9, 2e9, 3e9, etc. in Hz.


   .. py:attribute:: PHASE
      :value: 'phase'


      A phase, corresponding to e.g. 0, 30, 60, 90, etc. in degrees ranging from 0 to 360.


   .. py:method:: is_timing_sensitive() -> bool

      Whether an expression of this type affects timing.



.. py:class:: Expression(dict=None, /, **kwargs)

   Bases: :py:obj:`collections.UserDict`, :py:obj:`abc.ABC`


   Expression that produces a value when compiled.


   .. py:property:: dtype
      :type: DType

      :abstractmethod:


      Data type of the expression.


   .. py:method:: substitute(substitutions: dict[Expression, Expression | int | float | complex]) -> Expression | int | float | complex
      :abstractmethod:


      Substitute matching parts of expression, possibly evaluating a result.



   .. py:method:: reduce() -> Expression | int | float | complex

      Reduce complex ASTs if they can be simplified due to the presence of constants.



.. py:class:: UnaryExpression(operator: str, operand: Expression)

   Bases: :py:obj:`Expression`


   An expression with one operand and one operator.

   :param operator: The operator that acts on the operand.
   :param operand: The expression or variable that is acted on.


   .. py:attribute:: EVALUATORS
      :type:  ClassVar[dict[str, collections.abc.Callable]]


   .. py:attribute:: _dtype


   .. py:property:: operator
      :type: str


      The operator that acts on the operand.


   .. py:property:: operand
      :type: Expression


      The expression or variable that is acted on.


   .. py:property:: dtype
      :type: DType


      Data type of this expression.


   .. py:method:: _update() -> None


   .. py:method:: substitute(substitutions: dict[Expression, Expression | int | float | complex]) -> Expression | int | float | complex

      Substitute matching operand, possibly evaluating a result.



   .. py:method:: reduce() -> Expression | int | float | complex

      Reduce complex ASTs if they can be simplified due to the presence of constants.

      Currently only handles a few cases (``a`` is a constant value in these examples):

      - ``-(-expr) -> expr``
      - ``+(expr * a) -> expr * a`` (same for ``/``)
      - ``-(expr * a) -> expr * (-a)`` (same for ``/``)

      :returns: Expression | int | float | complex
                    The simplified expression.




.. py:class:: BinaryExpression(lhs: Expression | complex, operator: str, rhs: Expression | complex)

   Bases: :py:obj:`Expression`


   An expression with two operands and one operator.

   :param lhs: The left-hand side of the expression.
   :param operator: The operator that acts on the operands.
   :param rhs: The right-hand side of the expression.


   .. py:attribute:: EVALUATORS
      :type:  ClassVar[dict[str, collections.abc.Callable]]


   .. py:property:: lhs
      :type: Expression


      The left-hand side of the expression.


   .. py:property:: operator
      :type: str


      The operator that acts on the operands.


   .. py:property:: rhs
      :type: Expression | complex


      The right-hand side of the expression.


   .. py:property:: dtype
      :type: DType


      Data type of this expression.


   .. py:method:: _update() -> None


   .. py:method:: substitute(substitutions: dict[Expression, Expression | int | float | complex]) -> Expression | int | float | complex

      Substitute matching operands, possibly evaluating a result.



   .. py:method:: reduce() -> Expression | int | float | complex

      Reduce complex ASTs if they can be simplified due to the presence of constants.

      Currently only handles a few cases (``a`` and ``b`` are constant values in these examples):

      - ``expr * 1 -> expr`` (same for ``/`` and ``//``)
      - ``expr + 0 -> expr`` (same for other applicable operators)
      - ``(expr * a) * b -> expr * (a * b)``
      - ``(expr * a) / b -> expr * (a / b)``
      - ``(expr / a) * b -> expr * (b / a)``
      - ``(expr / a) / b -> expr / (a * b)``
      - ``(-expr) * b -> expr * (-b)`` (same for ``/``)

      :returns: Expression | int | float | complex
                    The simplified expression.




.. py:data:: ContainsExpressionType

.. py:function:: substitute_value_in_arbitrary_container(val: ContainsExpressionType, substitutions: dict[Expression, Expression | int | float | complex]) -> tuple[Any, bool]

   Make the defined substitutions in the container type `val`.


