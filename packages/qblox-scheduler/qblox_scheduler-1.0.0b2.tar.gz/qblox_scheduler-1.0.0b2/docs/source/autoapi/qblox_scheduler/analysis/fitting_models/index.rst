fitting_models
==============

.. py:module:: qblox_scheduler.analysis.fitting_models 

.. autoapi-nested-parse::

   Models and fit functions to be used with the lmfit fitting framework.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.fitting_models.LorentzianModel
   qblox_scheduler.analysis.fitting_models.CosineModel
   qblox_scheduler.analysis.fitting_models.ResonatorModel
   qblox_scheduler.analysis.fitting_models.ExpDecayModel
   qblox_scheduler.analysis.fitting_models.RabiModel
   qblox_scheduler.analysis.fitting_models.DecayOscillationModel



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.fitting_models.get_model_common_doc
   qblox_scheduler.analysis.fitting_models.get_guess_common_doc
   qblox_scheduler.analysis.fitting_models.mk_seealso
   qblox_scheduler.analysis.fitting_models.hanger_func_complex_SI
   qblox_scheduler.analysis.fitting_models.cos_func
   qblox_scheduler.analysis.fitting_models.lorentzian_func
   qblox_scheduler.analysis.fitting_models.exp_decay_func
   qblox_scheduler.analysis.fitting_models.exp_damp_osc_func
   qblox_scheduler.analysis.fitting_models.resonator_phase_guess
   qblox_scheduler.analysis.fitting_models.fft_freq_phase_guess



.. py:function:: get_model_common_doc() -> str

   Returns a common docstring to be used with custom fitting
   :class:`~lmfit.model.Model` s.

   .. admonition:: Usage example for a custom fitting model
       :class: dropdown, tip

       See the usage example at the end of the :class:`~ResonatorModel` source-code:

       .. literalinclude:: ../../../../../../src/qblox_scheduler/analysis/fitting_models.py
           :pyobject: ResonatorModel


.. py:function:: get_guess_common_doc() -> str

   Returns a common docstring to be used for the :meth:`~lmfit.model.Model.guess`
   method of custom fitting :class:`~lmfit.model.Model` s.

   .. admonition:: Usage example for a custom fitting model
       :class: dropdown, tip

       See the usage example at the end of the :class:`~ResonatorModel` source-code:

       .. literalinclude:: ../../../../../../src/qblox_scheduler/analysis/fitting_models.py
           :pyobject: ResonatorModel


.. py:function:: mk_seealso(function_name: str, role: str = 'func', prefix: str = '\n\n', module_location: str = '.') -> str

   Returns a sphinx `seealso` pointing to a function.

   Intended to be used for building custom fitting model docstrings.

   .. admonition:: Usage example for a custom fitting model
       :class: dropdown, tip

       See the usage example at the end of the :class:`~ResonatorModel` source-code:

       .. literalinclude:: ../../../../../../src/qblox_scheduler/analysis/fitting_models.py
           :pyobject: ResonatorModel

   :param function_name: name of the function to point to
   :param role: a sphinx role, e.g. :code:`"func"`
   :param prefix: string preceding the `seealso`
   :param module_location: can be used to indicate a function outside this module, e.g.,
                           :code:`my_module.submodule` which contains the function.

   :returns: :
                 resulting string



.. py:function:: hanger_func_complex_SI(f: float, fr: float, Ql: float, Qe: float, A: float, theta: float, phi_v: float, phi_0: float, alpha: float = 1) -> complex

   This is the complex function for a hanger (lambda/4 resonator).

   :param f: frequency
   :param fr: resonance frequency
   :param A: background transmission amplitude
   :param Ql: loaded quality factor of the resonator
   :param Qe: magnitude of extrinsic quality factor :code:`Qe = |Q_extrinsic|`
   :param theta: phase of extrinsic quality factor (in rad)
   :param phi_v: phase to account for propagation delay to sample
   :param phi_0: phase to account for propagation delay from sample
   :param alpha: slope of signal around the resonance

   :returns: :
                 complex valued transmission


   See eq. S4 from Bruno et al. (2015)
   `ArXiv:1502.04082 <https://arxiv.org/abs/1502.04082>`_.

   .. math::

       S_{21} = A \left(1+\alpha \frac{f-f_r}{f_r} \right)
       \left(1- \frac{\frac{Q_l}{|Q_e|}e^{i\theta} }{1+2iQ_l \frac{f-f_r}{f_r}} \right)
       e^{i (\phi_v f + \phi_0)}

   The loaded and extrinsic quality factors are related to the internal and coupled Q
   according to:

   .. math::

       \frac{1}{Q_l} = \frac{1}{Q_c}+\frac{1}{Q_i}

   and

   .. math::

       \frac{1}{Q_c} = \mathrm{Re}\left(\frac{1}{|Q_e|e^{-i\theta}}\right)



.. py:function:: cos_func(x: float, frequency: float, amplitude: float, offset: float, phase: float = 0) -> float

   An oscillating cosine function:

   :math:`y = \mathrm{amplitude} \times \cos(2 \pi \times \mathrm{frequency} \times x + \mathrm{phase}) +  \mathrm{offset}`

   :param x: The independent variable (time, for example)
   :param frequency: A generalized frequency (in units of inverse x)
   :param amplitude: Amplitude of the oscillation
   :param offset: Output signal vertical offset
   :param phase: Phase offset / rad

   :returns: :
                 Output signal magnitude



.. py:function:: lorentzian_func(x: float, x0: float, width: float, a: float, c: float) -> float

   A Lorentzian function.

   .. math::

       y = \frac{a*\mathrm{width}}{\pi(\mathrm{width}^2 + (x - x_0)^2)} + c

   :param x: independent variable
   :param x0: horizontal offset
   :param width: Lorenztian linewidth
   :param a: amplitude
   :param c: vertical offset

   :returns: :
                 Lorentzian function



.. py:function:: exp_decay_func(t: float, tau: float, amplitude: float, offset: float, n_factor: float) -> float

   This is a general exponential decay function:

   :math:`y = \mathrm{amplitude} \times \exp\left(-(t/\tau)^\mathrm{n\_factor}\right) + \mathrm{offset}`

   :param t: time
   :param tau: decay time
   :param amplitude: amplitude of the exponential decay
   :param offset: asymptote of the exponential decay, the value at t=infinity
   :param n_factor: exponential decay factor

   :returns: :
                 Output of exponential function as a float



.. py:function:: exp_damp_osc_func(t: float, tau: float, n_factor: float, frequency: float, phase: float, amplitude: float, offset: float)

   A sinusoidal oscillation with an exponentially decaying envelope function:

   :math:`y = \mathrm{amplitude} \times \exp\left(-(t/\tau)^\mathrm{n\_factor}\right)(\cos(2\pi\mathrm{frequency}\times t + \mathrm{phase}) + \mathrm{oscillation_offset}) + \mathrm{exponential_offset}`

   :param t: time
   :param tau: decay time
   :param n_factor: exponential decay factor
   :param frequency: frequency of the oscillation
   :param phase: phase of the oscillation
   :param amplitude: initial amplitude of the oscillation
   :param offset: Output signal vertical offset

   :returns: :
                 Output of decaying cosine function as a float



.. py:class:: LorentzianModel(*args, **kwargs)

   Bases: :py:obj:`lmfit.model.Model`


   Model for data which follows a Lorentzian function.

   Uses the function :func:`~lorentzian_func` as the
   defining equation.


   .. py:method:: guess(data: numpy.typing.NDArray, **kws) -> lmfit.parameter.Parameters

      Guess some initial values for the model based on the data.



.. py:class:: CosineModel(*args, **kwargs)

   Bases: :py:obj:`lmfit.model.Model`


   Exemplary lmfit model with a guess for a cosine.

   .. note::

       The :mod:`lmfit.models` module provides several fitting models that might fit
       your needs out of the box.


   .. py:method:: guess(data, x, **kws) -> lmfit.parameter.Parameters

      Guess parameters based on the data

      :param data: Data to fit to
      :type data: np.ndarray
      :param x: Independent variable
      :type x: np.ndarray



.. py:class:: ResonatorModel(*args, **kwargs)

   Bases: :py:obj:`lmfit.model.Model`


   Resonator model

   Implementation and design patterns inspired by the
   `complex resonator model example <https://lmfit.github.io/lmfit-py/examples/example_complex_resonator_model.html>`_
   (`lmfit` documentation).



   .. py:method:: guess(data, **kws) -> lmfit.parameter.Parameters

      Guess starting values for the parameters of a Model.

      This is not implemented for all models, but is available for many
      of the built-in models.

      :param data: Array of data (i.e., y-values) to use to guess parameter values.
      :type data: array_like
      :param x: Array of values for the independent variable (i.e., x-values).
      :type x: array_like
      :param \*\*kws: Additional keyword arguments, passed to model function.
      :type \*\*kws: optional

      :returns: Parameters
                    Initial, guessed values for the parameters of a Model.

      :raises NotImplementedError: If the `guess` method is not implemented for a Model.

      .. rubric:: Notes

      Should be implemented for each model subclass to run
      `self.make_params()`, update starting values and return a
      Parameters object.

      .. versionchanged:: 1.0.3
         Argument ``x`` is now explicitly required to estimate starting values.



.. py:class:: ExpDecayModel(*args, **kwargs)

   Bases: :py:obj:`lmfit.model.Model`


   Model for an exponential decay, such as a qubit T1 measurement.


   .. py:method:: guess(data, **kws) -> lmfit.parameter.Parameters

      Guess starting values for the parameters of a Model.

      This is not implemented for all models, but is available for many
      of the built-in models.

      :param data: Array of data (i.e., y-values) to use to guess parameter values.
      :type data: array_like
      :param x: Array of values for the independent variable (i.e., x-values).
      :type x: array_like
      :param \*\*kws: Additional keyword arguments, passed to model function.
      :type \*\*kws: optional

      :returns: Parameters
                    Initial, guessed values for the parameters of a Model.

      :raises NotImplementedError: If the `guess` method is not implemented for a Model.

      .. rubric:: Notes

      Should be implemented for each model subclass to run
      `self.make_params()`, update starting values and return a
      Parameters object.

      .. versionchanged:: 1.0.3
         Argument ``x`` is now explicitly required to estimate starting values.



.. py:class:: RabiModel(*args, **kwargs)

   Bases: :py:obj:`lmfit.model.Model`


   Model for a Rabi oscillation as a function of the microwave drive amplitude.
   Phase of oscillation is fixed at :math:`\pi` in order to ensure that the oscillation
   is at a minimum when the drive amplitude is 0.


   .. py:method:: guess(data, **kws) -> lmfit.parameter.Parameters

      Guess starting values for the parameters of a Model.

      This is not implemented for all models, but is available for many
      of the built-in models.

      :param data: Array of data (i.e., y-values) to use to guess parameter values.
      :type data: array_like
      :param x: Array of values for the independent variable (i.e., x-values).
      :type x: array_like
      :param \*\*kws: Additional keyword arguments, passed to model function.
      :type \*\*kws: optional

      :returns: Parameters
                    Initial, guessed values for the parameters of a Model.

      :raises NotImplementedError: If the `guess` method is not implemented for a Model.

      .. rubric:: Notes

      Should be implemented for each model subclass to run
      `self.make_params()`, update starting values and return a
      Parameters object.

      .. versionchanged:: 1.0.3
         Argument ``x`` is now explicitly required to estimate starting values.



.. py:class:: DecayOscillationModel(*args, **kwargs)

   Bases: :py:obj:`lmfit.model.Model`


   Model for a decaying oscillation which decays to a point with 0 offset from
   the centre of the oscillation (as in a Ramsey experiment, for example).


   .. py:method:: guess(data, **kws) -> lmfit.parameter.Parameters

      Guess starting values for the parameters of a Model.

      This is not implemented for all models, but is available for many
      of the built-in models.

      :param data: Array of data (i.e., y-values) to use to guess parameter values.
      :type data: array_like
      :param x: Array of values for the independent variable (i.e., x-values).
      :type x: array_like
      :param \*\*kws: Additional keyword arguments, passed to model function.
      :type \*\*kws: optional

      :returns: Parameters
                    Initial, guessed values for the parameters of a Model.

      :raises NotImplementedError: If the `guess` method is not implemented for a Model.

      .. rubric:: Notes

      Should be implemented for each model subclass to run
      `self.make_params()`, update starting values and return a
      Parameters object.

      .. versionchanged:: 1.0.3
         Argument ``x`` is now explicitly required to estimate starting values.



.. py:function:: resonator_phase_guess(s21: numpy.ndarray, freq: numpy.ndarray) -> tuple[float, float]

   Guesses the phase velocity in resonator spectroscopy,
   based on the median of all the differences between consecutive phases.

   :param s21: Resonator S21 data
   :param freq: Frequency of the spectroscopy pulse

   :returns: phi_0:
                 Guess for the phase offset
             phi_v:
                 Guess for the phase velocity



.. py:function:: fft_freq_phase_guess(data: numpy.ndarray, t: numpy.ndarray) -> tuple[float, float]

   Guess for a cosine fit using FFT, only works for evenly spaced points.

   :param data: Input data to FFT
   :param t: Independent variable (e.g. time)

   :returns: freq_guess:
                 Guess for the frequency of the cosine function
             ph_guess:
                 Guess for the phase of the cosine function



