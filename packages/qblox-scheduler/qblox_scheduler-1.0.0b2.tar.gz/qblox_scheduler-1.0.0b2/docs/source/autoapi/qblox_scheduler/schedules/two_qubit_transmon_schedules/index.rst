two_qubit_transmon_schedules
============================

.. py:module:: qblox_scheduler.schedules.two_qubit_transmon_schedules 

.. autoapi-nested-parse::

   Module containing schedules for common two qubit experiments (transmon).



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.schedules.two_qubit_transmon_schedules.chevron_cz_sched



.. py:function:: chevron_cz_sched(lf_qubit: str, hf_qubit: str, amplitudes: float | numpy.ndarray, duration: float, flux_port: str | None = None, repetitions: int = 1) -> qblox_scheduler.schedules.schedule.TimeableSchedule

   Chevron CZ calibration schedule that measures coupling of a qubit pair.

   This experiment provides information about the location
   of the :math:`|11\rangle \leftrightarrow |02\rangle` avoided crossing and
   distortions in the flux-control line.

   .. admonition:: TimeableSchedule sequence
       :class: tip

       .. jupyter-execute::

               from qblox_scheduler.schedules.two_qubit_transmon_schedules import (
                   chevron_cz_sched
               )

               sched = chevron_cz_sched(
                   lf_qubit="q0",
                   hf_qubit="q1",
                   amplitudes=0.5,
                   duration=20e-9,
               )

               sched.plot_circuit_diagram();

   .. note::
       This schedule uses a unipolar square flux pulse, which will cause
       distortions and leakage. For a high quality CZ
       gate, distortions should be corrected for by modelling and
       subsequently inverting the transfer function of the
       flux-control line.
       See e.g. :cite:t:`Jerger2019` or :cite:t:`Rol2020`
       for more information.

   :param lf_qubit: The name of a qubit, e.g., "q0", the qubit with lower frequency.
   :param hf_qubit: The name of coupled qubit, the qubit with the higher frequency.
   :param amplitudes: An array (or scalar) of the flux pulse amplitude(s) in V.
   :param duration: A scalar specifying the flux pulse duration in s.
   :param flux_port: An optional string for a flux port. If ``None``, this will default to
                     the ``hf_qubit`` flux port (``"{hf_qubit}:fl"``).
   :param repetitions: The amount of times the TimeableSchedule will be repeated.

   :returns: :
                 An experiment schedule.



