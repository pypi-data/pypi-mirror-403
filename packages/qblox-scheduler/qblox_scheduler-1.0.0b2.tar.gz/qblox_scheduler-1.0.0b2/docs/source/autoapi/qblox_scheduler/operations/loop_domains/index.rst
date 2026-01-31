loop_domains
============

.. py:module:: qblox_scheduler.operations.loop_domains 

.. autoapi-nested-parse::

   Domains to loop over with ``Schedule.loop``.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.loop_domains.Domain
   qblox_scheduler.operations.loop_domains.LinearDomain



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.loop_domains.linspace
   qblox_scheduler.operations.loop_domains.arange



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.loop_domains.T


.. py:data:: T

.. py:class:: Domain(/, **data: Any)

   Bases: :py:obj:`qblox_scheduler.structure.model.DataStructure`, :py:obj:`abc.ABC`, :py:obj:`Generic`\ [\ :py:obj:`T`\ ]


   An object representing a range of values to loop over.


   .. py:attribute:: dtype
      :type:  qblox_scheduler.operations.expressions.DType

      Data type of the linear domain.


   .. py:method:: values() -> collections.abc.Iterator[T]
      :abstractmethod:


      Return iterator over all values in this domain.



   .. py:property:: num_steps
      :type: int

      :abstractmethod:


      Return the number of steps in this domain.


.. py:class:: LinearDomain

   Bases: :py:obj:`Domain`\ [\ :py:obj:`Union`\ [\ :py:obj:`complex`\ , :py:obj:`float`\ ]\ ]


   Linear range of values to loop over, specified with a start value, an inclusive stop value and
   the number of linearly spaced points to generate.


   .. py:attribute:: start
      :type:  complex | float

      The starting value of the sequence.


   .. py:attribute:: stop
      :type:  complex | float

      The end value of the sequence.


   .. py:attribute:: num
      :type:  int

      Number of samples to generate. Must be non-negative.


   .. py:method:: values() -> collections.abc.Iterator[complex | float]

      Return iterator over all values in this domain.



   .. py:method:: _num_is_strictly_positive(num: int) -> int
      :classmethod:



   .. py:property:: num_steps
      :type: int


      The number of steps in this domain.


   .. py:property:: step_size
      :type: complex | float


      The step size of the range of values.


.. py:function:: linspace(start: complex | float, stop: complex | float, num: int, dtype: qblox_scheduler.operations.expressions.DType) -> LinearDomain

   Linear range of values to loop over, specified with a start value, an inclusive stop value and
   the number of linearly spaced points to generate.

   :param start: The starting value of the sequence.
   :param stop: The end value of the sequence.
   :param num: Number of samples to generate. Must be non-negative.
   :param dtype: Data type of the linear domain.


.. py:function:: arange(stop: float, dtype: qblox_scheduler.operations.expressions.DType) -> LinearDomain
                 arange(start: float, stop: float, dtype: qblox_scheduler.operations.expressions.DType) -> LinearDomain
                 arange(start: float, stop: float, step: float, dtype: qblox_scheduler.operations.expressions.DType) -> LinearDomain

   Linear range of values to loop over, specified with a start value, an exclusive stop value and a
   step size.

   :param start: Start of interval. The interval includes this value.
   :param stop: End of interval. The interval does not include this value, except in some cases where step
                is not an integer and floating point round-off affects the length of out.
   :param step: Spacing between values. For any output out, this is the distance between two adjacent
                values, out[i+1] - out[i].
   :param dtype: Data type of the linear domain.


