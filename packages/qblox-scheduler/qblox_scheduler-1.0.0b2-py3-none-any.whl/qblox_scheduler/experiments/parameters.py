# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2025, Qblox B.V.
"""Module containing the step to a set a parameter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel
from qcodes.parameters import Parameter

from qblox_scheduler.experiments.experiment import Step

if TYPE_CHECKING:
    from qblox_scheduler.device_under_test import QuantumDevice


class UndefinedParameterError(LookupError):
    """Raised when a parameter was not previously defined."""

    def __init__(self, operation_name: str, parameter_type: str) -> None:
        super().__init__(
            f"Error in '{operation_name}': there is no existing entry for this {parameter_type}. "
            "Use `create_new=True` if this is intentional."
        )


def _resolve_path(
    target: BaseModel | dict,
    path: list[str | int],
    value: Any,  # noqa: ANN401
) -> tuple[BaseModel | dict, str | int, Any]:
    for i, field in enumerate(path[:-1]):
        new_target = getattr(target, str(field)) if isinstance(target, BaseModel) else target[field]
        if new_target is None:
            # From here on, the fields are not defined. Turn the rest of the path into a
            # nested dictionary.
            return (target, field, _path_to_dict(path[-1], path[i + 1 : -1], value))
        target = new_target
    return (target, path[-1], value)


def _path_to_dict(target: str | int, path: list[str | int], value: Any) -> dict[str | int, Any]:  # noqa: ANN401
    out_dict = {target: value}
    for field in reversed(path):
        out_dict = {field: out_dict}
    return out_dict


def _set_value_checked(target: BaseModel | dict, key: Any, value: Any, create_new: bool) -> None:  # noqa: ANN401
    if isinstance(target, BaseModel):
        if not create_new:
            # Check for existence and raise error if not.
            _ = getattr(target, str(key))
        setattr(target, str(key), value)
    else:
        if not create_new:
            # Check for existence and raise error if not.
            _ = target[key]
        target[key] = value


class SetParameter(Step):
    """
    Experiment step that sets a QCoDeS parameter, or device element parameter.

    Examples
    --------
    Set a QCoDeS parameter:

    .. code-block:: python

        dc_offset = agent.get_clusters()["cluster0"].module4.out0_offset

        schedule = Schedule("resonator flux spectroscopy")
        with schedule.loop(linspace(0, 0.5, 30, DType.NUMBER)) as offset:
            schedule.add(SetParameter(dc_offset, offset))
            with schedule.loop(linspace(360e6, 380e6, 300, DType.FREQUENCY)) as freq:
                schedule.add(Reset("q0"))
                schedule.add(
                    Measure("q0", freq=freq, coords={"frequency": freq, "dc_offset": offset})
                )
                schedule.add(IdlePulse(4e-9))

    Set a device element parameter:

    .. code-block:: python

        schedule = Schedule("hello")
        with schedule.loop(linspace(0, 0.5, 3, DType.AMPLITUDE)) as amp:
            # corresponds to q0.measure.pulse_amp = amp
            schedule.add(SetParameter(("measure", "pulse_amp"), amp, element="q0"))
            schedule.add(Reset("q0"))
            schedule.add(
                Measure("q0", coords={"frequency": freq, "pulse_amp": amp})
            )


    Parameters
    ----------
    name:
        One of:

        - QCoDeS parameter
        - a str, corresponding to a parameter on the quantum device.
        - a tuple of str, corresponding to a nested parameter on the
          quantum device or device element or edge.
    value:
        Value to set the parameter to.
    element:
        Optional. If provided, the parameter is set on the device element with the given name.
    create_new:
        If True, create a new entry in the device configuration if no entry
        exists for this port-clock and hardware option. Otherwise, raise an
        error if the entry does not exist. Optional, by default False.

    """

    def __init__(
        self,
        name: Parameter | str | int | tuple[str | int, ...],
        value: Any,  # noqa: ANN401
        element: str | None = None,
        create_new: bool = False,
    ) -> None:
        if isinstance(name, Parameter):
            parameter = name
            friendly_name = f"{name.instrument.name + '.' if name.instrument else ''}{name.name}"
        else:
            parameter = [name] if isinstance(name, (str, int)) else list(name)
            friendly_name = ".".join(str(x) for x in parameter)
        if element is None:
            desc = f"set parameter {friendly_name} to {value}"
        else:
            desc = f"set parameter {friendly_name} to {value} on {element}"
        super().__init__(desc)
        self.data["parameter_info"] = {
            "element": element,
            "parameter": parameter,
            "value": value,
            "create_new": create_new,
        }

    @property
    def element(self) -> str | None:
        """Element to set QCoDeS parameter on."""
        return self.data["parameter_info"]["element"]

    @property
    def parameter(self) -> list[str | int] | Parameter:
        """QCoDeS parameter name to set."""
        return self.data["parameter_info"]["parameter"]

    @property
    def value(self) -> Any:  # noqa: ANN401
        """QCoDeS parameter value to set."""
        return self.data["parameter_info"]["value"]

    @property
    def create_new(self) -> bool:
        """Whether to create a new parameter if it did not previously exist."""
        return self.data["parameter_info"]["create_new"]

    def run(self, device: QuantumDevice, timeout: int = 10) -> None:  # noqa: ARG002
        """Execute step on quantum device."""
        parameter = self.parameter
        if isinstance(parameter, Parameter):
            parameter(self.value)
        else:
            element = self.element
            if element is not None:
                target, key, value = _resolve_path(device.elements[element], parameter, self.value)
            else:
                target, key, value = _resolve_path(device, parameter, self.value)
            try:
                _set_value_checked(target, key, value, self.create_new)
            except (AttributeError, KeyError) as err:
                raise UndefinedParameterError(self.name, "parameter") from err


class SetHardwareOption(Step):
    """
    Experiment step that sets a hardware option for a given port/clock.

    Example
    -------

    .. code-block:: python

        schedule = Schedule("resonator flux spectroscopy")
        with schedule.loop(linspace(36e6, 38e6, 300, DType.FREQUENCY)) as lo_freq:
            # corresponds to:
            #   hardware_config = device.generate_hardware_compilation_config()
            #   hardware_options = hardware_config.hardware_options
            #   hardware_options.modulation_frequencies["q0:mw-q0.f_larmor"].lo_freq = lo_freq
            schedule.add(
                SetHardwareOption(("modulation_frequencies", "lo_freq"), lo_freq, port="q0:mw-q0.f_larmor")
            )
            schedule.add(Measure("q0"))


    Parameters
    ----------
    name:
        One of:

        - a str, corresponding to a hardware option on the port/clock.
        - a tuple of str, corresponding to a nested hardware option on the
          port/clock
    value:
        Value to set the option to.
    port:
        Port/clock combination to set the option for.
    create_new:
        If True, create a new entry in the hardware configuration if no entry
        exists for this port-clock and hardware option. Otherwise, raise an
        error if the entry does not exist. Optional, by default False.

    """  # noqa: E501

    def __init__(
        self,
        name: str | int | tuple[str | int, ...],
        value: Any,  # noqa: ANN401
        port: str,
        create_new: bool = False,
    ) -> None:
        path = [name] if isinstance(name, (str, int)) else list(name)
        friendly_name = ".".join(str(x) for x in path)
        super().__init__(f"set hardware option {friendly_name} to {value} for port {port}")
        self.data["hardware_option_info"] = {
            "port": port,
            "path": path,
            "value": value,
            "create_new": create_new,
        }

    @property
    def port(self) -> str:
        """Port/clock combination to set option for."""
        return self.data["hardware_option_info"]["port"]

    @property
    def option(self) -> list[str | int]:
        """Option name to set."""
        return self.data["hardware_option_info"]["path"]

    @property
    def value(self) -> Any:  # noqa: ANN401
        """Option value to set."""
        return self.data["hardware_option_info"]["value"]

    @property
    def create_new(self) -> bool:
        """Whether to create a new configuration field if it did not previously exist."""
        return self.data["hardware_option_info"]["create_new"]

    def run(self, device: QuantumDevice, timeout: int = 10) -> None:  # noqa: ARG002
        """Execute step on quantum device."""
        hardware_config = device.generate_hardware_compilation_config()
        if hardware_config is None:
            raise RuntimeError("Quantum device does not have a compilation configuration")
        device.hardware_config = hardware_config

        option = self.option
        target = getattr(hardware_config.hardware_options, str(option[0]))
        key = self.port
        if option[1:]:
            target, key, value = _resolve_path(target[key], option[1:], self.value)
        elif target is None:
            if not self.create_new:
                raise UndefinedParameterError(self.name, "hardware option")
            target = hardware_config.hardware_options
            key = str(option[0])
            value = {key: self.value}
        else:
            value = self.value
        try:
            _set_value_checked(target, key, value, self.create_new)
        except (AttributeError, KeyError) as err:
            raise UndefinedParameterError(self.name, "hardware option") from err


class SetHardwareDescriptionField(Step):
    """
    Experiment step that sets a hardware description parameter for a given instrument.

    Example
    -------

    .. code-block:: python

        schedule = Schedule("test")
        # corresponds to:
        #   hardware_config = device.generate_hardware_compilation_config()
        #   cluster0_description = hardware_config.hardware_description["cluster0"]
        #   cluster0_description.modules[2].rf_output_on = False
        schedule.add(
            SetHardwareDescriptionField(("modules", 2, "rf_output_on"), False, instrument="cluster0")
        )
        schedule.add(Measure("q0"))


    Parameters
    ----------
    name:
        one of:

        - a str, corresponding to a hardware option on the port/clock.
        - a tuple of str, corresponding to a nested hardware option on the
          port/clock
    value:
        Value to set the parameter to.
    instrument:
        Instrument to set the parameter for.
    create_new:
        If True, create a new entry in the hardware configuration if no entry
        exists for this port-clock and hardware option. Otherwise, raise an
        error if the entry does not exist. Optional, by default False.

    """  # noqa: E501

    def __init__(
        self,
        name: str | int | tuple[str | int, ...],
        value: Any,  # noqa: ANN401
        instrument: str,
        create_new: bool = False,
    ) -> None:
        path = [name] if isinstance(name, (str, int)) else list(name)
        friendly_path = ".".join(str(x) for x in path)
        super().__init__(
            f"set hardware description field {friendly_path} to {value} for instrument {instrument}"
        )
        self.data["hardware_description_field_info"] = {
            "instrument": instrument,
            "path": path,
            "value": value,
            "create_new": create_new,
        }

    @property
    def instrument(self) -> str:
        """Instrument to set field for."""
        return self.data["hardware_description_field_info"]["instrument"]

    @property
    def field(self) -> list[str | int]:
        """Field path to set."""
        return self.data["hardware_description_field_info"]["path"]

    @property
    def value(self) -> Any:  # noqa: ANN401
        """Field value to set."""
        return self.data["hardware_description_field_info"]["value"]

    @property
    def create_new(self) -> bool:
        """Whether to create a new configuration field if it did not previously exist."""
        return self.data["hardware_description_field_info"]["create_new"]

    def run(self, device: QuantumDevice, timeout: int = 10) -> None:  # noqa: ARG002
        """Execute step on quantum device."""
        hardware_config = device.generate_hardware_compilation_config()
        if hardware_config is None:
            raise RuntimeError("Quantum device does not have a compilation configuration")
        device.hardware_config = hardware_config

        target, key, value = _resolve_path(
            hardware_config.hardware_description[self.instrument], self.field, self.value
        )
        try:
            _set_value_checked(target, key, value, self.create_new)
        except (AttributeError, KeyError) as err:
            raise UndefinedParameterError(self.name, "hardware description field") from err
