gate_library
============

.. py:module:: qblox_scheduler.operations.gate_library 

.. autoapi-nested-parse::

   Standard gateset for use with the qblox_scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.gate_library.Rxy
   qblox_scheduler.operations.gate_library.X
   qblox_scheduler.operations.gate_library.X90
   qblox_scheduler.operations.gate_library.Y
   qblox_scheduler.operations.gate_library.Y90
   qblox_scheduler.operations.gate_library.Rz
   qblox_scheduler.operations.gate_library.Z
   qblox_scheduler.operations.gate_library.Z90
   qblox_scheduler.operations.gate_library.S
   qblox_scheduler.operations.gate_library.SDagger
   qblox_scheduler.operations.gate_library.T
   qblox_scheduler.operations.gate_library.TDagger
   qblox_scheduler.operations.gate_library.H
   qblox_scheduler.operations.gate_library.CNOT
   qblox_scheduler.operations.gate_library.CZ
   qblox_scheduler.operations.gate_library.Reset
   qblox_scheduler.operations.gate_library.Measure



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.gate_library._modulo_360_with_mapping



.. py:class:: Rxy(theta: float, phi: float, qubit: str, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   A single qubit rotation around an axis in the equator of the Bloch sphere.

   This operation can be represented by the following unitary as defined in
   https://doi.org/10.1109/TQE.2020.2965810:

   .. math::

       \mathsf {R}_{xy} \left(\theta, \varphi\right) = \begin{bmatrix}
       \textrm {cos}(\theta /2) & -ie^{-i\varphi }\textrm {sin}(\theta /2)
       \\ -ie^{i\varphi }\textrm {sin}(\theta /2) & \textrm {cos}(\theta /2)
       \end{bmatrix}


   :param theta: Rotation angle in degrees, will be casted to the [-180, 180) domain.
   :param phi: Phase of the rotation axis, will be casted to the [0, 360) domain.
   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: X(qubit: str, **device_overrides)

   Bases: :py:obj:`Rxy`


   A single qubit rotation of 180 degrees around the X-axis.

   This operation can be represented by the following unitary:

   .. math::

       X180 = R_{X180} = \begin{bmatrix}
            0 & -i \\
            -i & 0 \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: X90(qubit: str, **device_overrides)

   Bases: :py:obj:`Rxy`


   A single qubit rotation of 90 degrees around the X-axis.

   It is identical to the Rxy gate with theta=90 and phi=0

   Defined by the unitary:

   .. math::
       X90 = R_{X90} = \frac{1}{\sqrt{2}}\begin{bmatrix}
               1 & -i \\
               -i & 1 \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: Y(qubit: str, **device_overrides)

   Bases: :py:obj:`Rxy`


   A single qubit rotation of 180 degrees around the Y-axis.

   It is identical to the Rxy gate with theta=180 and phi=90

   Defined by the unitary:

   .. math::
       Y180 = R_{Y180} = \begin{bmatrix}
            0 & -1 \\
            1 & 0 \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: Y90(qubit: str, **device_overrides)

   Bases: :py:obj:`Rxy`


   A single qubit rotation of 90 degrees around the Y-axis.

   It is identical to the Rxy gate with theta=90 and phi=90

   Defined by the unitary:

   .. math::

       Y90 = R_{Y90} = \frac{1}{\sqrt{2}}\begin{bmatrix}
               1 & -1 \\
               1 & 1 \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: Rz(theta: float, qubit: str, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   A single qubit rotation about the Z-axis of the Bloch sphere.

   This operation can be represented by the following unitary as defined in
   https://www.quantum-inspire.com/kbase/rz-gate/:

   .. math::

       \mathsf {R}_{z} \left(\theta\right) = \begin{bmatrix}
       e^{-i\theta/2} & 0
       \\ 0 & e^{i\theta/2} \end{bmatrix}

   :param theta: Rotation angle in degrees, will be cast to the [-180, 180) domain.
   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: Z(qubit: str, **device_overrides)

   Bases: :py:obj:`Rz`


   A single qubit rotation of 180 degrees around the Z-axis.

   Note that the gate implements :math:`R_z(\pi) = -iZ`, adding a global phase of :math:`-\pi/2`.
   This operation can be represented by the following unitary:

   .. math::

       Z180 = R_{Z180} = -iZ = e^{-\frac{\pi}{2}}Z = \begin{bmatrix}
            -i & 0 \\
            0 & i \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: Z90(qubit: str, **device_overrides)

   Bases: :py:obj:`Rz`


   A single qubit rotation of 90 degrees around the Z-axis.

   This operation can be represented by the following unitary:

   .. math::

       Z90 =
       R_{Z90} =
       e^{-\frac{\pi/2}{2}}S =
       e^{-\frac{\pi/2}{2}}\sqrt{Z} = \frac{1}{\sqrt{2}}\begin{bmatrix}
            1-i & 0 \\
            0 & 1+i \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: S(qubit: str, **device_overrides)

   Bases: :py:obj:`Z90`


   A single qubit rotation of 90 degrees around the Z-axis.

   This implements an :math:`S` gate up to a global phase.
   Therefore, this operation is a direct alias of the `Z90` operations

   This operation can be represented by the following unitary:

   .. math::

       R_{Z90} =
       e^{-i\frac{\pi}{4}}S =
       e^{-i\frac{\pi}{4}}\sqrt{Z} = \frac{1}{\sqrt{2}}\begin{bmatrix}
            1-i & 0 \\
            0 & 1+i \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: SDagger(qubit: str, **device_overrides)

   Bases: :py:obj:`Rz`


   A single qubit rotation of -90 degrees around the Z-axis.

   Implements :math:`S^\dagger` up to a global phase.

   This operation can be represented by the following unitary:

   .. math::

       R_{Z270} =
       e^{\frac{\pi}{4}}S^\dagger =
       e^{\frac{\pi}{4}}\sqrt{Z}^\dagger = \frac{1}{\sqrt{2}}\begin{bmatrix}
            1+i & 0 \\
            0 & 1-i \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: T(qubit: str, **device_overrides)

   Bases: :py:obj:`Rz`


   A single qubit rotation of 45 degrees around the Z-axis.

   Implements :math:`T` up to a global phase.

   This operation can be represented by the following unitary:

   .. math::

       R_{Z45} =
       e^{-\frac{\pi}{8}}T =
       e^{-\frac{\pi}{8}}\begin{bmatrix}
            1 & 0 \\
            0 & \frac{1+i}{\sqrt{2}} \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: TDagger(qubit: str, **device_overrides)

   Bases: :py:obj:`Rz`


   A single qubit rotation of -45 degrees around the Z-axis.

   Implements :math:`T^\dagger` up to a global phase.

   This operation can be represented by the following unitary:

   .. math::

       R_{Z315} =
       e^{\frac{\pi}{8}}T^\dagger =
       e^{\frac{\pi}{8}}\begin{bmatrix}
            1 & 0 \\
            0 & \frac{1-i}{\sqrt{2}} \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: H(*qubits: str, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   A single qubit Hadamard gate.

   Note that the gate uses :math:`R_z(\pi) = -iZ`, adding a global phase of :math:`-\pi/2`.
   This operation can be represented by the following unitary:

   .. math::

       H = Y90 \cdot Z = \frac{-i}{\sqrt{2}}\begin{bmatrix}
            1 & 1 \\
            1 & -1 \\ \end{bmatrix}

   :param qubit: The target device element.
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: CNOT(qC: str, qT: str, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Conditional-NOT gate, a common entangling gate.

   Performs an X gate on the target qubit qT conditional on the state
   of the control qubit qC.

   This operation can be represented by the following unitary:

   .. math::

       \mathrm{CNOT}  = \begin{bmatrix}
           1 & 0 & 0 & 0 \\
           0 & 1 & 0 & 0 \\
           0 & 0 & 0 & 1 \\
           0 & 0 & 1 & 0 \\ \end{bmatrix}

   :param qC: The control device element.
   :param qT: The target device element
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: CZ(qC: str, qT: str, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Conditional-phase gate, a common entangling gate.

   Performs a Z gate on the target device element qT conditional on the state
   of the control device element qC.

   This operation can be represented by the following unitary:

   .. math::

       \mathrm{CZ}  = \begin{bmatrix}
           1 & 0 & 0 & 0 \\
           0 & 1 & 0 & 0 \\
           0 & 0 & 1 & 0 \\
           0 & 0 & 0 & -1 \\ \end{bmatrix}

   :param qC: The control device element.
   :param qT: The target device element
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: Reset(*qubits: str, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Reset a qubit to the :math:`|0\rangle` state.

   The Reset gate is an idle operation that is used to initialize one or more qubits.

   .. note::

       Strictly speaking this is not a gate as it can not
       be described by a unitary.

   .. admonition:: Examples
       :class: tip

       The operation can be used in several ways:

       .. jupyter-execute::

           from qblox_scheduler.operations.gate_library import Reset

           reset_1 = Reset("q0")
           reset_2 = Reset("q1", "q2")
           reset_3 = Reset(*[f"q{i}" for i in range(3, 6)])

   :param qubits: The device element(s) to reset. NB one or more device element can be specified, e.g.,
                  :code:`Reset("q0")`, :code:`Reset("q0", "q1", "q2")`, etc..
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:class:: Measure(*qubits: str, acq_channel: collections.abc.Hashable | None = None, coords: dict | None = None, acq_index: tuple[int, Ellipsis] | tuple[None, Ellipsis] | int | None = None, acq_protocol: Literal['SSBIntegrationComplex', 'Timetag', 'TimetagTrace', 'Trace', 'TriggerCount', 'ThresholdedTriggerCount', 'NumericalSeparatedWeightedIntegration', 'NumericalWeightedIntegration', 'ThresholdedAcquisition'] | None = None, bin_mode: qblox_scheduler.enums.BinMode | str | None = None, feedback_trigger_label: str | None = None, **device_overrides)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   A projective measurement in the Z-basis.

   The measurement is compiled according to the type of acquisition specified
   in the device configuration.

   .. note::

       Strictly speaking this is not a gate as it can not
       be described by a unitary.

   :param qubits: The device elements you want to measure.
   :param acq_channel: Only for special use cases.
                       By default (if None): the acquisition channel specified in the device element is used.
                       If set, this acquisition channel is used for this measurement.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Index of the register where the measurement is stored.  If None specified,
                     this defaults to writing the result of all device elements to acq_index 0. By default
                     None.
   :param acq_protocol: Acquisition protocols that are supported. If ``None`` is specified, the
                        default protocol is chosen based on the device and backend configuration. By
                        default None.
   :type acq_protocol: "SSBIntegrationComplex" | "Trace" | "TriggerCount" |             "NumericalSeparatedWeightedIntegration" |             "NumericalWeightedIntegration" | None, Optional
   :param bin_mode: The binning mode that is to be used. If not None, it will overwrite the
                    binning mode used for Measurements in the circuit-to-device compilation
                    step. By default None.
   :param feedback_trigger_label: The label corresponding to the feedback trigger, which is mapped by the
                                  compiler to a feedback trigger address on hardware, by default None.
   :type feedback_trigger_label: str
   :param device_overrides: Device level parameters that override device configuration values
                            when compiling from circuit to device level.


.. py:function:: _modulo_360_with_mapping(theta: float) -> float

   Maps an input angle ``theta`` (in degrees) onto the range ``]-180, 180]``.

   By mapping the input angle to the range ``]-180, 180]`` (where -180 is
   excluded), it ensures that the output amplitude is always minimized on the
   hardware. This mapping should not have an effect on the device element in general.

   -180 degrees is excluded to ensure positive amplitudes in the gates like
   X180 and Z180.

   Note that an input of -180 degrees is remapped to 180 degrees to maintain
   the positive amplitude constraint.

   :param theta: The rotation angle in degrees. This angle will be mapped to the interval
                 ``]-180, 180]``.
   :type theta: float

   :returns: float
                 The mapped angle in degrees, which will be in the range ``]-180, 180]``.
                 This mapping ensures the output amplitude is always minimized for
                 transmon operations.

   .. rubric:: Example

   ```
   >>> _modulo_360_with_mapping(360)
   0.0
   >>> _modulo_360_with_mapping(-180)
   180.0
   >>> _modulo_360_with_mapping(270)
   -90.0
   ```


