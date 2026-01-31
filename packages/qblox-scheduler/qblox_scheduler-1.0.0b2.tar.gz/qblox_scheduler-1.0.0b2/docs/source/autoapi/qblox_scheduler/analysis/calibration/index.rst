calibration
===========

.. py:module:: qblox_scheduler.analysis.calibration 

.. autoapi-nested-parse::

   Module containing analysis utilities for calibration procedures.

   In particular, manipulation of data and calibration points for qubit readout
   calibration.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.calibration.rotate_to_calibrated_axis
   qblox_scheduler.analysis.calibration.has_calibration_points



.. py:function:: rotate_to_calibrated_axis(data: numpy.ndarray, ref_val_0: complex, ref_val_1: complex) -> numpy.ndarray

   Rotates, normalizes and offsets complex valued data based on calibration points.

   :param data: An array of complex valued data points.
   :param ref_val_0: The reference value corresponding to the 0 state.
   :param ref_val_1: The reference value corresponding to the 1 state.

   :returns: :
                 Calibrated array of complex data points.



.. py:function:: has_calibration_points(s21: numpy.ndarray, indices_state_0: tuple = (-2, ), indices_state_1: tuple = (-1, )) -> bool

   Determine if dataset with S21 data has calibration points for 0 and 1 states.

   Three pieces of information are used to infer the presence of calibration points:

   - The angle of the calibration points with respect to the average of the datapoints,
   - The distance between the calibration points, and
   - The average distance to the line defined be the calibration points.

   The detection is made robust by averaging 3 datapoints for each extremity of
   the "segment" described by the data on the IQ-plane.

   .. seealso:: :ref:`howto-analysis-has-calibration-points`

   :param s21: Array of complex datapoints corresponding to the experiment on the IQ plane.
   :param indices_state_0: Indices in the ``s21`` array that correspond to the ground state.
   :param indices_state_1: Indices in the ``s21`` array that correspond to the first excited state.

   :returns: :
                 The inferred presence of calibration points.



