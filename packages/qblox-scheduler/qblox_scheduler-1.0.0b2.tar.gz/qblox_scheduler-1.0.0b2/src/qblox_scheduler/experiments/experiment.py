# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2025, Qblox B.V.
"""Module containing the core experiment concepts."""

from __future__ import annotations

import inspect
import logging
from abc import ABC, abstractmethod
from collections import UserDict
from copy import copy, deepcopy
from enum import Enum
from typing import TYPE_CHECKING

from xarray import Dataset

from qblox_scheduler.helpers.collections import make_hash
from qblox_scheduler.helpers.importers import export_python_object_to_path_string
from qblox_scheduler.instrument_coordinator.utility import merge_acquisition_sets
from qblox_scheduler.json_utils import (
    JSONSchemaValMixin,
    JSONSerializable,
)
from qblox_scheduler.operations.expressions import DType, substitute_value_in_arbitrary_container
from qblox_scheduler.operations.variables import Variable

if TYPE_CHECKING:
    from typing import Any

    from qblox_scheduler.device_under_test import QuantumDevice
    from qblox_scheduler.operations.expressions import Expression

logger = logging.getLogger(__name__)


class Step(JSONSchemaValMixin, UserDict, ABC):
    """
    A step containing a single (possibly) near-time operation to be performed in an experiment.

    An `Experiment` consists of steps, each of which performs a specific operation
    (usually on hardware). There is no real-time guarantee between steps, as opposed to `Operation`.
    """

    schema_filename = "step.json"
    _class_signature = None

    def __init__(self, name: str) -> None:
        super().__init__()

        # ensure keys exist
        self.data["name"] = name
        self.data["schedule_info"] = {}
        self.data["parameter_info"] = {}
        self.data["hardware_option_info"] = {}
        self.data["hardware_description_field_info"] = {}

    def __eq__(self, other: object) -> bool:
        """
        Returns the equality of two instances based on its hash.

        Parameters
        ----------
        other
            The other operation to compare to.

        Returns
        -------
        :

        """
        return hash(self) == hash(other)

    def __str__(self) -> str:
        """
        Returns a unique, evaluable string for unchanged data.

        Returns a concise string representation which can be evaluated into a new
        instance using :code:`eval(str(operation))` only when the data dictionary has
        not been modified.

        This representation is guaranteed to be unique.
        """
        return f"{self.__class__.__name__}(name='{self.name}')"

    def __getstate__(self) -> dict[str, object]:
        return {
            "deserialization_type": export_python_object_to_path_string(self.__class__),
            "data": self.data,
        }

    def __setstate__(self, state: dict[str, dict]) -> None:
        self.data = state["data"]
        self._update()

    def __hash__(self) -> int:
        return make_hash(self.data)

    def _update(self) -> None:
        """Update the Step's internals."""
        pass

    def clone(self) -> Step:
        """Clone this operation into a new independent operation."""
        state = self.__getstate__()
        state["data"] = deepcopy(state["data"])
        new_self = self.copy()
        # convincing the type checker of the accuracy of an arbitrary dict is difficult
        new_self.__setstate__(state)  # type: ignore
        return new_self

    def substitute(
        self, substitutions: dict[Expression, Expression | int | float | complex]
    ) -> Step:
        """Substitute matching expressions in operand, possibly evaluating a result."""
        state = self.__getstate__()
        state["data"], changed = substitute_value_in_arbitrary_container(
            state["data"],  # type: ignore
            substitutions,
        )

        if changed:
            new_self = self.copy()
            # convincing the type checker of the accuracy of an arbitrary dict is difficult
            new_self.__setstate__(state)  # type: ignore
            return new_self
        else:
            return self

    @property
    def name(self) -> str:
        """Return the name of the step."""
        return self.data["name"]

    @classmethod
    def _get_signature(cls, parameters: dict) -> str:
        """
        Returns the constructor call signature of this instance for serialization.

        The string constructor representation can be used to recreate the object
        using eval(signature).

        Parameters
        ----------
        parameters : dict
            The current data dictionary.

        Returns
        -------
        :

        """
        if cls._class_signature is None:
            logger.info("Caching signature for class %s", cls.__name__)
            cls._class_signature = inspect.signature(cls)
        signature = cls._class_signature

        def to_kwarg(key: str) -> str:
            """
            Returns a key-value pair in string format of a keyword argument.

            Parameters
            ----------
            key
                The parameter key

            Returns
            -------
            :

            """
            value = parameters[key]
            if isinstance(value, Enum):
                enum_value = value.value
                value = enum_value
            value = f"'{value}'" if isinstance(value, str) else value
            return f"{key}={value}"

        required_params = list(signature.parameters.keys())
        kwargs_list = map(to_kwarg, required_params)

        return f"{cls.__name__}({','.join(kwargs_list)})"

    @abstractmethod
    def run(self, device: QuantumDevice, timeout: int) -> Dataset | None:
        """Execute step on quantum device."""
        ...


class Experiment(JSONSchemaValMixin, JSONSerializable, UserDict):
    """An experiment."""

    schema_filename = "experiment.json"

    def __init__(self, name: str, data: dict[str, Any] | None = None) -> None:
        super().__init__()

        # ensure keys exist
        self.data["name"] = name
        self.data["steps"] = []
        self.data["variables"] = {}
        if data is not None:
            self.data.update(data)

    def __getstate__(self) -> dict[str, Any]:
        data = copy(self.data)
        return {
            "deserialization_type": export_python_object_to_path_string(self.__class__),
            "data": data,
        }

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.data = state["data"]

    @property
    def name(self) -> str:
        """Return the name of the experiment."""
        return self.data["name"]

    @property
    def steps(self) -> list[Step]:
        """Return the steps in the experiment."""
        return self.data["steps"]

    def declare(self, dtype: DType) -> Variable:
        """
        Declare a variable.

        Parameters
        ----------
        dtype
            The variable type.

        """
        var = Variable(dtype)
        self.define(var)
        return var

    def define(self, var: Variable) -> None:
        """
        Add a declared variable.

        Parameters
        ----------
        var
            The variable.

        """
        self.data["variables"][var.id_] = var

    def add(self, step: Step) -> None:
        """Add step to experiment."""
        self.steps.append(step)

    def run(
        self,
        device: QuantumDevice,
        timeout: int = 10,
    ) -> Dataset:
        """Run experiment on quantum device."""
        # Steps may modify the configuration. This should not be persistent so we copy the state.
        device = device.model_copy(deep=True)

        data_set = Dataset()
        for step in self.steps:
            step_data_set = step.run(device, timeout=timeout)
            if step_data_set is not None:
                data_set = merge_acquisition_sets(data_set, step_data_set)
        return data_set

    def clone(self) -> Experiment:
        """Clone this schedule into a separate independent experiment."""
        new_data = deepcopy(self.data)
        return self.__class__(self.name, new_data)

    def substitute(
        self, substitutions: dict[Expression, Expression | int | float | complex]
    ) -> Experiment:
        """Substitute matching expressions in this experiment."""
        changed = False

        new_steps = []
        for step in self.steps:
            new_step = step.substitute(substitutions)
            if new_step is not step:
                changed = True
            else:
                new_step = step.clone()
            new_steps.append(new_step)

        if changed:
            new_experiment = self.clone()
            new_experiment.data["steps"] = new_steps
            return new_experiment
        else:
            return self
