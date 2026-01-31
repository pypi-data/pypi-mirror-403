# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Module containing the QuantumDevice object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar
from typing_extensions import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ModelWrapValidatorHandler,
    PositiveInt,
    TypeAdapter,
    field_validator,
    model_validator,
)
from qcodes.instrument import Instrument, find_or_create_instrument

from qblox_scheduler.backends.graph_compilation import (
    DeviceCompilationConfig,
    SerialCompilationConfig,
)
from qblox_scheduler.backends.qblox.exceptions import InvalidQuantumDeviceConfigurationError
from qblox_scheduler.backends.qblox_backend import QbloxHardwareCompilationConfig
from qblox_scheduler.backends.types.common import HardwareCompilationConfig
from qblox_scheduler.device_under_test.device_element import DeviceElement
from qblox_scheduler.device_under_test.edge import Edge
from qblox_scheduler.enums import SchedulingStrategy
from qblox_scheduler.helpers.importers import (
    import_python_object_from_string,
)
from qblox_scheduler.instrument_coordinator import InstrumentCoordinator
from qblox_scheduler.structure.model import SchedulerBaseModel

if TYPE_CHECKING:
    from pathlib import Path

ConcreteDeviceElement = TypeVar("ConcreteDeviceElement", bound=DeviceElement)
ConcreteEdge = TypeVar("ConcreteEdge", bound=Edge)


class QuantumDevice(SchedulerBaseModel):
    """
    The QuantumDevice directly represents the device under test (DUT).

    This contains a description of the connectivity to the control hardware as
    well as parameters specifying quantities like cross talk, attenuation and
    calibrated cable-delays. The QuantumDevice also contains references to
    individual DeviceElements, representations of elements on a device (e.g, a
    transmon qubit) containing the (calibrated) control-pulse parameters.

    This object can be used to generate configuration files for the compilation step
    from the gate-level to the pulse level description.
    These configuration files should be compatible with the
    :meth:`~qblox_scheduler.backends.graph_compilation.ScheduleCompiler.compile`
    function.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # to accept InstrumentCoordinator
    )

    elements: dict[str, ConcreteDeviceElement] = Field(  # type: ignore[reportGeneralTypeIssues]
        default_factory=dict,
        description="A list containing all elements that are located on this QuantumDevice.",
    )

    edges: dict[str, ConcreteEdge] = Field(  # type: ignore[reportGeneralTypeIssues]
        default_factory=dict,
        description=(
            "A list containing all the edges which connect the DeviceElements "
            "within this QuantumDevice."
        ),
    )

    instr_instrument_coordinator: InstrumentCoordinator | None = Field(
        default=None,
        description="A reference to the instrument_coordinator instrument.",
        exclude=True,
    )

    cfg_sched_repetitions: PositiveInt = Field(
        default=1024,
        description=(
            "The number of times execution of the schedule gets repeated when "
            "performing experiments, i.e. used to set the repetitions attribute of "
            "the TimeableSchedule objects generated."
        ),
    )

    keep_original_schedule: bool = Field(
        default=True,
        description=(
            "If `True`, the compiler will not modify the schedule argument. "
            "If `False`, the compilation modifies the schedule, thereby "
            "making the original schedule unusable for further usage; this "
            "improves compilation time. Warning: if `False`, the returned schedule "
            "references objects from the original schedule, please refrain from modifying "
            "the original schedule after compilation in this case!"
        ),
    )

    if TYPE_CHECKING:
        # This is needed to address the fact that we often assign a dict to `hardware_config`
        # which is automatically deserialized by Pydantic into the proper `HardwareConfig`
        # at runtime; however, pyright doesn't know this and complains that the attribute
        # cannot be a dict.
        # We don't *actually* want dicts to be allowed as values, hence the branching
        # with TYPE_CHECKING to appease the type checker.
        hardware_config: HardwareCompilationConfig | dict | None = None
    else:
        hardware_config: QbloxHardwareCompilationConfig | None = Field(
            default=None,
            discriminator="config_type",
        )
    """
    The input dictionary used to generate a valid HardwareCompilationConfig using
    :meth:`~.generate_hardware_compilation_config`.
    This configures the compilation from the quantum-device layer to the control-hardware layer.

    Useful methods to write and reload the configuration from a json file are
    :meth:`~.HardwareConfig.load_from_json_file` and
    :meth:`~.HardwareConfig.write_to_json_file`.
    """

    scheduling_strategy: SchedulingStrategy = Field(
        default=SchedulingStrategy.ASAP,
        description="Scheduling strategy used to calculate absolute timing.",
    )

    def __getstate__(self) -> dict[str, Any]:
        """
        Get the state of :class:`~QuantumDevice` (used for YAML serialization).

        We need to skip `instr_instrument_coordinator`.
        """
        return {
            field_name: field_value
            for field_name, field_value in iter(self)
            if field_name != "instr_instrument_coordinator"
        }

    def __deepcopy__(self, memo: dict[int, Any] | None = None) -> QuantumDevice:
        """Override deepcopy to not copy instr_instrument_coordinator."""
        instr_coord = self.instr_instrument_coordinator
        self.instr_instrument_coordinator = None
        deepcopied = super().__deepcopy__(memo)
        deepcopied.instr_instrument_coordinator = instr_coord
        self.instr_instrument_coordinator = instr_coord
        return deepcopied

    @field_validator("instr_instrument_coordinator", mode="before")
    @classmethod
    def validate_instrument_coordinator(
        cls, value: str | InstrumentCoordinator | None
    ) -> Instrument | None:
        """
        Load InstrumentCoordinator instance from its name.

        Pydantic doesn't know how to handle a QCoDeS instrument; thus, we have to allow
        arbitrary types and manually fetch them with `find_or_create_instrument`.
        """
        match value:
            case str():
                return find_or_create_instrument(InstrumentCoordinator, "ic")
            case InstrumentCoordinator():
                return value
            case None:
                return None
        raise ValueError("expected an InstrumentCoordinator instance or its name.")

    @field_validator("scheduling_strategy")
    @classmethod
    def validate_scheduling_strategy(cls, value: str | SchedulingStrategy) -> SchedulingStrategy:
        """Force `scheduling_strategy` into its proper enum value."""
        return SchedulingStrategy(value)

    @model_validator(mode="wrap")
    @classmethod
    def validate_elements_and_edges(
        cls,
        data: Any,  # noqa: ANN401
        handler: ModelWrapValidatorHandler[Self],
    ) -> Self:
        """
        Add elements and edges to the model by calling `add_element` and `add_edge`
        respectively to force our consistency checks.
        """
        if isinstance(data, cls):
            return handler(data)

        elements = data.pop("elements", {})
        edges = data.pop("edges", {})
        # Invoking the handler will cause this method to be called again, but it seems like
        # it's expected behaviour with wrap model validators. The nested call won't receive
        # any edges, and thus the for loop below will be skipped.
        model = handler(data)
        ta_element = TypeAdapter(ConcreteDeviceElement)
        ta_edge = TypeAdapter(ConcreteEdge)

        for element_data in elements.values():
            element = ta_element.validate_python(element_data)
            model.add_element(element)
        for edge_data in edges.values():
            edge = ta_edge.validate_python(edge_data)
            model.add_edge(edge)

        return model

    def generate_compilation_config(self) -> SerialCompilationConfig:
        """Generate a config for use with a :class:`~.graph_compilation.ScheduleCompiler`."""
        return SerialCompilationConfig(
            name="QuantumDevice-generated SerialCompilationConfig",
            keep_original_schedule=self.keep_original_schedule,
            device_compilation_config=self.generate_device_config(),
            hardware_compilation_config=self.generate_hardware_compilation_config(),
        )

    def generate_hardware_config(self) -> dict[str, Any]:
        """
        Generate a valid hardware configuration describing the quantum device.

        Returns
        -------
            The hardware configuration file used for compiling from the quantum-device
            layer to a hardware backend.

        .. warning:

            The config currently has to be specified by the user using the
            :code:`hardware_config` parameter.

        """
        return (
            # Exclude `compilation_passes` and other fields bloating the output
            self.hardware_config.model_dump(exclude_unset=True)
            if isinstance(self.hardware_config, BaseModel)
            else {}
        )

    def generate_device_config(self) -> DeviceCompilationConfig:
        """
        Generate a device config.

        This config is used to compile from the quantum-circuit to the
        quantum-device layer.
        """
        clocks = {}
        elements_cfg = {}
        edges_cfg = {}

        # iterate over the elements on the device
        for element in self.elements.values():
            element_cfg = element.generate_device_config()
            clocks.update(element_cfg.clocks)
            elements_cfg.update(element_cfg.elements)

        # iterate over the edges on the device
        for edge in self.edges.values():
            edge_cfg = edge.generate_edge_config()
            edges_cfg.update(edge_cfg)

        # Ignore pyright because of a bug (the error is in the DeviceCompilationConfig class)
        device_config = DeviceCompilationConfig(  # type: ignore
            elements=elements_cfg,
            clocks=clocks,
            edges=edges_cfg,
            scheduling_strategy=self.scheduling_strategy,
        )

        return device_config

    def generate_hardware_compilation_config(self) -> HardwareCompilationConfig | None:
        """
        Generate a hardware compilation config.

        The compilation config is used to compile from the quantum-device to the
        control-hardware layer.
        """
        hardware_config = self.hardware_config
        if hardware_config is None:
            return None
        elif isinstance(hardware_config, HardwareCompilationConfig):
            # Hardware config is already a valid HardwareCompilationConfig DataStructure
            return hardware_config
        else:
            # Parse a (backend-specific) HardwareCompilationConfig
            if "backend" in hardware_config:
                raise ValueError(
                    f"`{HardwareCompilationConfig.__name__}` no longer takes a"
                    f" 'backend' field; instead, specify the 'config_type', which should"
                    " contain a string reference to the backend-specific datastructure"
                    " that should be parsed."
                )
            hardware_compilation_config_model = hardware_config["config_type"]
            if isinstance(hardware_compilation_config_model, str):
                hardware_compilation_config_model = import_python_object_from_string(
                    hardware_compilation_config_model
                )
            hardware_compilation_config = hardware_compilation_config_model.model_validate(
                hardware_config
            )

        return hardware_compilation_config

    def get_element(self, name: str) -> DeviceElement:
        """
        Return a :class:`~qblox_scheduler.device_under_test.device_element.DeviceElement`
        by name.

        Parameters
        ----------
        name
            The element name.

        Returns
        -------
        :
            The element.

        Raises
        ------
        KeyError
            If key ``name`` is not present in `self.elements`.

        """
        try:
            return self.elements[name]
        except KeyError:
            raise KeyError(f"'{name}' is not an element of {self.name}.") from None

    def add_element(
        self,
        element: DeviceElement,
    ) -> None:
        """
        Add an element to the elements collection.

        Parameters
        ----------
        element
            The element to add.

        Raises
        ------
        ValueError
            If an element with a duplicated name is added to the collection.
        TypeError
            If :code:`element` is not an instance of the base element.

        """
        if not isinstance(element, DeviceElement):
            raise TypeError(f"{element!r} is not a DeviceElement.")

        if element.name in self.elements:
            raise ValueError(f"'{element.name}' has already been added.")

        self.elements[element.name] = element

    def remove_element(self, name: str) -> None:
        """
        Removes an element by name.

        Parameters
        ----------
        name
            The element name.
            Has to follow the convention ``"{element_0}_{element_1}"``.

        """
        try:
            del self.elements[name]
        except KeyError:
            raise KeyError(f"'{name}' is not an element of {self.name}.") from None

    def get_edge(self, name: str) -> Edge:
        """
        Returns an edge by name.

        Parameters
        ----------
        name
            The edge name.
            Has to follow the convention ``"{element_0}_{element_1}"``.

        Returns
        -------
        :
            The edge.

        Raises
        ------
        KeyError
            If key ``name`` is not present in ``self.edges``.

        """
        try:
            return self.edges[name]
        except KeyError:
            raise KeyError(f"'{name}' is not an edge of {self.name}.") from None

    def add_edge(self, edge: Edge) -> None:
        """
        Add the edges.

        Parameters
        ----------
        edge
            The edge to add.

        """
        if not isinstance(edge, Edge):
            raise TypeError(f"{edge!r} is not an Edge")

        if edge.name in self.edges:
            raise ValueError(f"'{edge.name}' has already been added")

        for element_name in (edge.parent_element_name, edge.child_element_name):
            if element_name not in self.elements:
                raise ValueError(f"'{element_name}' is not an element of {self.name}.")

        for bound_element in (edge.parent_element, edge.child_element):
            if bound_element is not None and id(bound_element) != id(
                self.elements[bound_element.name]
            ):
                raise ValueError(
                    f"A different element with name {bound_element.name} "
                    f"is already present in {self.name}."
                )

        if edge.parent_element is None:
            edge._parent_device_element = self.elements[edge.parent_element_name]
        if edge.child_element is None:
            edge._child_device_element = self.elements[edge.child_element_name]

        self.edges[edge.name] = edge

    def remove_edge(self, name: str) -> None:
        """
        Remove an edge by name.

        Parameters
        ----------
        name
            The edge name connecting the elements.
            Has to follow the convention ``"{element_0}_{element_1}"``.

        """
        try:
            del self.edges[name]
        except KeyError:
            raise KeyError(f"'{name}' is not an edge of {self.name}.") from None

    @classmethod
    def from_json_file(cls, filename: str | Path) -> Self:
        """Read JSON data from a file and convert it to an instance of the attached class."""
        with open(filename) as file:
            text = file.read()

        # the json format of QuantumDevice has changed from quantify to qblox, where before
        # we had e.g. the line
        # "deserialization_type": "quantify_scheduler.device_under_test...
        # the current format does not have this key.
        if "deserialization_type" in text:
            raise InvalidQuantumDeviceConfigurationError(
                "If passing an old quantify_scheduler configuration, "
                "try converting it to a qblox_scheduler configuration using \n"
                "our migration helper tool after installing qblox-scheduler[cli]:\n"
                f"    qblox-scheduler convert-configs {filename}\n"
            )
        return cls.from_json(text)
