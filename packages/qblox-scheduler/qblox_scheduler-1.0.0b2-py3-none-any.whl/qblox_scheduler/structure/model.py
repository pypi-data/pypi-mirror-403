# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Root models for data structures used within the package."""

# ruff: noqa: ANN401

from __future__ import annotations

import os
import warnings
from datetime import datetime, timezone
from inspect import isclass
from io import StringIO
from typing import TYPE_CHECKING, Annotated, Any, TypedDict
from typing_extensions import Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    TypeAdapter,
    model_validator,
)
from pydantic_core import PydanticUndefined

from qblox_scheduler.analysis.data_handling import OutputDirectoryManager
from qblox_scheduler.helpers.importers import import_python_object_from_string
from qblox_scheduler.yaml_utils import register_model, yaml

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


_Unset: Any = PydanticUndefined


class Numbers(TypedDict, total=False):
    """Dict used to emulate the behaviour of the ``Numbers`` qcodes validator."""

    min_value: float
    max_value: float
    allow_nan: bool


def Parameter(  # noqa: N802
    *,
    initial_value: Any = _Unset,
    label: str | None = _Unset,
    docstring: str | None = _Unset,
    unit: str | None = _Unset,
    vals: Numbers | None = _Unset,
    **kwargs: Any,
) -> Any:
    """
    Wrapper function around `:func:~pydantic.Field` that tries to emulate qcodes parameters
    as closely as possible, to facilitate migration and reduce diff lines.

    Parameters
    ----------
    initial_value
        Maps to ``default`` or ``default_factory`` (if callable).
    label
        Maps to ``title``, displayed on the JSON schema.
    docstring
        Maps to ``description``, displayed on the JSON schema.
    unit
        Stored internally, retrievable using :meth:`~SchedulerBaseModel.get_unit`.
    vals
        Maps to ``allow_inf_nan``, ``ge`` and ``le``.
    kwargs
        Other arguments passed on to the original ``Field`` function.

    Returns
    -------
    Any:
        To appease the linters; actually a `:class:~pydantic.fields.FieldInfo` instance.

    """
    if initial_value is not _Unset:
        if callable(initial_value):
            kwargs["default_factory"] = initial_value
        else:
            kwargs["default"] = initial_value

    if label is not _Unset:
        kwargs["title"] = label
    if docstring is not _Unset:
        kwargs["description"] = docstring
    if vals is not _Unset:
        if (allow_nan := vals.get("allow_nan")) is not None:  # type: ignore
            kwargs["allow_inf_nan"] = allow_nan
        # TODO: Pydantic doesn't behave well when both NaN and numerical constraints are involved.
        #  We need to create a custom annotation validator for this case.
        else:
            if (min_value := vals.get("min_value")) is not None:  # type: ignore
                kwargs["ge"] = min_value
            if (max_value := vals.get("max_value")) is not None:  # type: ignore
                kwargs["le"] = max_value

    field_info = Field(**kwargs)

    # We need a marker to instruct the model to save extra attributes for this field.
    # The only available argument in the original `Field` signature is `json_schema_extra`,
    #  but that isn't good to use because it would be included in the json schema.
    # The private `_attributes_set` is in `__slots__` and we can "abuse" to store extra markers
    #  on the `FieldInfo` instance for later use.
    # `_Unset` and `None` ought to be handled separately due to the "real" value
    #  of `PydanticUndefined` being loaded from `pydantic_core` at runtime.
    if unit is not _Unset and unit is not None:
        field_info._attributes_set["unit"] = unit

    return field_info


def is_identifier(value: str) -> str:
    """Pydantic validator for names that are valid identifiers."""
    if not value.isidentifier():
        raise ValueError(f"{value} is not a valid identifier")
    return value


class _SerializableBaseModel(BaseModel):
    """
    Mixin class that enables dict, JSON and YAML serialization and deserialization
    by attaching `to_` and `from_` helper methods.
    """

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """Register every new subclass of the attached base model with the YAML handler."""
        register_model(cls, yaml)

    def to_dict(self) -> dict[str, Any]:
        """Alias for `BaseModel.model_dump`."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Alias for `BaseModel.model_validate`."""
        return cls.model_validate(data)

    def to_json(self, indent: int | None = None) -> str:
        """Alias for `BaseModel.model_dump_json`."""
        return self.model_dump_json(indent=indent)

    @classmethod
    def from_json(cls, json_data: str) -> Self:
        """Alias for `BaseModel.model_validate_json`."""
        return cls.model_validate_json(json_data)

    def _generate_file_name(self, path: str | None, add_timestamp: bool, extension: str) -> str:
        """Generate a file name to be used by `to_*_file` methods."""
        if path is None:
            path = str(OutputDirectoryManager.get_datadir())

        name = getattr(self, "name", self.__class__.__name__.lower())

        if add_timestamp:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S_%Z")
            filename = os.path.join(path, f"{name}_{timestamp}.{extension}")
        else:
            filename = os.path.join(path, f"{name}.{extension}")

        return filename

    def to_json_file(
        self,
        path: str | None = None,
        add_timestamp: bool = True,
    ) -> str:
        """Convert the object's data structure to a JSON string and store it in a file."""
        filename = self._generate_file_name(path, add_timestamp, "json")

        with open(filename, "w") as file:
            file.write(self.to_json())

        return filename

    @classmethod
    def from_json_file(cls, filename: str | Path) -> Self:
        """Read JSON data from a file and convert it to an instance of the attached class."""
        with open(filename) as file:
            deserialized_obj = cls.from_json(file.read())
        return deserialized_obj

    def to_yaml(self) -> str:
        """
        Convert the object's data structure to a YAML string.

        For performance reasons, to save to file use :meth:`~to_yaml_file` instead.
        """
        warnings.warn(
            "`to_yaml` is slow and should only be used for testing purposes.",
            category=ResourceWarning,
        )

        stream = StringIO()
        yaml.dump(self, stream)
        return stream.getvalue()

    @classmethod
    def from_yaml(cls, yaml_data: str) -> Self:
        """
        Convert YAML data to an instance of the attached class.

        For performance reasons, to load from file use :meth:`~from_yaml_file` instead.
        """
        warnings.warn(
            "`from_yaml` is slow and should only be used for testing purposes.",
            category=ResourceWarning,
        )

        return yaml.load(StringIO(yaml_data))

    def to_yaml_file(
        self,
        path: str | None = None,
        add_timestamp: bool = True,
    ) -> str:
        """Convert the object's data structure to a YAML string and store it in a file."""
        filename = self._generate_file_name(path, add_timestamp, "yaml")

        with open(filename, "w") as file:
            yaml.dump(self, file)

        return filename

    @classmethod
    def from_yaml_file(cls, filename: str | Path) -> Self:
        """Read YAML data from a file and convert it to an instance of the attached class."""
        # TODO: This is actually a generic loader and will return anything that is registered,
        #  not just instances of the present class. Perhaps it would be sensible to introduce
        #  a check when a user loads something that isn't at least a subclass of what they're
        #  expecting to deserialize.
        with open(filename) as file:
            deserialized_obj = yaml.load(file)
        return deserialized_obj


class SchedulerBaseModel(_SerializableBaseModel):
    """Pydantic base model to support qcodes-style instrument and parameter definitions."""

    model_config = ConfigDict(
        allow_inf_nan=False,  # disallow infinity and NaN values for floats
        extra="forbid",  # disallow unspecified fields
        ser_json_inf_nan="constants",  # serialize math.nan as NaN
        strict=True,  # enforce strict typing
        use_enum_values=True,  # uses values to serialize StrEnum
        validate_assignment=True,  # validate when attributes change
    )

    name: Annotated[str, AfterValidator(is_identifier)] = Field(kw_only=False)

    def __init__(self, /, name: str, **data: Any) -> None:
        """
        Allow the name to be passed to models as a positional argument.

        TODO: Achieve this in a way that appeases type checkers.
        """
        data["name"] = name
        super().__init__(**data)

    def __getstate__(self) -> dict[str, Any]:
        """
        Get the state of this model (used for YAML serialization).

        We don't invoke :meth:`~BaseModel.model_dump` to because it automatically serializes
        all the submodules contained within, while we want to let `ruamel.yaml` handle
        recursion instead to attach the appropriate YAML tags.
        """
        return dict(self)

    @property
    def parameters(self) -> dict[str, Any]:
        """Mapping of parameters of this element."""
        return {
            field_name: field_value
            for field_name, field_value in self
            if field_name != "name" and not isinstance(field_value, SchedulerSubmodule)
        }

    @property
    def submodules(self) -> dict[str, Any]:
        """Mapping of submodules of this element."""
        return {
            field_name: field_value
            for field_name, field_value in self
            if isinstance(field_value, SchedulerSubmodule)
        }

    @classmethod
    def get_unit(cls, field_name: str) -> str | None:
        """Get the unit declared for a certain field/parameter."""
        try:
            # Need to explicitly cast to string for pyright
            unit = cls.model_fields[field_name]._attributes_set.get("unit")
            return str(unit) if unit else None
        except KeyError:
            raise AttributeError(f"{cls.__name__!r} has no parameter {field_name!r}") from None

    @model_validator(mode="before")
    @classmethod
    def create_submodule_instances(cls, data: Any) -> Any:
        """During model instantiation, create an empty/default instance of all submodules."""
        if isinstance(data, dict):
            for field_name, field_info in cls.model_fields.items():
                if (
                    field_name not in data
                    and isclass(field_info.annotation)
                    and issubclass(field_info.annotation, SchedulerSubmodule)
                ):
                    data[field_name] = TypeAdapter(field_info.annotation).validate_python(
                        {"name": field_name}
                    )
        return data

    @model_validator(mode="after")
    def fill_submodule_parent_defaults(self) -> Self:
        """
        After module creation, for each submodule, fill in the default values for fields
        that read from an attribute of the parent model.
        """
        for field_name, field_value in self:
            if field_name == "parent":
                continue
            if isinstance(field_value, SchedulerSubmodule):
                field_value.parent = self
                if callable(fn := getattr(field_value, "_fill_defaults", None)):
                    fn()
        return self

    def close(self) -> None:
        """Does nothing."""
        warnings.warn(
            f"{self.__class__.__name__} is not an instrument, no need to close it!", stacklevel=2
        )

    @classmethod
    def close_all(cls) -> None:
        """Does nothing."""
        warnings.warn(f"{cls.__name__} is not an instrument, no need to close it!", stacklevel=2)


class SchedulerSubmodule(SchedulerBaseModel):
    """Compatibility class emulating the behaviour of ``InstrumentModule``/``InstrumentChannel``."""

    _parent: SchedulerBaseModel | SchedulerSubmodule | None = PrivateAttr(default=None)

    def __init__(
        self, /, name: str, *, parent: SchedulerBaseModel | None = None, **data: Any
    ) -> None:
        self._parent = parent
        super().__init__(name=name, **data)

    @property
    def parent(self) -> SchedulerBaseModel | None:  # noqa: D102
        return self._parent

    @parent.setter
    def parent(self, value: SchedulerBaseModel | None) -> None:
        self._parent = value

    def __eq__(self, other: Any) -> bool:
        """
        Set both `_parent` attributes of the models being compared to a common value
        before testing for equality to prevent `RecursionError`.

        This is an unfortunate quirk in the behaviour of Pydantic's own `__eq__` method,
        which does a "quick" tests by asserting equality between the `__dict__` attributes
        of `self` and `other`. The problem with this is that there is no way to hide
        the `_parent` attribute, which then ends up being compared and blow up recursively
        as its own submodules are in turn compared.
        """
        if isinstance(other, SchedulerSubmodule):
            self_parent_bak = self._parent
            other_parent_bak = other._parent

            self._parent = other._parent = ...  # type: ignore
            is_eq = super().__eq__(other)

            self._parent = self_parent_bak
            other._parent = other_parent_bak

            return is_eq

        return super().__eq__(other)

    def __hash__(self) -> int:
        """Hash the model by hashing the parent and the name."""
        return hash((self._parent, self.name))


# TODO: Merge with `SchedulerBaseModel`
class DataStructure(_SerializableBaseModel):
    """
    A parent for all data structures.

    Data attributes are generated from the class' type annotations, similarly to
    `dataclasses <https://docs.python.org/3/library/dataclasses.html>`_. If data
    attributes are JSON-serializable, data structure can be serialized using
    ``json()`` method. This string can be deserialized using ``parse_raw()`` classmethod
    of a correspondent child class.

    If required, data fields can be validated, see examples for more information.
    It is also possible to define custom field types with advanced validation.

    This class is a pre-configured `pydantic <https://docs.pydantic.dev/>`_
    model. See its documentation for details of usage information.

    .. admonition:: Examples
        :class: dropdown

        .. include:: /examples/structure.DataStructure.rst
    """

    model_config = ConfigDict(
        extra="forbid",
        # ensures exceptions are raised when passing extra argument that are not
        # part of a model when initializing.
        validate_assignment=True,
        # run validation when assigning attributes
    )


def deserialize_function(fun: str) -> Callable[..., Any]:
    """
    Import a python function from a dotted import string (e.g.,
    "qblox_scheduler.structure.model.deserialize_function").

    Parameters
    ----------
    fun : str
        A dotted import path to a function (e.g.,
        "qblox_scheduler.waveforms.square"), or a function pointer.

    Returns
    -------
    Callable[[Any], Any]


    Raises
    ------
    ValueError
        Raised if the function cannot be imported from path in the string.

    """
    try:
        return import_python_object_from_string(fun)
    except ImportError as exc:
        raise ValueError(f"{fun} is not a valid path to a known function.") from exc


def deserialize_class(cls: str) -> type:
    """
    Import a python class from a dotted import string (e.g.,
    "qblox_scheduler.structure.model.DataStructure").

    Parameters
    ----------
    cls : str
        A dotted import path to a class (e.g.,
        "qblox_scheduler.structure.model.DataStructure"), or a class pointer.

    Returns
    -------
    :
        The type you are trying to import.

    Raises
    ------
    ValueError
        Raised if the class cannot be imported from path in the string.

    """
    try:
        return import_python_object_from_string(cls)
    except ImportError as exc:
        raise ValueError(f"{cls} is not a valid path to a known class.") from exc
