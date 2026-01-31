collections
===========

.. py:module:: qblox_scheduler.helpers.collections 

.. autoapi-nested-parse::

   Helpers for various collections.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.helpers.collections.make_hash
   qblox_scheduler.helpers.collections.without
   qblox_scheduler.helpers.collections.find_inner_dicts_containing_key
   qblox_scheduler.helpers.collections.find_all_port_clock_combinations
   qblox_scheduler.helpers.collections.find_port_clock_path



.. py:function:: make_hash(obj: set | tuple | list | numpy.ndarray | dict | collections.abc.Hashable) -> int

   Make a hash from a dictionary, list, tuple or set to any level.

   From: https://stackoverflow.com/questions/5884066/hashing-a-dictionary

   :param obj: Input collection.

   :returns: :
                 Hash.



.. py:function:: without(dict_in: dict, keys: list) -> dict

   Copy a dictionary excluding a specific list of keys.

   :param dict_in: Input dictionary.
   :param keys: List of keys to exclude.

   :returns: :
                 Filtered dictionary.



.. py:function:: find_inner_dicts_containing_key(d: collections.abc.MutableMapping, key: collections.abc.Hashable) -> list[dict]

   Generate a list of the first dictionaries encountered that contain a certain key.

   This is achieved by recursively traversing the nested structures until the key is
   found, which is then appended to a list.

   :param d: The dictionary to traverse.
   :param key: The key to search for.

   :returns: :
                 A list containing all the inner dictionaries containing the specified key.



.. py:function:: find_all_port_clock_combinations(d: dict) -> list[tuple[str, str]]

   Generate a list with all port-clock combinations found in a nested dictionary.

   Traversing the dictionary is done using the
   ``find_inner_dicts_containing_key`` function.

   :param d: The dictionary to traverse.

   :returns: :
                 A list containing tuples representing the port and clock combinations found
                 in the dictionary.



.. py:function:: find_port_clock_path(hardware_config: dict, port: str, clock: str) -> list

   Find the path to a port-clock combination in a nested dictionary.

   :param hardware_config: The (nested) hardware config dictionary to loop over.
   :param port: The port to find.
   :param clock: The clock to find.

   :returns: :
                 A list representing the keys to the port-clock combination in the hardware config.
                 If the port-clock location is in a list, the list index is also included in this path.



