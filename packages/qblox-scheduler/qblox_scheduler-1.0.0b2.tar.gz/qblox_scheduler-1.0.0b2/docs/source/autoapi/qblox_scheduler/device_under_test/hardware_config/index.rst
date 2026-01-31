hardware_config
===============

.. py:module:: qblox_scheduler.device_under_test.hardware_config 

.. autoapi-nested-parse::

   Module containing the HardwareConfig object.

   Extends ManualParameter to add methods to load from/to file and reload.
   Note: ManualParameter might be refactored out at some point in the future.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.device_under_test.hardware_config.HardwareConfig




.. py:class:: HardwareConfig(configuration: dict | None = None, instrument: qblox_scheduler.QuantumDevice | None = None)

   Bases: :py:obj:`collections.UserDict`


   The input dictionary used to generate a valid HardwareCompilationConfig.
   This configures the compilation from the quantum-device layer to the control-hardware layer.

   :param configuration: A dictionary with the hardware configuration.


   .. py:method:: set(value: dict) -> None

      Set the hardware configuration onto the dict itself.



   .. py:method:: load_from_json_file(file_path: str | pathlib.Path) -> None

      Reload the object's configuration from a file.
      Updates the object's data using the contents of the file.

      :param file_path: The path to the file to reload from.

      :raises FileNotFoundError: If the provided file path does not exist.
      :raises IOError: If an I/O error occurs during file reading.



   .. py:method:: write_to_json_file(file_path: str | pathlib.Path) -> None

      Write the current configuration to a specified file.
      If the file does not exist, it is created.
      The data is written in JSON format, and an indentation of 2.

      :param file_path: The path to the file where data will be written.

      :raises ValueError: If neither a file path is provided nor a previously known file path exists.
      :raises IOError: If an I/O error occurs during file creation or writing.



