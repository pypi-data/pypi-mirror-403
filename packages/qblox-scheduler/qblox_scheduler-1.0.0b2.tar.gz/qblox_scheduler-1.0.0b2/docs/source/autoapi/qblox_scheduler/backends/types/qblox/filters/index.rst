filters
=======

.. py:module:: qblox_scheduler.backends.types.qblox.filters 

.. autoapi-nested-parse::

   Python dataclasses for compilation to Qblox hardware.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.types.qblox.filters.QbloxRealTimeFilter




.. py:class:: QbloxRealTimeFilter

   Bases: :py:obj:`dataclasses_json.DataClassJsonMixin`


   An individual real time filter on Qblox hardware.


   .. py:attribute:: coeffs
      :type:  Optional[Union[float, list[float]]]
      :value: None


      Coefficient(s) of the filter.
      Can be None if there is no filter
      or if it is inactive.


   .. py:attribute:: config
      :type:  qblox_scheduler.backends.qblox.enums.FilterConfig

      Configuration of the filter.
      One of 'BYPASSED', 'ENABLED',
      or 'DELAY_COMP'.


   .. py:attribute:: marker_delay
      :type:  qblox_scheduler.backends.qblox.enums.FilterMarkerDelay

      State of the marker delay.
      One of 'BYPASSED' or 'ENABLED'.


