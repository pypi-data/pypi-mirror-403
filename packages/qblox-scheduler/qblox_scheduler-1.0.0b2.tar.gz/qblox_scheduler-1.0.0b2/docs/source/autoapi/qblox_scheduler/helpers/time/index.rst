time
====

.. py:module:: qblox_scheduler.helpers.time 

.. autoapi-nested-parse::

   Python time wrapper functions.

   These function help to make time dependent modules testable.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.helpers.time.get_time
   qblox_scheduler.helpers.time.sleep



.. py:function:: get_time() -> float

   Return the time in seconds since the epoch as a floating point number.

   Acts as a wrapper around :func:`time.time` in order to make it testable.
   Mocking time.time() can conflicts with the internal python ticker thread.

   :returns: :
                 Time since epoch



.. py:function:: sleep(seconds: float) -> None

   Delay execution for a given number of seconds.

   The argument may be a floating point
   number for subsecond precision.

   :param seconds: The amount of time to wait.


