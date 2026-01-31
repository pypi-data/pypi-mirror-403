helpers
=======

.. py:module:: qblox_scheduler.backends.qblox.helpers 

.. autoapi-nested-parse::

   Helper functions for Qblox backend.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.helpers.Frequencies
   qblox_scheduler.backends.qblox.helpers.ValidatedFrequencies
   qblox_scheduler.backends.qblox.helpers.LoopBegin
   qblox_scheduler.backends.qblox.helpers.ConditionalBegin
   qblox_scheduler.backends.qblox.helpers._ControlFlowReturn



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.helpers.generate_waveform_data
   qblox_scheduler.backends.qblox.helpers.generate_waveform_names_from_uuid
   qblox_scheduler.backends.qblox.helpers.generate_uuid_from_wf_data
   qblox_scheduler.backends.qblox.helpers.add_to_wf_dict_if_unique
   qblox_scheduler.backends.qblox.helpers.generate_waveform_dict
   qblox_scheduler.backends.qblox.helpers.to_grid_time
   qblox_scheduler.backends.qblox.helpers.is_multiple_of_grid_time
   qblox_scheduler.backends.qblox.helpers.get_nco_phase_arguments
   qblox_scheduler.backends.qblox.helpers.get_nco_set_frequency_arguments
   qblox_scheduler.backends.qblox.helpers.determine_clock_lo_interm_freqs
   qblox_scheduler.backends.qblox.helpers.generate_port_clock_to_device_map
   qblox_scheduler.backends.qblox.helpers._get_control_flow_begins
   qblox_scheduler.backends.qblox.helpers._get_control_flow_ends
   qblox_scheduler.backends.qblox.helpers._get_list_of_operations_for_op_info_creation
   qblox_scheduler.backends.qblox.helpers._assign_pulse_info_to_devices
   qblox_scheduler.backends.qblox.helpers._assign_acq_info_to_devices
   qblox_scheduler.backends.qblox.helpers._assign_asm_info_to_devices
   qblox_scheduler.backends.qblox.helpers.assign_pulse_and_acq_info_to_devices
   qblox_scheduler.backends.qblox.helpers.calc_from_units_volt
   qblox_scheduler.backends.qblox.helpers.single_scope_mode_acquisition_raise
   qblox_scheduler.backends.qblox.helpers.is_square_pulse
   qblox_scheduler.backends.qblox.helpers.convert_qtm_fine_delay_to_int



.. py:function:: generate_waveform_data(data_dict: dict, sampling_rate: float, duration: float | None = None) -> numpy.ndarray

   Generates an array using the parameters specified in ``data_dict``.

   :param data_dict: The dictionary that contains the values needed to parameterize the
                     waveform. ``data_dict['wf_func']`` is then called to calculate the values.
   :type data_dict: dict
   :param sampling_rate: The sampling rate used to generate the time axis values.
   :type sampling_rate: float
   :param duration: The duration of the waveform in seconds. This parameter can be used if
                    ``data_dict`` does not contain a ``'duration'`` key. By default None.
   :type duration: float or None, Optional

   :returns: wf_data : np.ndarray
                 The (possibly complex) values of the generated waveform. The number of values is
                 determined by rounding to the nearest integer.

   :raises TypeError: If ``data_dict`` does not contain a ``'duration'`` entry and ``duration is
       None``.


.. py:function:: generate_waveform_names_from_uuid(uuid: object) -> tuple[str, str]

   Generates names for the I and Q parts of the complex waveform based on a unique
   identifier for the pulse/acquisition.

   :param uuid: A unique identifier for a pulse/acquisition.

   :returns: uuid_I:
                 Name for the I waveform.
             uuid_Q:
                 Name for the Q waveform.



.. py:function:: generate_uuid_from_wf_data(wf_data: numpy.ndarray, decimals: int = 12) -> str

   Creates a unique identifier from the waveform data, using a hash. Identical arrays
   yield identical strings within the same process.

   :param wf_data: The data to generate the unique id for.
   :param decimals: The number of decimal places to consider.

   :returns: :
                 A unique identifier.



.. py:function:: add_to_wf_dict_if_unique(wf_dict: dict[str, Any], waveform: numpy.ndarray) -> int

   Adds a waveform to the waveform dictionary if it is not yet in there and returns the
   uuid and index. If it is already present it simply returns the uuid and index.

   :param wf_dict: The waveform dict in the format expected by the sequencer.
   :param waveform: The waveform to add.

   :returns: dict[str, Any]
                 The (updated) wf_dict.
             str
                 The uuid of the waveform.
             int
                 The index.



.. py:function:: generate_waveform_dict(waveforms_complex: dict[str, numpy.ndarray]) -> dict[str, dict]

   Takes a dictionary with complex waveforms and generates a new dictionary with
   real valued waveforms with a unique index, as required by the hardware.

   :param waveforms_complex: Dictionary containing the complex waveforms. Keys correspond to a unique
                             identifier, value is the complex waveform.

   :returns: dict[str, dict]
                 A dictionary with as key the unique name for that waveform, as value another
                 dictionary containing the real-valued data (list) as well as a unique index.
                 Note that the index of the Q waveform is always the index of the I waveform
                 +1.


   .. admonition:: Examples

       .. jupyter-execute::

           import numpy as np
           from qblox_scheduler.backends.qblox.helpers import generate_waveform_dict

           complex_waveforms = {12345: np.array([1, 2])}
           generate_waveform_dict(complex_waveforms)

           # {'12345_I': {'data': [1, 2], 'index': 0},
           # '12345_Q': {'data': [0, 0], 'index': 1}}



.. py:function:: to_grid_time(time: float, grid_time_ns: int = constants.GRID_TIME) -> int

   Convert time value in s to time in ns, and verify that it is aligned with grid time.

   Takes a float value representing a time in seconds as used by the schedule, and
   returns the integer valued time in nanoseconds that the sequencer uses.

   The time value needs to be aligned with grid time, i.e., needs to be a multiple
   of :data:`~.constants.GRID_TIME`, within a tolerance of 1 picosecond.

   :param time: A time value in seconds.
   :param grid_time_ns: The grid time to use in nanoseconds.

   :returns: :
                 The integer valued nanosecond time.

   :raises ValueError: If ``time`` is not a multiple of :data:`~.constants.GRID_TIME` within the tolerance.


.. py:function:: is_multiple_of_grid_time(time: float, grid_time_ns: int = constants.GRID_TIME) -> bool

   Determine whether a time value in seconds is a multiple of the grid time.

   Within a tolerance as defined by
   :meth:`~qblox_scheduler.backends.qblox.helpers.to_grid_time`.

   :param time: A time value in seconds.
   :param grid_time_ns: The grid time to use in nanoseconds.

   :returns: :
                 ``True`` if ``time`` is a multiple of the grid time, ``False`` otherwise.



.. py:function:: get_nco_phase_arguments(phase_deg: float) -> int

   Converts a phase in degrees to the int arguments the NCO phase instructions expect.
   We take ``phase_deg`` modulo 360 to account for negative phase and phase larger than
   360.

   :param phase_deg: The phase in degrees

   :returns: :
                 The int corresponding to the phase argument.



.. py:function:: get_nco_set_frequency_arguments(frequency_hz: float) -> int

   Converts a frequency in Hz to the int argument the NCO set_freq instruction expects.

   :param frequency_hz: The frequency in Hz.

   :returns: :
                 The frequency expressed in steps for the NCO set_freq instruction.

   :raises ValueError: If the frequency_hz is out of range.


.. py:class:: Frequencies

   Holds and validates frequencies.


   .. py:attribute:: clock
      :type:  float


   .. py:attribute:: LO
      :type:  float | None
      :value: None



   .. py:attribute:: IF
      :type:  float | None
      :value: None



.. py:class:: ValidatedFrequencies

   Simple dataclass that holds immutable frequencies after validation.


   .. py:attribute:: clock
      :type:  float


   .. py:attribute:: LO
      :type:  float


   .. py:attribute:: IF
      :type:  float


.. py:function:: determine_clock_lo_interm_freqs(freqs: Frequencies, downconverter_freq: float | None = None, mix_lo: bool | None = True) -> ValidatedFrequencies

   From known frequency for the local oscillator or known intermodulation frequency,
   determine any missing frequency, after optionally applying ``downconverter_freq`` to
   the clock frequency.

   If ``mix_lo`` is ``True``, the following relation is obeyed:
   :math:`f_{RF} = f_{LO} + f_{IF}`.

   If ``mix_lo`` is ``False``, :math:`f_{RF} = f_{LO}` is upheld.

   .. warning::
       Using ``downconverter_freq`` requires custom Qblox hardware, do not use otherwise.

   :param freqs: Frequencies object containing clock, local oscillator (LO) and
                 Intermodulation frequency (IF), the frequency of the numerically controlled
                 oscillator (NCO).
   :type freqs: Frequencies
   :param downconverter_freq: Frequency for downconverting the clock frequency, using:
                              :math:`f_\mathrm{out} = f_\mathrm{downconverter} - f_\mathrm{in}`.
   :type downconverter_freq: Optional[float]
   :param mix_lo: Flag indicating whether IQ mixing is enabled with the LO.
   :type mix_lo: bool

   :returns: :
                 :class:`.ValidatedFrequencies` object containing the determined LO and IF
                 frequencies and the optionally downconverted clock frequency.

   :Warns: * **RuntimeWarning** -- In case ``downconverter_freq`` is set equal to 0, warns to unset via
             ``null``/``None`` instead.
           * **RuntimeWarning** -- In case LO is overridden to clock due to ``mix_lo`` being `False`

   :raises ValueError: In case ``downconverter_freq`` is less than 0.
   :raises ValueError: In case ``downconverter_freq`` is less than ``clock_freq``.
   :raises ValueError: In case ``mix_lo`` is ``True`` and neither LO frequency nor IF has been supplied.
   :raises ValueError: In case ``mix_lo`` is ``True`` and both LO frequency
       and IF have been supplied and do not adhere to
       :math:`f_{RF} = f_{LO} + f_{IF}`.


.. py:function:: generate_port_clock_to_device_map(device_compilers: dict[str, Any]) -> dict[str, str]

   Generates a mapping that specifies which port-clock combinations belong to which
   device.

   Here, device means a top-level entry in the hardware config, e.g. a Cluster,
   not which module within the Cluster.

   Each port-clock combination may only occur once.

   :param device_compilers: Dictionary containing compiler configs.

   :returns: :
                 A dictionary with as key a tuple representing a port-clock combination, and
                 as value the name of the device. Note that multiple port-clocks may point to
                 the same device.

   :raises ValueError: If a port-clock combination occurs multiple times in the hardware configuration.


.. py:class:: LoopBegin(repetitions: int, t0: float = 0, domain: dict[qblox_scheduler.operations.variables.Variable, qblox_scheduler.operations.loop_domains.LinearDomain] | None = None)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Operation to indicate the beginning of a loop.

   :param repetitions: number of repetitions
   :type repetitions: int
   :param t0: time offset, by default 0
   :type t0: float, Optional


.. py:class:: ConditionalBegin(qubit_name: str, feedback_trigger_address: int, feedback_trigger_invert: bool, feedback_trigger_count: int, t0: float)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   Operation to indicate the beginning of a conditional.

   :param qubit_name: The name of the device element to condition on.
   :param feedback_trigger_address: Feedback trigger address
   :param t0: Time offset, by default 0


.. py:function:: _get_control_flow_begins(control_flow_operation: qblox_scheduler.operations.control_flow_library.ControlFlowOperation) -> list[qblox_scheduler.operations.operation.Operation]

.. py:class:: _ControlFlowReturn(t0: float = 0)

   Bases: :py:obj:`qblox_scheduler.operations.operation.Operation`


   An operation that signals the end of the current control flow statement.

   Cannot be added to TimeableSchedule manually.

   :param t0: time offset, by default 0
   :type t0: float, Optional


.. py:function:: _get_control_flow_ends(control_flow_operation: qblox_scheduler.operations.control_flow_library.ControlFlowOperation) -> list[qblox_scheduler.operations.operation.Operation]

.. py:function:: _get_list_of_operations_for_op_info_creation(operation: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule, time_offset: float, accumulator: list[tuple[float, qblox_scheduler.operations.operation.Operation, qblox_scheduler.helpers.generate_acq_channels_data.FullSchedulableLabel]], full_schedulable_label: qblox_scheduler.helpers.generate_acq_channels_data.FullSchedulableLabel) -> None

.. py:function:: _assign_pulse_info_to_devices(device_compilers: dict[str, qblox_scheduler.backends.qblox.instrument_compilers.ClusterCompiler], portclock_mapping: dict[str, str], name: str, pulse_info: dict[str, Any], operation_start_time: float) -> None

.. py:function:: _assign_acq_info_to_devices(device_compilers: dict[str, qblox_scheduler.backends.qblox.instrument_compilers.ClusterCompiler], portclock_mapping: dict[str, str], name: str, acquisition_info: dict[str, Any], operation_start_time: float, schedulable_label_to_acq_index: qblox_scheduler.helpers.generate_acq_channels_data.SchedulableLabelToAcquisitionIndex, optional_full_schedulable_label: qblox_scheduler.helpers.generate_acq_channels_data.FullSchedulableLabel) -> None

.. py:function:: _assign_asm_info_to_devices(device_compilers: dict[str, qblox_scheduler.backends.qblox.instrument_compilers.ClusterCompiler], portclock_mapping: dict[str, str], operation: qblox_scheduler.operations.hardware_operations.inline_q1asm.InlineQ1ASM, op_start_time: float) -> None

.. py:function:: assign_pulse_and_acq_info_to_devices(schedule: qblox_scheduler.schedules.schedule.TimeableSchedule, device_compilers: dict[str, qblox_scheduler.backends.qblox.instrument_compilers.ClusterCompiler], schedulable_label_to_acq_index: qblox_scheduler.helpers.generate_acq_channels_data.SchedulableLabelToAcquisitionIndex) -> None

   Traverses the schedule and generates `OpInfo` objects for every pulse and
   acquisition, and assigns it to the correct `ClusterCompiler`.

   :param schedule: The schedule to extract the pulse and acquisition info from.
   :param device_compilers: Dictionary containing InstrumentCompilers as values and their names as keys.
   :param schedulable_label_to_acq_index: Schedulable label to acquisition indices dictionary for binned acquisitions.

   :raises RuntimeError: This exception is raised then the function encountered an operation that has no
       pulse or acquisition info assigned to it.
   :raises KeyError: This exception is raised when attempting to assign a pulse with a port-clock
       combination that is not defined in the hardware configuration.
   :raises KeyError: This exception is raised when attempting to assign an acquisition with a
       port-clock combination that is not defined in the hardware configuration.


.. py:function:: calc_from_units_volt(voltage_range: qblox_scheduler.backends.types.qblox.BoundedParameter, name: str, param_name: str, offset: float | None) -> float | None

   Helper method to calculate the offset from mV or V.
   Then compares to given voltage range, and throws a ValueError if out of bounds.

   :param voltage_range: The range of the voltage levels of the device used.
   :param name: The name of the device used.
   :param param_name: The name of the offset parameter this method is using.
   :param offset: The value of the offset parameter this method is using.

   :returns: :
                 The normalized offsets.

   :raises RuntimeError: When a unit range is given that is not supported, or a value is given that falls
       outside the allowed range.


.. py:function:: single_scope_mode_acquisition_raise(sequencer_0: int, sequencer_1: int, module_name: str) -> None

   Raises an error stating that only one scope mode acquisition can be used per module.

   :param sequencer_0: First sequencer which attempts to use the scope mode acquisition.
   :param sequencer_1: Second sequencer which attempts to use the scope mode acquisition.
   :param module_name: Name of the module.

   :raises ValueError: Always raises the error message.


.. py:function:: is_square_pulse(operation: qblox_scheduler.operations.operation.Operation | qblox_scheduler.schedules.schedule.TimeableSchedule) -> bool

   Check if the operation is a square pulse.

   :param operation: The operation to check.

   :returns: :
                 True if the operation is a square pulse, False otherwise.



.. py:function:: convert_qtm_fine_delay_to_int(fine_delay: float) -> int

   Convert a fine delay value in seconds to an integer value for Q1ASM.


