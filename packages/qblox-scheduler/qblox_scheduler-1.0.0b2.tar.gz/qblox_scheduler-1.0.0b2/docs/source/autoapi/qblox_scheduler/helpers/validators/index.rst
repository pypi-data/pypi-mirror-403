validators
==========

.. py:module:: qblox_scheduler.helpers.validators 

.. autoapi-nested-parse::

   Module containing pydantic validators.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.helpers.validators.Numbers
   qblox_scheduler.helpers.validators._Durations
   qblox_scheduler.helpers.validators._Amplitudes
   qblox_scheduler.helpers.validators._NonNegativeFrequencies
   qblox_scheduler.helpers.validators._Delays
   qblox_scheduler.helpers.validators._Hashable




.. py:class:: Numbers(min_value: qcodes.validators.validators.numbertypes = -np.inf, max_value: qcodes.validators.validators.numbertypes = np.inf, allow_nan: bool = False)

   Bases: :py:obj:`qcodes.utils.validators.Numbers`


   A custom qcodes Numbers validator that allows for nan values.

   Requires a number  of type int, float, numpy.integer or numpy.floating.

   :param min_value: Minimal value allowed, default -inf.
   :param max_value: Maximal value allowed, default inf.
   :param allow_nan: if nan values are allowed, default False.

   :raises TypeError: If min or max value not a number. Or if min_value is: larger than the max_value.


   .. py:attribute:: _allow_nan
      :value: False



   .. py:method:: validate(value: qcodes.validators.validators.numbertypes, context: str = '') -> None

      Validate if number else raises error.

      :param value: A number.
      :param context: Context for validation.

      :raises TypeError: If not int or float.:
      :raises ValueError: If number is not between the min and the max value.:



.. py:class:: _Durations

   Bases: :py:obj:`Numbers`


   Validator used for durations. It allows all numbers greater than or equal to 0.


.. py:class:: _Amplitudes

   Bases: :py:obj:`Numbers`


   Validator used for amplitudes. It allows all numbers and nan.


.. py:class:: _NonNegativeFrequencies

   Bases: :py:obj:`Numbers`


   Validator used for frequencies. It allows positive numbers and nan.


.. py:class:: _Delays

   Bases: :py:obj:`Numbers`


   Validator used for delays. It allows all numbers.


.. py:class:: _Hashable

   Bases: :py:obj:`qcodes.utils.validators.Validator`\ [\ :py:obj:`collections.abc.Hashable`\ ]


   Validator used for hashables.


   .. py:attribute:: _valid_values
      :value: (0, 'str')



   .. py:method:: validate(value: collections.abc.Hashable, context: str = '') -> None

      Validates if hashable else raises error.

      :param value: Value to validate
      :param context: Context for validation.

      :raises TypeError: If value is not hashable.



