base
====

.. py:module:: qblox_scheduler.backends.qblox.operation_handling.base 

.. autoapi-nested-parse::

   Defines interfaces for operation handling strategies.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.backends.qblox.operation_handling.base.IOperationStrategy




.. py:class:: IOperationStrategy

   Bases: :py:obj:`abc.ABC`


   Defines the interface operation strategies must adhere to.


   .. py:property:: operation_info
      :type: qblox_scheduler.backends.types.qblox.OpInfo

      :abstractmethod:


      Returns the pulse/acquisition information extracted from the schedule.


   .. py:method:: generate_data(wf_dict: dict[str, object]) -> None
      :abstractmethod:


      Generates the waveform data and adds them to the wf_dict (if not already
      present). This is either the awg data, or the acquisition weights.

      :param wf_dict: The dictionary to add the waveform to. N.B. the dictionary is modified in
                      function.



   .. py:method:: insert_qasm(qasm_program: qblox_scheduler.backends.qblox.qasm_program.QASMProgram) -> None
      :abstractmethod:


      Add the assembly instructions for the Q1 sequence processor that corresponds to
      this pulse/acquisition.

      :param qasm_program: The QASMProgram to add the assembly instructions to.



