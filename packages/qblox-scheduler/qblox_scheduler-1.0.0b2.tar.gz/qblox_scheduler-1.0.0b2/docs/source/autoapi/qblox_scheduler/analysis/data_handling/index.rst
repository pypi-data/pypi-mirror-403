data_handling
=============

.. py:module:: qblox_scheduler.analysis.data_handling 

.. autoapi-nested-parse::

   Data handling utilities for Qblox Scheduler.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.data_handling.OutputDirectoryManager
   qblox_scheduler.analysis.data_handling.AnalysisDataContainer



Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.analysis.data_handling._get_default_datadir



.. py:function:: _get_default_datadir(verbose: bool = False) -> pathlib.Path

   Returns (and optionally print) a default datadir path.

   Intended for fast prototyping, tutorials, examples, etc..

   :param verbose: If ``True`` prints the returned datadir.

   :returns: :
                 The ``Path.home() / "qblox_data"`` path.



.. py:class:: OutputDirectoryManager

   Manages output directory paths for Qblox Scheduler data storage.

   The class maintains a single instance throughout
   the application lifecycle, ensuring consistent directory management.

   .. attribute:: _datadir

      The current data directory path. Private attribute managed through
      setter and getter methods.

      :type: str or Path


   .. py:attribute:: DATADIR
      :type:  ClassVar[pathlib.Path]


   .. py:method:: set_datadir(datadir: pathlib.Path | str | None = None) -> None
      :classmethod:


      Sets the data directory.

      :param datadir: Path of the data directory. If set to ``None``, resets the datadir to the
                      default datadir (``<top_level>/data``).
      :type datadir: pathlib.Path or str or None



   .. py:method:: get_datadir() -> pathlib.Path
      :classmethod:


      Returns the current data directory.

      :returns: :
                    The current data directory.




.. py:class:: AnalysisDataContainer(tuid: str, name: str)

   Class which represents all data related to an experiment. This allows the user to
   run experiments and store data. The class serves as an
   initial interface and uses the directory paths set by OutputDirectoryManager.


   .. py:attribute:: DATASET_NAME
      :type:  ClassVar[str]
      :value: 'dataset.hdf5'



   .. py:attribute:: SNAPSHOT_FILENAME
      :type:  ClassVar[str]
      :value: 'snapshot.json'



   .. py:attribute:: _TUID_LENGTH
      :type:  ClassVar[int]
      :value: 26



   .. py:attribute:: tuid


   .. py:attribute:: day_folder


   .. py:attribute:: data_folder


   .. py:property:: experiment_name
      :type: str


      The name of the experiment.


   .. py:method:: load_dataset(tuid: quantify_core.data.types.TUID, name: str = DATASET_NAME) -> xarray.Dataset
      :classmethod:


      Loads a dataset specified by a tuid.

      :param tuid: A :class:`~quantify_core.data.types.TUID` string. It is also possible to specify
                   only the first part of a tuid.
      :param name: Name of the dataset.

      :returns: :
                    The dataset.




   .. py:method:: load_dataset_from_path(path: pathlib.Path | str) -> xarray.Dataset
      :classmethod:


      Loads a :class:`~xarray.Dataset` with a specific engine preference.

      Before returning the dataset :meth:`AdapterH5NetCDF.recover()
      <quantify_core.data.dataset_adapters.AdapterH5NetCDF.recover>` is applied.

      This function tries to load the dataset until success with the following engine
      preference:

      - ``"h5netcdf"``
      - ``"netcdf4"``
      - No engine specified (:func:`~xarray.load_dataset` default)

      :param path: Path to the dataset.

      :returns: :
                    The loaded dataset.




   .. py:method:: write_dataset(dataset: xarray.Dataset) -> None

      Writes the quantify dataset to the directory specified by
      `~.data_folder`.

      :param dataset: The dataset to be written to the directory



   .. py:method:: save_snapshot(snapshot: Optional[dict[str, Any]] = None, compression: Literal['bz2', 'gzip', 'lzma'] | None = None) -> None

      Writes the snapshot to disk as specified by
      `~.data_folder`.

      :param snapshot: The snapshot to be written to the directory
      :param compression: The compression type to use. Can be one of 'gzip', 'bz2', 'lzma'.
                          Defaults to None, which means no compression.



   .. py:method:: get_latest_tuid(contains: str = '') -> quantify_core.data.types.TUID
      :classmethod:


      Returns the most recent tuid.

      .. tip::

          This function is similar to :func:`~get_tuids_containing` but is preferred if
          one is only interested in the most recent
          :class:`~quantify_core.data.types.TUID` for performance reasons.

      :param contains: An optional string contained in the experiment name.

      :returns: :
                    The latest TUID.

      :raises FileNotFoundError: No data found.



   .. py:method:: get_tuids_containing(contains: str = '', t_start: datetime.datetime | str | None = None, t_stop: datetime.datetime | str | None = None, max_results: int = sys.maxsize, reverse: bool = False) -> list[quantify_core.data.types.TUID]
      :classmethod:


      Returns a list of tuids containing a specific label.

      .. tip::

          If one is only interested in the most recent
          :class:`~quantify_core.data.types.TUID`, :func:`~get_latest_tuid` is preferred
          for performance reasons.

      :param contains: A string contained in the experiment name.
      :param t_start: datetime to search from, inclusive. If a string is specified, it will be
                      converted to a datetime object using :obj:`~dateutil.parser.parse`.
                      If no value is specified, will use the year 1 as a reference t_start.
      :param t_stop: datetime to search until, exclusive. If a string is specified, it will be
                     converted to a datetime object using :obj:`~dateutil.parser.parse`.
                     If no value is specified, will use the current time as a reference t_stop.
      :param max_results: Maximum number of results to return. Defaults to unlimited.
      :param reverse: If False, sorts tuids chronologically, if True sorts by most recent.

      :returns: list
                    A list of :class:`~quantify_core.data.types.TUID`: objects.

      :raises FileNotFoundError: No data found.



   .. py:method:: locate_experiment_container(tuid: str) -> pathlib.Path
      :classmethod:


      Returns the experiment container for the given tuid.



