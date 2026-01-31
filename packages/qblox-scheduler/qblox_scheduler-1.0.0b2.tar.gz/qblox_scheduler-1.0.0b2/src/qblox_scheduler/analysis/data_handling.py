# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.

"""Data handling utilities for Qblox Scheduler."""

import datetime
import sys
from pathlib import Path
from typing import Any, ClassVar, Literal, Optional

import rich
import xarray as xr
from dateutil.parser import parse

import quantify_core.data.dataset_adapters as da
from quantify_core.data.handling import snapshot as create_snapshot
from quantify_core.data.handling import write_dataset as qc_write_dataset
from quantify_core.data.types import TUID
from quantify_core.utilities.general import save_json


def _get_default_datadir(verbose: bool = False) -> Path:
    """
    Returns (and optionally print) a default datadir path.

    Intended for fast prototyping, tutorials, examples, etc..

    Parameters
    ----------
    verbose
        If ``True`` prints the returned datadir.

    Returns
    -------
    :
        The ``Path.home() / "qblox_data"`` path.

    """
    datadir = (Path.home() / "qblox_data").resolve()
    if verbose:
        rich.print(f"Data will be saved in:\n{datadir}")

    return datadir


class OutputDirectoryManager:
    """
    Manages output directory paths for Qblox Scheduler data storage.

    The class maintains a single instance throughout
    the application lifecycle, ensuring consistent directory management.

    Attributes
    ----------
    _datadir : str or Path
        The current data directory path. Private attribute managed through
        setter and getter methods.

    """

    DATADIR: ClassVar[Path] = _get_default_datadir()

    @classmethod
    def set_datadir(cls, datadir: Path | str | None = None) -> None:
        """
        Sets the data directory.

        Parameters
        ----------
        datadir : pathlib.Path or str or None
            Path of the data directory. If set to ``None``, resets the datadir to the
            default datadir (``<top_level>/data``).

        """
        if isinstance(datadir, str):
            datadir = Path(datadir)

        if datadir is None:
            datadir = _get_default_datadir()

        try:
            Path(datadir).mkdir(exist_ok=True, parents=True)
        except PermissionError as e:
            raise PermissionError(
                f"Permission error while setting datadir {datadir}."
                "\nPlease make sure you have the correct permissions."
            ) from e

        cls.DATADIR = datadir

    @classmethod
    def get_datadir(cls) -> Path:
        """
        Returns the current data directory.

        Returns
        -------
        :
            The current data directory.

        """
        if not Path.is_dir(cls.DATADIR):
            raise NotADirectoryError(
                "The datadir is not valid."
                "\nWe recommend to settle for a single common data directory for all \n"
                "notebooks/experiments within your measurement setup/PC.\n"
                "E.g. '~/qblox_data' (unix), or 'D:\\Data\\qblox_data' (Windows).\n"
            )
        return cls.DATADIR


class AnalysisDataContainer:
    """
    Class which represents all data related to an experiment. This allows the user to
    run experiments and store data. The class serves as an
    initial interface and uses the directory paths set by OutputDirectoryManager.
    """

    DATASET_NAME: ClassVar[str] = "dataset.hdf5"
    SNAPSHOT_FILENAME: ClassVar[str] = "snapshot.json"
    _TUID_LENGTH: ClassVar[int] = 26  # Length of "YYYYmmDD-HHMMSS-sss-******"

    def __init__(self, tuid: str, name: str):
        """
        Creates an instance of the AnalysisDataContainer.

        Parameters
        ----------
        tuid
            TUID to use
        name
            Name to append to the data directory path.

        """
        self.tuid = tuid

        # Date folder works as a container of TUIDs
        date_folder = tuid.split("-")[0]
        self.day_folder = OutputDirectoryManager.get_datadir() / date_folder
        Path.mkdir(self.day_folder, exist_ok=True)

        # A TUID folder that contains data and potentially snapshot
        self.data_folder = (
            (self.day_folder / f"{self.tuid}-{name}") if name else self.day_folder / f"{self.tuid}"
        )
        Path.mkdir(self.data_folder, exist_ok=True)

    @property
    def experiment_name(self) -> str:
        """The name of the experiment."""
        return self.tuid[self._TUID_LENGTH :]

    @classmethod
    def load_dataset(
        cls,
        tuid: TUID,
        name: str = DATASET_NAME,
    ) -> xr.Dataset:
        """
        Loads a dataset specified by a tuid.

        Parameters
        ----------
        tuid
            A :class:`~quantify_core.data.types.TUID` string. It is also possible to specify
            only the first part of a tuid.
        name
            Name of the dataset.

        Returns
        -------
        :
            The dataset.

        """
        day_folder = OutputDirectoryManager.get_datadir() / Path(tuid.split("-")[0])
        path = list(Path(day_folder).rglob(f"{tuid}*"))[0] / name
        return AnalysisDataContainer.load_dataset_from_path(path)

    @classmethod
    def load_dataset_from_path(cls, path: Path | str) -> xr.Dataset:
        """
        Loads a :class:`~xarray.Dataset` with a specific engine preference.

        Before returning the dataset :meth:`AdapterH5NetCDF.recover()
        <quantify_core.data.dataset_adapters.AdapterH5NetCDF.recover>` is applied.

        This function tries to load the dataset until success with the following engine
        preference:

        - ``"h5netcdf"``
        - ``"netcdf4"``
        - No engine specified (:func:`~xarray.load_dataset` default)

        Parameters
        ----------
        path
            Path to the dataset.

        Returns
        -------
        :
            The loaded dataset.

        """  # pylint: disable=line-too-long
        exceptions = []
        engines = ["h5netcdf", "netcdf4", None]
        for engine in engines:
            # there are three datasets that a user can load:
            # - "old" quantify datasets ( <2.0.0)
            # - "new" quantify datasets (>= 2.0.0)
            # - qblox-scheduler datasets

            try:
                dataset = xr.load_dataset(path, engine=engine)
            except Exception as exception:  # noqa: BLE001, PERF203
                exceptions.append(exception)
            else:
                # Only quantify_dataset_version=>2.0.0 requires the adapter
                if "quantify_dataset_version" in dataset.attrs:
                    dataset = da.AdapterH5NetCDF.recover(dataset)
                return dataset

        # Do not let exceptions pass silently
        for exception, engine in zip(exceptions, engines[: engines.index(engine)]):  # type: ignore  # noqa: B020, B905
            print(
                f"Failed loading dataset with '{engine}' engine. "
                f"Raised '{exception.__class__.__name__}':\n    {exception}",
            )
        # raise the last exception
        raise exception  # type: ignore

    def write_dataset(self, dataset: xr.Dataset) -> None:
        """
        Writes the quantify dataset to the directory specified by
        `~.data_folder`.

        Parameters
        ----------
        dataset
            The dataset to be written to the directory

        """
        qc_write_dataset(self.data_folder / self.DATASET_NAME, dataset)

    def save_snapshot(
        self,
        snapshot: Optional[dict[str, Any]] = None,
        compression: Literal["bz2", "gzip", "lzma"] | None = None,
    ) -> None:
        """
        Writes the snapshot to disk as specified by
        `~.data_folder`.

        Parameters
        ----------
        snapshot
            The snapshot to be written to the directory
        compression
            The compression type to use. Can be one of 'gzip', 'bz2', 'lzma'.
            Defaults to None, which means no compression.

        """
        if snapshot is None:
            snapshot = create_snapshot()
        save_json(
            directory=self.data_folder,
            filename=self.SNAPSHOT_FILENAME,
            data=snapshot,
            compression=compression,
        )

    @classmethod
    def get_latest_tuid(cls, contains: str = "") -> TUID:
        """Returns the most recent tuid.

        .. tip::

            This function is similar to :func:`~get_tuids_containing` but is preferred if
            one is only interested in the most recent
            :class:`~quantify_core.data.types.TUID` for performance reasons.

        Parameters
        ----------
        contains
            An optional string contained in the experiment name.

        Returns
        -------
        :
            The latest TUID.

        Raises
        ------
        FileNotFoundError
            No data found.
        """
        # `max_results=1, reverse=True` makes sure the tuid is found efficiently asap
        return AnalysisDataContainer.get_tuids_containing(contains, max_results=1, reverse=True)[0]

    @classmethod
    # pylint: disable=too-many-locals
    def get_tuids_containing(
        cls,
        contains: str = "",
        t_start: datetime.datetime | str | None = None,
        t_stop: datetime.datetime | str | None = None,
        max_results: int = sys.maxsize,
        reverse: bool = False,
    ) -> list[TUID]:
        """Returns a list of tuids containing a specific label.

        .. tip::

            If one is only interested in the most recent
            :class:`~quantify_core.data.types.TUID`, :func:`~get_latest_tuid` is preferred
            for performance reasons.

        Parameters
        ----------
        contains
            A string contained in the experiment name.
        t_start
            datetime to search from, inclusive. If a string is specified, it will be
            converted to a datetime object using :obj:`~dateutil.parser.parse`.
            If no value is specified, will use the year 1 as a reference t_start.
        t_stop
            datetime to search until, exclusive. If a string is specified, it will be
            converted to a datetime object using :obj:`~dateutil.parser.parse`.
            If no value is specified, will use the current time as a reference t_stop.
        max_results
            Maximum number of results to return. Defaults to unlimited.
        reverse
            If False, sorts tuids chronologically, if True sorts by most recent.

        Returns
        -------
        list
            A list of :class:`~quantify_core.data.types.TUID`: objects.

        Raises
        ------
        FileNotFoundError
            No data found.
        """
        datadir = OutputDirectoryManager.get_datadir()
        if isinstance(t_start, str):
            t_start = parse(t_start)
        elif t_start is None:
            t_start = datetime.datetime(1, 1, 1)
        if isinstance(t_stop, str):
            t_stop = parse(t_stop)
        elif t_stop is None:
            t_stop = datetime.datetime.now()

        # date range filters, define here to make the next line more readable
        d_start = t_start.strftime("%Y%m%d")
        d_stop = t_stop.strftime("%Y%m%d")

        def lower_bound(dir_name: str) -> bool:
            return dir_name >= d_start if d_start else True

        def upper_bound(dir_name: str) -> bool:
            return dir_name <= d_stop if d_stop else True

        daydirs = list(
            filter(
                lambda x: (
                    x.name.isdigit()
                    and len(x.name) == 8
                    and lower_bound(x.name)
                    and upper_bound(x.name)
                ),
                datadir.iterdir(),
            ),
        )
        daydirs.sort(reverse=reverse)
        if len(daydirs) == 0:
            err_msg = f"There are no valid day directories in the data folder '{datadir}'"
            if t_start or t_stop:
                err_msg += f", for the range {t_start or ''} to {t_stop or ''}"
            raise FileNotFoundError(err_msg)

        tuids = []
        for daydir in daydirs:
            expdirs = list(
                filter(
                    lambda x: (
                        len(x.name) > 25
                        and x.is_dir()
                        and (contains in x.name)  # label is part of exp_name
                        and TUID.is_valid(x.name[:26])  # tuid is valid
                        and (t_start <= TUID.datetime_seconds(x.name) < t_stop)
                    ),
                    Path.iterdir(datadir / daydir),
                ),
            )
            expdirs.sort(reverse=reverse)
            for expname in expdirs:
                # Check for inconsistent folder structure for datasets portability
                if daydir != expname.name[:8]:
                    raise FileNotFoundError(
                        f"Experiment container '{expname}' is in wrong day directory '{daydir}'",
                    )
                tuids.append(TUID(expname.name[:26]))
                if len(tuids) == max_results:
                    return tuids
        if len(tuids) == 0:
            raise FileNotFoundError(f"No experiment found containing '{contains}'")
        return tuids

    @classmethod
    def locate_experiment_container(cls, tuid: str) -> Path:
        """Returns the experiment container for the given tuid."""
        day_folder = Path(tuid.split("-")[0])

        # Based on the tuid check if there is a respective folder(s)
        folder_list = list(
            Path(OutputDirectoryManager.get_datadir() / day_folder).rglob(f"{tuid}*")
        )

        if len(folder_list) == 0:
            raise FileNotFoundError(
                f"Experiment container with given TUID {tuid}\
                                    was not found"
            )
        return folder_list[0]
