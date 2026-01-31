constants
=========

.. py:module:: qblox_scheduler.backends.qblox.constants 

.. autoapi-nested-parse::

   Constants for compilation to Qblox hardware.



Module Contents
---------------

.. py:data:: MAX_NUMBER_OF_INSTRUCTIONS_QCM
   :type:  int
   :value: 16384


   Maximum supported number of instructions in Q1ASM programs for QCM/QCM-RF.

.. py:data:: MAX_NUMBER_OF_INSTRUCTIONS_QRM
   :type:  int
   :value: 12288


   Maximum supported number of instructions in Q1ASM programs for QRM/QRM-RF.

.. py:data:: MAX_NUMBER_OF_INSTRUCTIONS_QRC
   :type:  int
   :value: 12288


   Maximum supported number of instructions in Q1ASM programs for QRC.

.. py:data:: MAX_NUMBER_OF_INSTRUCTIONS_QTM
   :type:  int
   :value: 16384


   Maximum supported number of instructions in Q1ASM programs for QTM.

.. py:data:: IMMEDIATE_SZ_GAIN

   Size of gain instruction immediates in Q1ASM programs.

.. py:data:: IMMEDIATE_MAX_WAIT_TIME

   Max size of wait instruction immediates in Q1ASM programs. Max value allowed by
   assembler is 2**16-1, but this is the largest that is a multiple of 4 ns.

.. py:data:: IMMEDIATE_SZ_OFFSET

   Size of offset instruction immediates in Q1ASM programs.

.. py:data:: REGISTER_SIZE_BITS
   :value: 32


   Size of registers in Q1ASM programs, in number of bits.

.. py:data:: AWG_INSTRUCTION_BIT_SIZE
   :value: 16


   Amount of bits allocated for the `set_awg_gain` and `set_awg_offs` instructions.

.. py:data:: REGISTER_SIZE

   Size of registers in Q1ASM programs.

.. py:data:: NUMBER_OF_QBLOX_ACQ_INDICES
   :type:  int
   :value: 32


   Maximum number of Qblox acquisition index.

.. py:data:: MAX_NUMBER_OF_RUNTIME_ALLOCATED_QBLOX_ACQ_BINS
   :type:  int
   :value: 4096


   Maximum number of Qblox acquisition bins for acquisitions that allocate bins at runtime
   (e.g. TriggerCount on a QRM with BinMode.DISTRIBUTION).

.. py:data:: NCO_PHASE_STEPS_PER_DEG
   :value: 2777777.777777778


   The number of steps per degree for NCO phase instructions arguments.

.. py:data:: NCO_FREQ_STEPS_PER_HZ
   :value: 4.0


   The number of steps per Hz for the NCO set_freq instruction.

.. py:data:: NCO_FREQ_LIMIT_STEPS
   :value: 2000000000.0


.. py:data:: GRID_TIME
   :value: 1


   Clock period of the sequencers. All time intervals used must be multiples of this value.

.. py:data:: MIN_TIME_BETWEEN_OPERATIONS
   :value: 4


   Minimum time between two operations to prevent FIFO errors.

.. py:data:: MIN_TIME_BETWEEN_NCO_OPERATIONS
   :value: 4


   Minimum time between two frequency updates or two phase updates..

.. py:data:: MIN_TIME_BETWEEN_ACQUISITIONS
   :value: 300


   Minimum time between two acquisitions to prevent FIFO errors.

.. py:data:: SAMPLING_RATE
   :value: 1000000000


   Sampling rate of the Qblox control/readout instruments.

.. py:data:: STITCHED_PULSE_PART_DURATION_NS
   :value: 2000


   Default duration of the individual waveforms that are used to build up a longer
   stitched waveform. See
   :func:`~qblox_scheduler.operations.hardware_operations.pulse_factories.long_ramp_pulse` for an
   example.

.. py:data:: PULSE_STITCHING_DURATION
   :value: 1e-07


   Duration of the individual pulses when pulse stitching is used.
   Only applies to square pulses.

.. py:data:: PULSE_STITCHING_DURATION_RAMP
   :value: 2e-06


   Duration of the individual pulses when RampPulse is concerted to long_ramp_pulse.

.. py:data:: DEFAULT_MIXER_PHASE_ERROR_DEG
   :value: 0.0


   Default phase shift in the instruments for mixer corrections.

.. py:data:: MIN_MIXER_PHASE_ERROR_DEG
   :value: -45


   Lowest phase shift that can be configured in the instruments for mixer corrections.

.. py:data:: MAX_MIXER_PHASE_ERROR_DEG
   :value: 45


   Highest phase shift that can be configured in the instruments for mixer corrections.

.. py:data:: DEFAULT_MIXER_AMP_RATIO
   :value: 1.0


   Default value of the amplitude correction. N.B. This correction is defined
   as Q/I.

.. py:data:: MIN_MIXER_AMP_RATIO
   :value: 0.5


   Lowest value the amplitude correction can be set to. N.B. This correction is defined
   as Q/I.

.. py:data:: MAX_MIXER_AMP_RATIO
   :value: 2.0


   Highest value the amplitude correction can be set to. N.B. This correction is defined
   as Q/I.

.. py:data:: NUMBER_OF_REGISTERS
   :type:  int
   :value: 64


   Number of registers available in the Qblox sequencers.

.. py:data:: MAX_SAMPLE_SIZE_SCOPE_ACQUISITIONS
   :type:  int
   :value: 16384


   Maximal amount of scope trace acquisition datapoints returned.

.. py:data:: MAX_SAMPLE_SIZE_WAVEFORMS
   :type:  int
   :value: 16384


   Maximal amount of samples in the waveforms to be uploaded to a sequencer.

.. py:data:: MIN_PHASE_ROTATION_ACQ
   :value: 0


   Minimum value of the sequencer integration result phase rotation in degrees.

.. py:data:: MAX_PHASE_ROTATION_ACQ
   :value: 360


   Maximum value of the sequencer integration result phase rotation in degrees.

.. py:data:: MIN_DISCRETIZATION_THRESHOLD_ACQ
   :value: -16777212.0


   Minimum value of the sequencer discretization threshold
   for discretizing the phase rotation result.

.. py:data:: MAX_DISCRETIZATION_THRESHOLD_ACQ
   :value: 16777212.0


   Maximum value of the sequencer discretization threshold
   for discretizing the phase rotation result.

.. py:data:: MAX_NUMBER_OF_BINS
   :type:  int
   :value: 131072


   Number of bins available in the Qblox sequencers.

.. py:data:: GENERIC_IC_COMPONENT_NAME
   :type:  str
   :value: 'generic'


   Default name for the generic instrument coordinator component.

.. py:data:: TRIGGER_DELAY
   :type:  float
   :value: 3.64e-07


   Total delay time of the feedback trigger before it is registered after the
   end of a thresholded acquisition.

.. py:data:: MAX_FEEDBACK_TRIGGER_ADDRESS
   :type:  int
   :value: 15


   Available trigger addresses on each cluster range from 1,...,15.

.. py:data:: MAX_MIN_INSTRUCTION_WAIT
   :type:  float
   :value: 4e-09


   Maximum of minimum wait times for real-time-instructions. e.g. play,
   set_cond, acquire, require at least 4ns.

.. py:data:: GRID_TIME_TOLERANCE_TIME
   :type:  float
   :value: 0.0011


   Tolerance for time values in nanoseconds.

   .. versionadded:: 0.21.2

.. py:data:: QTM_FINE_DELAY_INT_TO_NS_RATIO
   :value: 128


   Ratio of the integer fine delay argument value to the actual delay in nanoseconds.

   The fine delay argument has a resolution of 1/128 ns.

.. py:data:: MAX_QTM_FINE_DELAY_NS
   :value: 15.9921875


   Maximum fine delay value in nanoseconds for QTM instructions that take a fine delay
   argument.

   The maximum integer value is based on an 11-bit unsigned integer.

.. py:data:: MIN_FINE_DELAY_SPACING_NS
   :value: 7


   QTM instructions with unequal fine delay must be at least this far apart in time.

.. py:data:: FIR_COEFF_RESOLUTION

   The precision with which to validate the FIR coefficients. Based on the finite word length of 16
   bits on the FPGA.

