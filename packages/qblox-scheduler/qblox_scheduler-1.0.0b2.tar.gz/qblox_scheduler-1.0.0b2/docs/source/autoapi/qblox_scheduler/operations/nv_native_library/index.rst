nv_native_library
=================

.. py:module:: qblox_scheduler.operations.nv_native_library 

.. autoapi-nested-parse::

   NV-center-specific operations for use with the qblox_scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.operations.nv_native_library.ChargeReset
   qblox_scheduler.operations.nv_native_library.CRCount




.. py:class:: ChargeReset(*qubits: str)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Prepare a NV to its negative charge state NV$^-$.

   Create a new instance of ChargeReset operation that is used to initialize the
   charge state of an NV center.

   :param qubit: The qubit to charge-reset. NB one or more qubits can be specified, e.g.,
                 :code:`ChargeReset("qe0")`, :code:`ChargeReset("qe0", "qe1", "qe2")`, etc..


.. py:class:: CRCount(*qubits: str, acq_channel: collections.abc.Hashable | None = None, coords: dict | None = None, acq_index: tuple[int, Ellipsis] | tuple[None, Ellipsis] | int | None = None, acq_protocol: Literal['Trace', 'TriggerCount', None] = None, bin_mode: qblox_scheduler.enums.BinMode | None = None)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Operate ionization and spin pump lasers for charge and resonance counting.

   Gate level description for an optical CR count measurement.

   The measurement is compiled according to the type of acquisition specified
   in the device configuration.

   :param qubits: The qubits you want to measure
   :param acq_channel: Only for special use cases.
                       By default (if None): the acquisition channel specified in the device element is used.
                       If set, this acquisition channel is used for this measurement.
   :param coords: Coords for the acquisition.
                  These coordinates for the measured value for this operation
                  appear in the retrieved acquisition data.
                  For example ``coords={"amp": 0.1}`` has the effect, that the measured
                  value for this acquisition will be associated with ``amp==0.1``.
                  By default ``None``, no coords are added.
   :param acq_index: Index of the register where the measurement is stored.
                     If None specified, it will default to a list of zeros of len(qubits)
   :param acq_protocol: Acquisition protocol (currently ``"TriggerCount"`` and ``"Trace"``)
                        are supported. If ``None`` is specified, the default protocol is chosen
                        based on the device and backend configuration.
   :param bin_mode: The binning mode that is to be used. If not None, it will overwrite
                    the binning mode used for Measurements in the quantum-circuit to
                    quantum-device compilation step.


