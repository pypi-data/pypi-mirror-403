q1asm_instructions
==================

.. py:module:: qblox_scheduler.backends.qblox.q1asm_instructions 

.. autoapi-nested-parse::

   Module that holds all the string literals that are valid instructions that can be
   executed by the sequencer in Qblox hardware.



Module Contents
---------------

.. py:data:: ILLEGAL
   :value: 'illegal'


.. py:data:: STOP
   :value: 'stop'


.. py:data:: NOP
   :value: 'nop'


.. py:data:: NEW_LINE
   :value: ''


.. py:data:: JUMP
   :value: 'jmp'


.. py:data:: LOOP
   :value: 'loop'


.. py:data:: JUMP_GREATER_EQUALS
   :value: 'jge'


.. py:data:: JUMP_LESS_THAN
   :value: 'jlt'


.. py:data:: MOVE
   :value: 'move'


.. py:data:: NOT
   :value: 'not'


.. py:data:: ADD
   :value: 'add'


.. py:data:: SUB
   :value: 'sub'


.. py:data:: AND
   :value: 'and'


.. py:data:: OR
   :value: 'or'


.. py:data:: XOR
   :value: 'xor'


.. py:data:: ARITHMETIC_SHIFT_LEFT
   :value: 'asl'


.. py:data:: ARITHMETIC_SHIFT_RIGHT
   :value: 'asr'


.. py:data:: SET_MARKER
   :value: 'set_mrk'


.. py:data:: SET_FREQUENCY
   :value: 'set_freq'


.. py:data:: RESET_PHASE
   :value: 'reset_ph'


.. py:data:: SET_NCO_PHASE_OFFSET
   :value: 'set_ph'


.. py:data:: INCR_NCO_PHASE_OFFSET
   :value: 'set_ph_delta'


.. py:data:: SET_AWG_GAIN
   :value: 'set_awg_gain'


.. py:data:: SET_AWG_OFFSET
   :value: 'set_awg_offs'


.. py:data:: SET_DIGITAL
   :value: 'set_digital'


.. py:data:: SET_TIME_REF
   :value: 'set_time_ref'


.. py:data:: SET_SCOPE_EN
   :value: 'set_scope_en'


.. py:data:: PLAY
   :value: 'play'


.. py:data:: ACQUIRE
   :value: 'acquire'


.. py:data:: ACQUIRE_WEIGHED
   :value: 'acquire_weighed'


.. py:data:: ACQUIRE_TTL
   :value: 'acquire_ttl'


.. py:data:: WAIT
   :value: 'wait'


.. py:data:: WAIT_SYNC
   :value: 'wait_sync'


.. py:data:: WAIT_TRIGGER
   :value: 'wait_trigger'


.. py:data:: UPDATE_PARAMETERS
   :value: 'upd_param'


.. py:data:: FEEDBACK_SET_COND
   :value: 'set_cond'


.. py:data:: FEEDBACK_TRIGGER_EN
   :value: 'set_latch_en'


.. py:data:: FEEDBACK_TRIGGERS_RST
   :value: 'latch_rst'


.. py:data:: PLAY_PULSE
   :value: 'play_pulse'


.. py:data:: ACQUIRE_TIMETAGS
   :value: 'acquire_timetags'


.. py:data:: ACQUIRE_DIGITAL
   :value: 'acquire_digital'


.. py:data:: UPD_THRES
   :value: 'upd_thres'


