resources
=========

.. py:module:: qblox_scheduler.resources 

.. autoapi-nested-parse::

   Common resources for use with the qblox_scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.resources.Resource
   qblox_scheduler.resources.ClockResource
   qblox_scheduler.resources.BasebandClockResource
   qblox_scheduler.resources.DigitalClockResource




.. py:class:: Resource(name: str)

   Bases: :py:obj:`collections.UserDict`


   A resource corresponds to a physical resource such as a port or a clock.

   :param name: The resource name.


   .. py:property:: name
      :type: str


      Returns the name of the Resource.

      :returns: :


   .. py:property:: hash
      :type: str


      A hash based on the contents of the Operation.


.. py:class:: ClockResource(name: str, freq: float, phase: float = 0)

   Bases: :py:obj:`Resource`


   The ClockResource corresponds to a physical clock used to modulate pulses.

   :param name: the name of this clock
   :param freq: the frequency of the clock in Hz
   :param phase: the starting phase of the clock in deg


   .. py:attribute:: data


.. py:class:: BasebandClockResource(name: str)

   Bases: :py:obj:`Resource`


   Global identity for a virtual baseband clock.

   Baseband signals are assumed to be real-valued and will not be modulated.

   :param name: the name of this clock


   .. py:attribute:: IDENTITY
      :value: 'cl0.baseband'



   .. py:attribute:: data


.. py:class:: DigitalClockResource(name: str)

   Bases: :py:obj:`Resource`


   Global identity for a virtual digital clock.

   Digital clocks can only be associated with digital channels.

   :param name: the name of this clock


   .. py:attribute:: IDENTITY
      :value: 'digital'



   .. py:attribute:: data


