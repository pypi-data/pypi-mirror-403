type_casting
============

.. py:module:: qblox_scheduler.backends.qblox.type_casting 

.. autoapi-nested-parse::

   Utility functions for type casting.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.type_casting._cast_amplitude_to_signed_int
   qblox_scheduler.backends.qblox.type_casting._cast_hz_to_signed_int
   qblox_scheduler.backends.qblox.type_casting._cast_deg_to_signed_int
   qblox_scheduler.backends.qblox.type_casting._get_safe_step_size
   qblox_scheduler.backends.qblox.type_casting.get_safe_step_size



Attributes
~~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.type_casting.SIGNED_INT_CASTING_FNS


.. py:function:: _cast_amplitude_to_signed_int(amplitude: float, bits: int = constants.REGISTER_SIZE_BITS) -> int

.. py:function:: _cast_hz_to_signed_int(value: float) -> int

.. py:function:: _cast_deg_to_signed_int(value: float) -> int

.. py:data:: SIGNED_INT_CASTING_FNS
   :type:  dict[qblox_scheduler.operations.expressions.DType, collections.abc.Callable[[float], int]]

.. py:function:: _get_safe_step_size(start: int, stop: int, num: int) -> int

.. py:function:: get_safe_step_size(domain: qblox_scheduler.operations.loop_domains.LinearDomain) -> int

   Get a step size that ensures the final value will not overflow in a sweep.

   :param domain: The domain to calculate a step size for.

   :returns: int
                 The step size as a signed integer.

   :raises ValueError: When the domain is complex.


