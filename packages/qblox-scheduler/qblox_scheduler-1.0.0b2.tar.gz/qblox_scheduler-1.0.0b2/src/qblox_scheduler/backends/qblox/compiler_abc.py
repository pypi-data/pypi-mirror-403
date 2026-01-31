# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Compiler base and utility classes for Qblox backend."""

from __future__ import annotations

import json
import logging
import warnings
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Hashable
from dataclasses import dataclass
from enum import Enum, auto
from os import makedirs, path
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Protocol,
    TypeVar,
)

from pathvalidate import sanitize_filename
from qcodes.utils.json_utils import NumpyJSONEncoder

from qblox_scheduler.analysis.data_handling import OutputDirectoryManager
from qblox_scheduler.backends.qblox import (
    constants,
    driver_version_check,
    helpers,
    q1asm_instructions,
    register_manager,
)
from qblox_scheduler.backends.qblox.operation_handling.acquisitions import (
    AcquisitionStrategyPartial,
)
from qblox_scheduler.backends.qblox.operation_handling.pulses import (
    DigitalOutputStrategy,
    GenericPulseStrategy,
    MarkerPulseStrategy,
)
from qblox_scheduler.backends.qblox.operation_handling.q1asm_injection_strategy import (
    Q1ASMInjectionStrategy,
)
from qblox_scheduler.backends.qblox.operation_handling.virtual import (
    ConditionalStrategy,
    ControlFlowReturnStrategy,
    LoopStrategy,
    UpdateParameterStrategy,
)
from qblox_scheduler.backends.qblox.qasm_program import QASMProgram
from qblox_scheduler.backends.qblox.qblox_acq_index_manager import (
    AcqFullyAppendLoopNode,
    FullyAppendAcqInfo,
    QbloxAcquisitionIndexManager,
    QbloxAcquisitionModuleResourceManager,
)
from qblox_scheduler.backends.types.common import ThresholdedTriggerCountMetadata
from qblox_scheduler.backends.types.qblox import (
    ClusterModuleDescription,
    OpInfo,
    SequencerSettings,
    StaticHardwareProperties,
    ThresholdedAcqTriggerReadSettings,
)
from qblox_scheduler.enums import BinMode
from qblox_scheduler.helpers.schedule import (
    _is_acquisition_binned_append,
    _is_acquisition_binned_average,
    _is_acquisition_binned_average_append,
)
from quantify_core.data.handling import gen_tuid

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from qblox_scheduler.backends.qblox.operation_handling.base import (
        IOperationStrategy,
    )
    from qblox_scheduler.backends.qblox_backend import (
        _ClusterCompilationConfig,
        _ClusterModuleCompilationConfig,
        _LocalOscillatorCompilationConfig,
        _SequencerCompilationConfig,
    )

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class InstrumentCompiler(ABC):
    """
    Abstract base class that defines a generic instrument compiler.

    The subclasses that inherit from this are meant to implement the compilation
    steps needed to compile the lists of
    :class:`~qblox_scheduler.backends.types.qblox.OpInfo` representing the
    pulse and acquisition information to device-specific instructions.

    Each device that needs to be part of the compilation process requires an
    associated ``InstrumentCompiler``.

    Parameters
    ----------
    name
        Name of the `QCoDeS` instrument this compiler object corresponds to.
    total_play_time
        Total time execution of the schedule should go on for. This parameter is
        used to ensure that the different devices, potentially with different clock
        rates, can work in a synchronized way when performing multiple executions of
        the schedule.
    instrument_cfg
        The compilation config referring to this device.

    """

    def __init__(
        self,
        name: str,
        total_play_time: float,
        instrument_cfg: (
            _ClusterModuleCompilationConfig
            | _ClusterCompilationConfig
            | _LocalOscillatorCompilationConfig
        ),
    ) -> None:
        self.name = name
        self.total_play_time = total_play_time
        self.instrument_cfg = instrument_cfg

    def prepare(self, **kwargs) -> None:  # noqa: B027 ("abstract" yet called by subclasses)
        """
        Method that can be overridden to implement logic before the main compilation
        starts. This step is to extract all settings for the devices that are dependent
        on settings of other devices. This step happens after instantiation of the
        compiler object but before the start of the main compilation.
        """

    @abstractmethod
    def compile(self, debug_mode: bool, repetitions: int) -> object:
        """
        An abstract method that should be overridden in a subclass to implement the
        actual compilation. It should turn the pulses and acquisitions added to the
        device into device-specific instructions.

        Parameters
        ----------
        debug_mode
            Debug mode can modify the compilation process,
            so that debugging of the compilation process is easier.
        repetitions
            Number of times execution of the schedule is repeated.

        Returns
        -------
        :
            A data structure representing the compiled program. The type is
            dependent on implementation.

        """


@dataclass
class _AcquisitionGroup:
    """Data to store for each acquisition group."""

    root: AcqFullyAppendLoopNode
    node: AcqFullyAppendLoopNode
    acq_strategies: list[IOperationStrategy]

    def _current_loop_bin_modes(self) -> list[BinMode | None]:
        loop_bin_modes: list[BinMode | None] = []
        current_node = self.node
        while current_node.parent is not None:
            loop_bin_modes.append(current_node.bin_mode)
            current_node = current_node.parent
        return loop_bin_modes[::-1]

    def is_compatible(self, loop_bin_modes: list[BinMode]) -> bool:
        """
        Checks whether an acquisition with the loop_bin_modes (the argument)
        is compatible with the group, if the acquisition was added to the current node.
        An acquisition is compatible with a group if for all loops in the group
        and for the acquisitions the same bin mode is applied.
        """
        this_group_loop_bin_modes = self._current_loop_bin_modes()
        # Consistency check whether
        # everything went well with previous compilation steps.
        assert len(loop_bin_modes) == len(this_group_loop_bin_modes)

        for this_group_loop_bin_mode, loop_bin_mode in zip(
            this_group_loop_bin_modes, loop_bin_modes, strict=False
        ):
            if (this_group_loop_bin_mode is not None) and (
                this_group_loop_bin_mode != loop_bin_mode
            ):
                return False
        return True

    def update_loop_bin_modes(self, loop_bin_modes: list[BinMode]) -> None:
        """
        Update the tree with the new loop bin modes.
        This is needed to be called, because when iterating the operations,
        we do not know beforehand which loops are using which bin modes,
        it is determined by the acquisition inside of them.
        So when we find a new acquisition, we update all loop bin modes in the tree.
        """
        current_node = self.node
        for loop_bin_mode in reversed(loop_bin_modes):
            current_node.bin_mode = loop_bin_mode
            current_node = current_node.parent
            # Consistency check whether
            # everything went well with previous compilation steps.
            assert current_node is not None
        # Consistency check whether
        # everything went well with previous compilation steps.
        assert current_node is self.root

    def add_acquisition(self, strategy: AcquisitionStrategyPartial) -> None:
        """
        Add acquisition to the group at the current node.
        Note, this function does not check whether the acquisition is compatible with the group.
        First, check that with the `is_compatible` function.
        """
        acq_data = strategy.operation_info.data
        acq_channel = acq_data["acq_channel"]
        acq_index = acq_data["acq_index"]
        protocol = acq_data["protocol"]
        thresholded_trigger_count_metadata = (
            ThresholdedTriggerCountMetadata(
                acq_data["thresholded_trigger_count"]["threshold"],
                acq_data["thresholded_trigger_count"]["condition"],
            )
            if protocol == "ThresholdedTriggerCount"
            else None
        )
        acq_info = FullyAppendAcqInfo(acq_channel, acq_index, thresholded_trigger_count_metadata)
        self.node.children.append(acq_info)
        self.acq_strategies.append(strategy)

    @property
    def number_of_acq_indices(self) -> int:
        """Number of total acquisition indices in the group."""
        return sum(
            acq_strategy.operation_info.data["acq_index"].number_of_acq_indices
            for acq_strategy in self.acq_strategies
        )


T = TypeVar("T", bound=Hashable)


class SequencerCompiler(ABC):
    """
    Class that performs the compilation steps on the sequencer level.

    Abstract base class for different sequencer types.

    Parameters
    ----------
    parent
        A reference to the module compiler this sequencer belongs to.
    index
        Index of the sequencer.
    static_hw_properties
        The static properties of the hardware.
        This effectively gathers all the differences between the different modules.
    sequencer_cfg
        The instrument compiler config associated to this instrument.

    """

    _settings: SequencerSettings

    def __init__(
        self,
        parent: ClusterModuleCompiler,
        index: int,
        static_hw_properties: StaticHardwareProperties,
        sequencer_cfg: _SequencerCompilationConfig,
    ) -> None:
        port, clock = sequencer_cfg.portclock.split("-")

        self.parent = parent
        self.index = index
        self.port = port
        self.clock = clock
        self.op_strategies: list[IOperationStrategy] = []

        self.static_hw_properties = static_hw_properties

        self.register_manager = register_manager.RegisterManager()

        self.qasm_hook_func = sequencer_cfg.sequencer_options.qasm_hook_func

        self.latency_correction = sequencer_cfg.latency_correction

        self.distortion_correction = sequencer_cfg.distortion_correction

        self.qblox_acq_index_manager = QbloxAcquisitionIndexManager(
            parent.qblox_acq_module_resource_manager
        )

    @property
    def connected_output_indices(self) -> tuple[int, ...]:
        """
        Return the connected output indices associated with the output name
        specified in the hardware config.

        For the baseband modules, output index 'n' corresponds to physical module
        output 'n+1'.

        For RF modules, output indices '0' and '1' (or: '2' and '3') correspond to
        'path_I' and 'path_Q' of some sequencer, and both these paths are routed to the
        **same** physical module output '1' (or: '2').
        """
        return self._settings.connected_output_indices

    @property
    def connected_input_indices(self) -> tuple[int, ...]:
        """
        Return the connected input indices associated with the input name specified
        in the hardware config.

        For the baseband modules, input index 'n' corresponds to physical module input
        'n+1'.

        For RF modules, input indices '0' and '1' correspond to 'path_I' and 'path_Q' of
        some sequencer, and both paths are connected to physical module input '1'.
        """
        return self._settings.connected_input_indices

    @property
    def portclock(self) -> tuple[str, str]:
        """
        A tuple containing the unique port and clock combination for this sequencer.

        Returns
        -------
        :
            The portclock.

        """
        return self.port, self.clock

    @property
    def settings(self) -> SequencerSettings:
        """
        Gives the current settings.

        Returns
        -------
        :
            The settings set to this sequencer.

        """
        return self._settings

    @property
    def name(self) -> str:
        """
        The name assigned to this specific sequencer.

        Returns
        -------
        :
            The name.

        """
        return f"seq{self.index}"

    @property
    def has_data(self) -> bool:
        """
        Whether or not the sequencer has any data (meaning pulses or acquisitions)
        assigned to it or not.

        Returns
        -------
        :
            Has data been assigned to this sequencer?

        """
        return len(self.op_strategies) > 0

    @abstractmethod
    def get_operation_strategy(
        self,
        operation_info: OpInfo,
    ) -> IOperationStrategy:
        """
        Determines and instantiates the correct strategy object.

        Parameters
        ----------
        operation_info
            The operation we are building the strategy for.

        Returns
        -------
        :
            The instantiated strategy object.

        """

    def _get_unique_value_or_raise(self, values: Iterable[T], setting_name: str) -> T:
        """Exception that occurs when multiple different values are derived for a setting."""
        values_set = set(values)
        if len(values_set) == 1:
            return values_set.pop()

        phrase = "no" if len(values_set) == 0 else f"{values_set} as possible"
        raise ValueError(
            f"Found {phrase} values for '{setting_name}' on the "
            f"sequencer for port-clock {self.port}-{self.clock}. '{setting_name}' "
            "must be unique per sequencer."
        )

    def add_operation_strategy(self, op_strategy: IOperationStrategy) -> None:
        """
        Adds the operation strategy to the sequencer compiler.

        Parameters
        ----------
        op_strategy
            The operation strategy.

        """
        self.op_strategies.append(op_strategy)
        if op_strategy.operation_info.is_parameter_instruction:
            update_parameters_strategy = UpdateParameterStrategy(
                OpInfo(
                    name="UpdateParameters",
                    data={
                        "t0": 0,
                        "port": self.port,
                        "clock": self.clock,
                        "duration": 0,
                        "instruction": q1asm_instructions.UPDATE_PARAMETERS,
                    },
                    timing=op_strategy.operation_info.timing,
                )
            )
            self.op_strategies.append(update_parameters_strategy)

    def _generate_awg_dict(self) -> dict[str, Any]:
        """
        Generates the dictionary that contains the awg waveforms in the
        format accepted by the driver.

        Notes
        -----
        The final dictionary to be included in the json that is uploaded to the module
        is of the form:

        .. code-block::

            program
            awg
                waveform_name
                    data
                    index
            acq
                waveform_name
                    data
                    index

        This function generates the awg dictionary.

        Returns
        -------
        :
            The awg dictionary.

        Raises
        ------
        ValueError
            I or Q amplitude is being set outside of maximum range.

        RuntimeError
            When the total waveform size specified for a port-clock combination exceeds
            the waveform sample limit of the hardware.

        """
        wf_dict: dict[str, Any] = {}
        # Q1ASM needs to be added to the dict first as they have user defined waveform indices
        priority_strategies = (Q1ASMInjectionStrategy,)
        strategies = []

        # Can loop over self.op_strategies.sort() first with key the instance check.
        # But that's O(nlogn) instead of O(n)

        for op_strategy in self.op_strategies:
            if isinstance(op_strategy, priority_strategies):
                op_strategy.generate_data(wf_dict=wf_dict)
            else:
                strategies.append(op_strategy)

        for op_strategy in strategies:
            if (
                isinstance(op_strategy, GenericPulseStrategy)
                or not op_strategy.operation_info.is_acquisition
            ):
                op_strategy.generate_data(wf_dict=wf_dict)

        self._validate_awg_dict(wf_dict=wf_dict)
        return wf_dict

    def _generate_weights_dict(self) -> dict[str, Any]:
        """
        Generates the dictionary that corresponds that contains the acq weights
        waveforms in the format accepted by the driver.

        Notes
        -----
        The final dictionary to be included in the json that is uploaded to the module
        is of the form:

        .. code-block::

            program
            awg
                waveform_name
                    data
                    index
            acq
                waveform_name
                    data
                    index

        This function generates the acq dictionary.

        Returns
        -------
        :
            The acq dictionary.

        Raises
        ------
        NotImplementedError
            Currently, only two one dimensional waveforms can be used as acquisition
            weights. This exception is raised when either or both waveforms contain
            both a real and imaginary part.

        """
        wf_dict: dict[str, Any] = {}
        for op_strategy in self.op_strategies:
            if op_strategy.operation_info.is_acquisition:
                op_strategy.generate_data(wf_dict)
        return wf_dict

    def _validate_awg_dict(self, wf_dict: dict[str, Any]) -> None:
        total_size = 0
        used_indices = set()
        for waveform in wf_dict.values():
            total_size += len(waveform["data"])
            if waveform["index"] in used_indices:
                raise RuntimeError(f"Duplicate index {waveform['index']} in waveform dictionary.")
            used_indices.add(waveform["index"])

        if total_size > constants.MAX_SAMPLE_SIZE_WAVEFORMS:
            raise RuntimeError(
                f"Total waveform size specified for port-clock {self.port}-"
                f"{self.clock} is {total_size} samples, which exceeds the sample "
                f"limit of {constants.MAX_SAMPLE_SIZE_WAVEFORMS}. The compiled "
                f"schedule cannot be uploaded to the sequencer.",
            )

    @abstractmethod
    def _prepare_acq_settings(
        self,
        acquisitions: list[IOperationStrategy],
    ) -> None:
        """
        Sets sequencer settings that are specific to certain acquisitions.
        For example for a TTL acquisition strategy.

        Parameters
        ----------
        acquisitions
            List of the acquisitions assigned to this sequencer.

        """

    def _validate_thresholded_trigger_count_metadata_by_acq_channel(
        self, acquisitions: list[IOperationStrategy]
    ) -> None:
        """
        Validate that all thresholds are the same for **single** threshold ThresholdedTriggerCount
        acquisitions on this sequencer.

        Returns
        -------
        :
            The threshold, if ThresholdedTriggerCount acquisition is scheduled,
            or None, if it is not scheduled.

        Raises
        ------
        RuntimeError
            If different thresholds are found.

        """
        metadata_dict: dict[int, ThresholdedTriggerCountMetadata] = {}
        for acq in acquisitions:
            if acq.operation_info.data["protocol"] != "ThresholdedTriggerCount":
                continue

            acq_channel = acq.operation_info.data["acq_channel"]
            threshold = acq.operation_info.data["thresholded_trigger_count"]["threshold"]
            condition = acq.operation_info.data["thresholded_trigger_count"]["condition"]
            if acq_channel in metadata_dict and (
                metadata_dict[acq_channel].threshold != threshold
                or metadata_dict[acq_channel].condition != condition
            ):
                raise ValueError(
                    f"Trying to set thresholded trigger count settings threshold={threshold} and "
                    f"condition={condition} for {acq_channel=}, while those were previously "
                    f"determined to be threshold={metadata_dict[acq_channel].threshold} and "
                    f"condition={metadata_dict[acq_channel].condition}, respectively. These "
                    "settings must be the same per acquisition channel."
                )
            metadata_dict[acq_channel] = ThresholdedTriggerCountMetadata(
                threshold=threshold, condition=condition
            )

    def generate_qasm_program(
        self,
        ordered_op_strategies: list[IOperationStrategy],
        total_sequence_time: float,
        align_qasm_fields: bool,
        repetitions: int,
    ) -> str:
        """
        Generates a QASM program for a sequencer. Requires the awg and acq dicts to
        already have been generated.

        Example of a program generated by this function:

        .. code-block::

                    wait_sync     4
                    set_mrk       1
                    move          10,R0         # iterator for loop with label start
            start:
                    wait          4
                    set_awg_gain  22663,10206  # setting gain for 9056793381316377208
                    play          0,1,4
                    wait          176
                    loop          R0,@start
                    set_mrk       0
                    upd_param     4
                    stop


        Parameters
        ----------
        ordered_op_strategies
            A sorted list of operations, in order of execution.
        total_sequence_time
            Total time the program needs to play for. If the sequencer would be done
            before this time, a wait is added at the end to ensure synchronization.
        align_qasm_fields
            If True, make QASM program more human-readable by aligning its fields.
        repetitions
            Number of times to repeat execution of the schedule.

        Returns
        -------
        :
            The generated QASM program.

        Warns
        -----
        RuntimeWarning
            When number of instructions in the generated QASM program exceeds the
            maximum supported number of instructions for sequencers in the type of
            module.

        Raises
        ------
        RuntimeError
            Upon ``total_sequence_time`` exceeding :attr:`.QASMProgram.elapsed_time`.

        """
        loop_label = "start"

        qasm = QASMProgram(
            static_hw_properties=self.static_hw_properties,
            register_manager=self.register_manager,
            align_fields=align_qasm_fields,
        )
        self._write_pre_wait_sync_instructions(qasm)

        # program header
        qasm.set_latch(self.op_strategies)
        qasm.emit(q1asm_instructions.WAIT_SYNC, constants.MIN_TIME_BETWEEN_OPERATIONS)
        qasm.emit(q1asm_instructions.UPDATE_PARAMETERS, constants.MIN_TIME_BETWEEN_OPERATIONS)

        self._initialize_acquisitions_fully_append_with_average_append_bin_mode(
            qasm, ordered_op_strategies
        )
        self._initialize_acquisitions(qasm, ordered_op_strategies, repetitions)

        # Program body. The operations must be ordered such that real-time IO operations
        # always come after any other operations. E.g., an offset instruction should
        # always come before the parameter update, play, or acquisition instruction.

        # Adds the latency correction, this needs to be a minimum of 4 ns,
        # so all sequencers get delayed by at least that.
        latency_correction_ns: int = self._get_latency_correction_ns(self.latency_correction)
        qasm.auto_wait(
            wait_time=constants.MIN_TIME_BETWEEN_OPERATIONS + latency_correction_ns,
            count_as_elapsed_time=False,
            comment=f"latency correction of {constants.MIN_TIME_BETWEEN_OPERATIONS} + "
            f"{latency_correction_ns} ns",
        )

        with qasm.loop(label=loop_label, repetitions=repetitions):
            self._write_repetition_loop_header(qasm)

            last_operation_end = {True: 0.0, False: 0.0}
            for operation in ordered_op_strategies:
                # Check if there is an overlapping pulse or overlapping acquisition
                if operation.operation_info.is_real_time_io_operation:
                    start_time = operation.operation_info.timing
                    is_acquisition = operation.operation_info.is_acquisition
                    if helpers.to_grid_time(start_time) < helpers.to_grid_time(
                        last_operation_end[is_acquisition]
                    ):
                        warnings.warn(
                            f"Operation is interrupting previous"
                            f" {'Acquisition' if is_acquisition else 'Pulse'}"
                            f" because it starts before the previous ends,"
                            f" offending operation:"
                            f" {operation.operation_info!s}",
                            RuntimeWarning,
                        )
                    last_operation_end[is_acquisition] = (
                        start_time + operation.operation_info.duration
                    )

            self._parse_operations(iter(ordered_op_strategies), qasm)

            end_time = helpers.to_grid_time(total_sequence_time)
            wait_time = end_time - qasm.elapsed_time
            if wait_time < 0:
                raise RuntimeError(
                    f"Invalid timing detected, attempting to insert wait "
                    f"of {wait_time} ns. The total duration of the "
                    f"schedule is {end_time} but {qasm.elapsed_time} ns "
                    f"already processed."
                )
            qasm.auto_wait(wait_time=wait_time)

        # program footer
        qasm.emit(q1asm_instructions.STOP)

        if repetitions > 1:
            # Because reset_ph will be called at the start of each repetition (on
            # analog modules), we need to assert that each repetition starts on the NCO
            # grid if there is more than 1 repetition.
            self._assert_total_play_time_on_nco_grid()

        if self.qasm_hook_func:
            self.qasm_hook_func(qasm)

        if (num_instructions := len(qasm.instructions)) > self.parent.max_number_of_instructions:
            warnings.warn(
                f"Number of instructions ({num_instructions}) compiled for "
                f"'{self.name}' of {self.parent.__class__.__name__} "
                f"'{self.parent.name}' exceeds the maximum supported number of "
                f"instructions in Q1ASM programs for {self.parent.__class__.__name__} "
                f"({self.parent.max_number_of_instructions}).",
                RuntimeWarning,
            )

        qasm.merge_some_arithmetic_instructions()
        qasm.fix_missing_nops()
        return str(qasm)

    def _assert_total_play_time_on_nco_grid(self) -> None:  # noqa: B027
        """
        Raises an error if the total play time does not align with the NCO grid time.

        Method is implemented on the base class instead of the `AnalogSequencerCompiler`
        subclass because it is called by `generate_qasm_program`.
        """
        pass

    class ParseOperationStatus(Enum):
        """Return status of the stack."""

        COMPLETED_ITERATION = auto()
        """The iterator containing operations is exhausted."""
        EXITED_CONTROL_FLOW = auto()
        """The end of a control flow scope is reached."""

    def _parse_operations(
        self,
        operations_iter: Iterator[IOperationStrategy],
        qasm: QASMProgram,
    ) -> ParseOperationStatus:
        """Handle control flow and insert Q1ASM."""
        while (strategy := next(operations_iter, None)) is not None:
            qasm.wait_till_start_operation(strategy.operation_info)
            if isinstance(strategy, LoopStrategy):
                loop_label = f"loop{len(qasm.instructions)}"
                domain = strategy.operation_info.data.get("domain")
                repetitions = strategy.operation_info.data["repetitions"]
                with qasm.loop(loop_label, repetitions, domain):
                    returned_from_return_stack = self._parse_operations(
                        operations_iter=operations_iter,
                        qasm=qasm,
                    )
                    assert returned_from_return_stack in self.ParseOperationStatus

            elif isinstance(strategy, ConditionalStrategy):
                with qasm.conditional(strategy):
                    returned_from_return_stack = self._parse_operations(
                        operations_iter=operations_iter,
                        qasm=qasm,
                    )
                    assert returned_from_return_stack in self.ParseOperationStatus

            elif isinstance(strategy, ControlFlowReturnStrategy):
                return self.ParseOperationStatus.EXITED_CONTROL_FLOW
            else:
                qasm.conditional_manager.update(strategy)
                self._insert_qasm(strategy, qasm)

        return self.ParseOperationStatus.EXITED_CONTROL_FLOW

    @abstractmethod
    def _insert_qasm(self, op_strategy: IOperationStrategy, qasm_program: QASMProgram) -> None:
        """Get Q1ASM instruction(s) from ``op_strategy`` and insert them into ``qasm_program``."""

    @abstractmethod
    def _write_pre_wait_sync_instructions(self, qasm: QASMProgram) -> None:
        """
        Write instructions to the QASM program that must come before the first wait_sync.

        The duration must be equal for all module types.
        """

    @abstractmethod
    def _write_repetition_loop_header(self, qasm: QASMProgram) -> None:
        """
        Write the Q1ASM that should appear at the start of the repetition loop.

        The duration must be equal for all module types.
        """

    def _get_ordered_operations(self) -> list[IOperationStrategy]:
        """Get the class' operation strategies in order of scheduled execution."""
        return sorted(
            self.op_strategies,
            key=lambda op: helpers.to_grid_time(op.operation_info.timing),
        )

    @staticmethod
    def _create_acq_groups(  # noqa: C901
        op_strategies: Iterable[IOperationStrategy],
    ) -> list[_AcquisitionGroup]:
        groups: list[_AcquisitionGroup] = []

        def find_and_update_compatible_group(
            loop_bin_modes: list[BinMode],
        ) -> _AcquisitionGroup | None:
            for group in groups:
                if group.is_compatible(loop_bin_modes):
                    group.update_loop_bin_modes(loop_bin_modes)
                    return group

        current_repetitions: list[int | None] = []

        for strategy in op_strategies:
            if isinstance(strategy, LoopStrategy):
                repetitions = strategy.operation_info.data["repetitions"]
                for group in groups:
                    group.node = group.node.add_control_flow_child(repetitions, None)
                current_repetitions.append(repetitions)
            elif isinstance(strategy, ConditionalStrategy):
                for group in groups:
                    group.node = group.node.add_control_flow_child(None, None)
                current_repetitions.append(None)
            elif isinstance(strategy, ControlFlowReturnStrategy):
                for group in groups:
                    if group.node.repetitions is None:
                        raise ValueError(
                            "Only loop control flow is supported "
                            "for acquisitions with AVERAGE_APPEND bin mode."
                        )
                    group.node = group.node.return_control_flow_child()
                current_repetitions.pop()
            elif strategy.operation_info.is_acquisition:
                # Help the type checker.
                assert isinstance(strategy, AcquisitionStrategyPartial)

                acq_data = strategy.operation_info.data
                protocol: str = acq_data["protocol"]
                bin_mode: BinMode = acq_data["bin_mode"]
                if _is_acquisition_binned_average_append(protocol, bin_mode):
                    acq_index = acq_data["acq_index"]
                    group = find_and_update_compatible_group(
                        acq_index.loop_bin_modes,
                    )
                    if group is None:
                        new_root = AcqFullyAppendLoopNode(
                            parent=None, children=[], repetitions=None, bin_mode=None
                        )
                        new_node = new_root
                        for repetition in current_repetitions:
                            new_node = new_node.add_control_flow_child(repetition, None)
                        group = _AcquisitionGroup(
                            root=new_root,
                            node=new_node,
                            acq_strategies=[],
                        )
                        group.update_loop_bin_modes(acq_index.loop_bin_modes)
                        groups.append(group)
                    group.add_acquisition(strategy)

        return groups

    def _initialize_acquisitions_fully_append_with_average_append_bin_mode(
        self, qasm: QASMProgram, op_strategies: list[IOperationStrategy]
    ) -> None:
        groups = self._create_acq_groups(op_strategies)

        for group in groups:
            if len(group.acq_strategies) == 0:
                continue

            try:
                qblox_acq_index, qblox_acq_bin_offset = (
                    self.qblox_acq_index_manager.allocate_bins_fully_append(
                        number_of_acq_indices=group.number_of_acq_indices,
                        tree=group.root,
                        repetitions=1,
                    )
                )
                bin_idx_register = self.register_manager.allocate_register()

            except ValueError as err:
                raise ValueError(
                    f"Error allocating acquisition memory for sequencer {self.name}."
                ) from err

            for op_strategy in group.acq_strategies:
                # Help the type checker.
                assert isinstance(op_strategy, AcquisitionStrategyPartial)

                op_strategy.qblox_acq_index = qblox_acq_index
                op_strategy.qblox_acq_bin = None
                op_strategy.bin_idx_register = bin_idx_register

            qasm.emit(
                q1asm_instructions.MOVE,
                qblox_acq_bin_offset,
                bin_idx_register,
                comment="Initialize acquisition bin_idx for acq. group",
            )

    def _initialize_acquisitions(
        self, qasm: QASMProgram, op_strategies: list[IOperationStrategy], repetitions: int
    ) -> None:
        """
        Adds the instructions to initialize the registers needed to use the append
        bin mode to the program. This should be added in the header.

        Parameters
        ----------
        qasm:
            The program to add the instructions to.
        op_strategies:
            An operations list including all the acquisitions to consider.
        repetitions:
            TimeableSchedule repetitions.

        """
        for op_strategy in op_strategies:
            if not op_strategy.operation_info.is_acquisition:
                continue
            # Help the type checker.
            assert isinstance(op_strategy, AcquisitionStrategyPartial)

            acq_data = op_strategy.operation_info.data
            acq_channel = acq_data["acq_channel"]
            protocol: str = acq_data["protocol"]
            bin_mode: BinMode = acq_data["bin_mode"]

            if _is_acquisition_binned_average_append(protocol, bin_mode):
                continue

            try:
                qblox_acq_index, qblox_acq_bin_offset, bin_idx_register = (
                    self._allocate_acquisition_memory_and_bin_register(
                        protocol,
                        bin_mode,
                        acq_data,
                        acq_channel,
                        repetitions,
                        op_strategy.operation_info,
                    )
                )
            except ValueError as err:
                raise ValueError(
                    f"Error allocating acquisition memory for sequencer {self.name}."
                ) from err

            op_strategy.qblox_acq_index = qblox_acq_index
            op_strategy.qblox_acq_bin = qblox_acq_bin_offset
            op_strategy.bin_idx_register = bin_idx_register
            if bin_idx_register is not None:
                op_strategy.reset_bin_idx_reg(qasm)

    def _allocate_acquisition_memory_and_bin_register(
        self,
        protocol: str,
        bin_mode: BinMode,
        acq_data: dict,
        acq_channel: Hashable,
        repetitions: int,
        op_info: OpInfo,
    ) -> tuple[int, int, str | None]:
        if (
            _is_acquisition_binned_average(protocol, bin_mode)
            or _is_acquisition_binned_append(protocol, bin_mode)
            or _is_acquisition_binned_average_append(protocol, bin_mode)
        ):
            thresholded_trigger_count_metadata = (
                ThresholdedTriggerCountMetadata(
                    acq_data["thresholded_trigger_count"]["threshold"],
                    acq_data["thresholded_trigger_count"]["condition"],
                )
                if protocol == "ThresholdedTriggerCount"
                else None
            )
            qblox_acq_index, qblox_acq_bin_offset = self.qblox_acq_index_manager.allocate_bins(
                acq_channel,
                acq_data["acq_index"].acq_index,
                thresholded_trigger_count_metadata,
                repetitions if bin_mode == BinMode.APPEND else None,
            )

            bin_idx_register = None
            if _is_acquisition_binned_append(
                protocol, bin_mode
            ) or _is_acquisition_binned_average_append(protocol, bin_mode):
                bin_idx_register = self.register_manager.allocate_register()

            return qblox_acq_index, qblox_acq_bin_offset, bin_idx_register
        elif bin_mode == BinMode.DISTRIBUTION and protocol in (
            "TriggerCount",
            "ThresholdedTriggerCount",
            "DualThresholdedTriggerCount",
        ):
            qblox_acq_index = self.qblox_acq_index_manager.allocate_qblox_index(acq_channel)
            qblox_acq_bin_offset = 0
            return qblox_acq_index, qblox_acq_bin_offset, None
        elif protocol in "Trace":
            qblox_acq_index, qblox_acq_bin_offset = self.qblox_acq_index_manager.allocate_trace(
                acq_channel
            )
            return qblox_acq_index, qblox_acq_bin_offset, None
        elif bin_mode == BinMode.APPEND and protocol == "TimetagTrace":
            qblox_acq_index, qblox_acq_bin_offset = (
                self.qblox_acq_index_manager.allocate_timetagtrace(
                    acq_channel,
                    acq_data["acq_index"].acq_index,
                    repetitions,
                )
            )
            bin_idx_register = self.register_manager.allocate_register()
            return qblox_acq_index, qblox_acq_bin_offset, bin_idx_register
        else:
            raise ValueError(
                f"Unsupported acquisition protocol '{protocol}' "
                f"for acquisition channel '{acq_channel}', "
                f"{op_info!r}."
            )

    def _get_latency_correction_ns(self, latency_correction: float) -> int:
        if latency_correction == 0:
            return 0

        latency_correction_ns = round(latency_correction * 1e9)

        return latency_correction_ns

    def _remove_redundant_update_parameters(self) -> None:
        """
        Removing redundant update parameter instructions.
        If multiple update parameter instructions happen at the same time,
        directly after each other in order, then it's safe to only keep one of them.

        Also, real time io operations act as update parameter instructions too.
        If a real time io operation happen ((just after or just before) and at the same time)
        as an update parameter instruction, then the update parameter instruction is redundant.
        """

        def _removal_pass(is_reversed: bool) -> None:
            indices_to_be_removed: set[int] = set()

            last_updated_timing: int | None = None
            # Cannot use self._get_ordered_operations here because of the `enumerate`.
            sorted_op_strategies = sorted(
                enumerate(self.op_strategies),
                key=lambda op: helpers.to_grid_time(op[1].operation_info.timing),
            )
            if is_reversed:
                sorted_op_strategies = reversed(sorted_op_strategies)
            for index, op_strategy in sorted_op_strategies:
                op_timing = helpers.to_grid_time(op_strategy.operation_info.timing)

                if (
                    op_strategy.operation_info.is_parameter_update
                    or op_strategy.operation_info.is_real_time_io_operation
                ):
                    if (
                        op_strategy.operation_info.is_parameter_update
                        and last_updated_timing is not None
                        and last_updated_timing == op_timing
                    ):
                        indices_to_be_removed.add(index)
                    else:
                        last_updated_timing = op_timing
                elif (
                    (not is_reversed and op_strategy.operation_info.is_parameter_instruction)
                    or (is_reversed and isinstance(op_strategy, ConditionalStrategy))
                    or isinstance(op_strategy, (LoopStrategy, ControlFlowReturnStrategy))
                ):
                    # If a parameter instruction happens while
                    # we're iterating through the operations not in reverse,
                    # that invalidates all the other update parameters
                    # (and real time io instructions) that were before it,
                    # because that potentially means the parameter is not updated.
                    #
                    # For conditionals and loops we
                    # cannot eliminate the update parameter just before them,
                    # because these control flows might not even
                    # run their bodies (for loops if repetition is 0).
                    #
                    # For loops, we cannot eliminate the first update parameter in the body,
                    # because we directly can jump there from the end of the body,
                    # not necessarily from the instruction just before the loop.

                    last_updated_timing = None

            self.op_strategies = [
                op for i, op in enumerate(self.op_strategies) if i not in indices_to_be_removed
            ]

        # We can remove all redundant update parameters which
        # happen at the same time and after each other,
        # and remove all update parameters which happen **after** a real time io operation,
        # if no parameter instruction is between them.
        _removal_pass(is_reversed=False)
        # We can remove all update parameters which
        # happen **before** a real time io operation.
        _removal_pass(is_reversed=True)

    def _validate_update_parameters_alignment(self) -> None:
        last_upd_params_incompatible_op_info: OpInfo | None = None
        total_play_time = helpers.to_grid_time(self.parent.total_play_time)

        sorted_op_strategies = self._get_ordered_operations()
        for op_strategy in reversed(sorted_op_strategies):
            op_timing = helpers.to_grid_time(op_strategy.operation_info.timing)

            if op_strategy.operation_info.is_parameter_update:
                if total_play_time == op_timing:
                    raise RuntimeError(
                        f"Parameter operation {op_strategy.operation_info} with start time "
                        f"{op_strategy.operation_info.timing} cannot be scheduled at the very end "
                        "of a TimeableSchedule. The TimeableSchedule can be extended by adding an "
                        "IdlePulse operation with a duration of at least "
                        f"{constants.MIN_TIME_BETWEEN_OPERATIONS} ns, "
                        f"or the Parameter operation can be "
                        "replaced by another operation."
                    )
                elif (
                    last_upd_params_incompatible_op_info is not None
                    and helpers.to_grid_time(last_upd_params_incompatible_op_info.timing)
                    == op_timing
                ):
                    raise RuntimeError(
                        f"Parameter operation {op_strategy.operation_info} with start time "
                        f"{op_strategy.operation_info.timing} cannot be scheduled exactly before "
                        f"the operation {last_upd_params_incompatible_op_info} "
                        f"with the same start time. "
                        "Insert an IdlePulse operation with a duration of at least "
                        f"{constants.MIN_TIME_BETWEEN_OPERATIONS} ns, "
                        f"or the Parameter operation can be "
                        "replaced by another operation."
                    )
            elif op_strategy.operation_info.is_control_flow_end or isinstance(
                op_strategy, LoopStrategy | ConditionalStrategy
            ):
                last_upd_params_incompatible_op_info = op_strategy.operation_info

    @staticmethod
    def _replace_digital_pulses(
        op_strategies: list[IOperationStrategy], module_options: ClusterModuleDescription
    ) -> list[IOperationStrategy]:
        """Replaces MarkerPulse operations by explicit high and low operations."""
        new_op_strategies: list[IOperationStrategy] = []
        for op_strategy in op_strategies:
            if isinstance(op_strategy, DigitalOutputStrategy):
                high_op_info = OpInfo(
                    name=op_strategy.operation_info.name,
                    data=op_strategy.operation_info.data.copy(),
                    timing=op_strategy.operation_info.timing,
                )
                high_op_info.data["enable"] = True
                high_op_info.data["duration"] = 0
                duration = op_strategy.operation_info.data["duration"]
                low_op_info = OpInfo(
                    name=op_strategy.operation_info.name,
                    data=op_strategy.operation_info.data.copy(),
                    timing=op_strategy.operation_info.timing + duration,
                )
                low_op_info.data["enable"] = False
                low_op_info.data["duration"] = 0
                if op_strategy.__class__ == MarkerPulseStrategy:
                    strategy_high = MarkerPulseStrategy(
                        operation_info=high_op_info,
                        channel_name=op_strategy.channel_name,
                        module_options=module_options,
                    )
                    strategy_low = MarkerPulseStrategy(
                        operation_info=low_op_info,
                        channel_name=op_strategy.channel_name,
                        module_options=module_options,
                    )
                else:
                    strategy_high = op_strategy.__class__(
                        operation_info=high_op_info,
                        channel_name=op_strategy.channel_name,
                    )
                    strategy_low = op_strategy.__class__(
                        operation_info=low_op_info,
                        channel_name=op_strategy.channel_name,
                    )
                new_op_strategies.append(strategy_high)
                new_op_strategies.append(
                    UpdateParameterStrategy(
                        OpInfo(
                            name="UpdateParameters",
                            data={
                                "t0": 0,
                                "port": high_op_info.data["port"],
                                "clock": high_op_info.data["clock"],
                                "duration": 0,
                                "instruction": q1asm_instructions.UPDATE_PARAMETERS,
                            },
                            timing=high_op_info.timing,
                        )
                    )
                )
                new_op_strategies.append(strategy_low)
                new_op_strategies.append(
                    UpdateParameterStrategy(
                        OpInfo(
                            name="UpdateParameters",
                            data={
                                "t0": 0,
                                "port": low_op_info.data["port"],
                                "clock": low_op_info.data["clock"],
                                "duration": 0,
                                "instruction": q1asm_instructions.UPDATE_PARAMETERS,
                            },
                            timing=low_op_info.timing,
                        )
                    )
                )
            else:
                new_op_strategies.append(op_strategy)

        return new_op_strategies

    @staticmethod
    def _generate_waveforms_and_program_dict(
        program: str,
        waveforms_dict: dict[str, Any],
        weights_dict: dict[str, Any] | None = None,
        acq_decl_dict: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generates the full waveforms and program dict that is to be uploaded to the
        sequencer from the program string and the awg and acq dicts, by combining them
        and assigning the appropriate keys.

        Parameters
        ----------
        program
            The compiled QASM program as a string.
        waveforms_dict
            The dictionary containing all the awg data and indices. This is expected to
            be of the form generated by the ``generate_awg_dict`` method.
        weights_dict
            The dictionary containing all the acq data and indices. This is expected to
            be of the form generated by the ``generate_acq_dict`` method.
        acq_decl_dict
            The dictionary containing all the acq declarations. This is expected to be
            of the form generated by the ``generate_acq_decl_dict`` method.

        Returns
        -------
        :
            The combined program.

        """
        compiled_dict: dict[str, Any] = {}
        compiled_dict["program"] = program
        compiled_dict["waveforms"] = waveforms_dict
        if weights_dict is not None:
            compiled_dict["weights"] = weights_dict
        if acq_decl_dict is not None:
            compiled_dict["acquisitions"] = acq_decl_dict
        return compiled_dict

    @staticmethod
    def _dump_waveforms_and_program_json(
        wf_and_pr_dict: dict[str, Any], label: str | None = None
    ) -> str:
        """
        Takes a combined waveforms and program dict and dumps it as a json file.

        Parameters
        ----------
        wf_and_pr_dict
            The dict to dump as a json file.
        label
            A label that is appended to the filename.

        Returns
        -------
        :
            The full absolute path where the json file is stored.

        """
        data_dir = OutputDirectoryManager.get_datadir()
        folder = path.join(data_dir, "schedules")
        makedirs(folder, exist_ok=True)

        filename = f"{gen_tuid()}.json" if label is None else f"{gen_tuid()}_{label}.json"
        filename = sanitize_filename(filename)
        file_path = path.join(folder, filename)

        with open(file_path, "w") as file:
            json.dump(wf_and_pr_dict, file, cls=NumpyJSONEncoder, indent=4)

        return file_path

    def prepare(self) -> None:
        """
        Perform necessary operations on this sequencer's data before
        :meth:`~SequencerCompiler.compile` is called.
        """
        self.op_strategies = self._replace_digital_pulses(
            self.op_strategies, self.parent.instrument_cfg.hardware_description
        )
        self._remove_redundant_update_parameters()
        self._validate_update_parameters_alignment()
        self._prepare_threshold_settings(self.op_strategies)

    def _prepare_threshold_settings(
        self,
        operations: list[IOperationStrategy],
    ) -> None:
        """
        Derive sequencer settings for trigger count thresholding.

        Parameters
        ----------
        operations
            List of the acquisitions assigned to this sequencer.

        """
        for operation in operations:
            if operation.operation_info.name != "ConditionalBegin":
                continue

            # Note: validation that all conditional operations, with the same address,
            # have the same "invert" and "count" settings is done in
            # qblox_backend._update_conditional_info_from_acquisition.
            # These asserts are for the developer:

            if (
                operation.operation_info.data["feedback_trigger_address"]
                in self._settings.thresholded_acq_trigger_read_settings
            ):
                read_settings = self._settings.thresholded_acq_trigger_read_settings[
                    operation.operation_info.data["feedback_trigger_address"]
                ]
                assert (
                    operation.operation_info.data["feedback_trigger_invert"]
                    == read_settings.thresholded_acq_trigger_invert
                )
                assert (
                    operation.operation_info.data["feedback_trigger_count"]
                    == read_settings.thresholded_acq_trigger_count
                )

            self._settings.thresholded_acq_trigger_read_settings[
                operation.operation_info.data["feedback_trigger_address"]
            ] = ThresholdedAcqTriggerReadSettings(
                thresholded_acq_trigger_invert=operation.operation_info.data[
                    "feedback_trigger_invert"
                ],
                thresholded_acq_trigger_count=operation.operation_info.data[
                    "feedback_trigger_count"
                ],
            )

    def compile(
        self,
        sequence_to_file: bool,
        align_qasm_fields: bool,
        repetitions: int = 1,
    ) -> SequencerSettings | None:
        """
        Performs the full sequencer level compilation based on the assigned data and
        settings. If no data is assigned to this sequencer, the compilation is skipped
        and None is returned instead.

        Parameters
        ----------
        sequence_to_file
            Dump waveforms and program dict to JSON file, filename stored in
            `SequencerCompiler.settings.seq_fn`.
        align_qasm_fields
            If True, make QASM program more human-readable by aligning its fields.
        repetitions
            Number of times execution the schedule is repeated.

        Returns
        -------
        :
            The compiled program.
            If no data is assigned to this sequencer, the
            compilation is skipped and None is returned instead.

        """
        if not self.has_data:
            return None

        awg_dict = self._generate_awg_dict()
        weights_dict = None
        acq_declaration_dict = None

        # the program needs _generate_weights_dict for the waveform indices
        if self.parent.supports_acquisition:
            weights_dict = {}
            acquisitions = [
                op_strategy
                for op_strategy in self.op_strategies
                if op_strategy.operation_info.is_acquisition
            ]
            if len(acquisitions) > 0:
                self._prepare_acq_settings(
                    acquisitions=acquisitions,
                )
                weights_dict = self._generate_weights_dict()

        # acq_declaration_dict needs to count number of acquires in the program
        operation_list = self._get_ordered_operations()
        qasm_program = self.generate_qasm_program(
            ordered_op_strategies=operation_list,
            total_sequence_time=self.parent.total_play_time,
            align_qasm_fields=align_qasm_fields,
            repetitions=repetitions,
        )

        if self.parent.supports_acquisition:
            acq_declaration_dict = self.qblox_acq_index_manager.acq_declaration_dict()

        wf_and_prog = self._generate_waveforms_and_program_dict(
            qasm_program, awg_dict, weights_dict, acq_declaration_dict
        )

        self._settings.sequence = wf_and_prog
        self._settings.seq_fn = None
        if sequence_to_file:
            self._settings.seq_fn = self._dump_waveforms_and_program_json(
                wf_and_pr_dict=wf_and_prog, label=f"{self.port}_{self.clock}"
            )

        return self._settings

    def _validate_thresholded_acquisitions(
        self, operations: list[IOperationStrategy], protocol: str
    ) -> None:
        """
        All thresholded acquisitions on a single sequencer must have the same label and the same
        threshold settings.
        """
        if protocol not in (
            "ThresholdedAcquisition",
            "ThresholdedTriggerCount",
            "WeightedThresholdedAcquisition",
        ):
            # Early return: we do not check other protocols.
            return

        acquisitions = [
            op
            for op in operations
            if op.operation_info.is_acquisition
            and op.operation_info.data.get("feedback_trigger_label") is not None
        ]
        if len(acquisitions) < 2:
            # Early return: only 1 acquisition means nothing can conflict.
            return

        keys_to_check = {}
        if protocol in ("ThresholdedAcquisition", "WeightedThresholdedAcquisition"):
            keys_to_check = {"acq_threshold", "acq_rotation", "feedback_trigger_label"}
        elif protocol == "ThresholdedTriggerCount":
            keys_to_check = {"thresholded_trigger_count", "feedback_trigger_label"}

        for key in keys_to_check:
            first_value = acquisitions[0].operation_info.data[key]
            for acq in acquisitions[1:]:
                if acq.operation_info.data[key] != first_value:
                    raise ValueError(
                        f"All {protocol} acquisitions on the same port-clock must have the same "
                        f"threshold settings. Found different settings for {key}:\n{first_value}\n"
                        f"\n{acq.operation_info.data[key]}"
                    )


_SequencerT_co = TypeVar("_SequencerT_co", bound=SequencerCompiler, covariant=True)
"""
A generic SequencerCompiler type for typehints in :class:`ClusterModuleCompiler`.

Covariant so that subclasses of ClusterModuleCompiler can use subclassses of
:class:`SequencerCompiler` in their typehints.
"""


class _ModuleSettingsType(Protocol):
    """
    A typehint for the various module settings (e.g.
    :class:`~qblox_scheduler.backends.types.qblox.BasebandModuleSettings`) classes.
    """

    def to_dict(self) -> dict[str, Any]:
        """Convert the settings to a dictionary."""
        ...


class ClusterModuleCompiler(InstrumentCompiler, Generic[_SequencerT_co], ABC):
    """
    Base class for all cluster modules, and an interface for those modules to the
    :class:`~qblox_scheduler.backends.qblox.instrument_compilers.ClusterCompiler`.

    This class is defined as an abstract base class since the distinctions between the
    different devices are defined in subclasses.
    Effectively, this base class contains the functionality shared by all Qblox
    devices and serves to avoid repeated code between them.

    Parameters
    ----------
    name
        Name of the `QCoDeS` instrument this compiler object corresponds to.
    total_play_time
        Total time execution of the schedule should go on for. This parameter is
        used to ensure that the different devices, potentially with different clock
        rates, can work in a synchronized way when performing multiple executions of
        the schedule.
    instrument_cfg
        The instrument compiler config referring to this device.

    """

    _settings: _ModuleSettingsType
    static_hw_properties: StaticHardwareProperties

    def __init__(
        self,
        name: str,
        total_play_time: float,
        instrument_cfg: _ClusterModuleCompilationConfig,
    ) -> None:
        driver_version_check.verify_qblox_instruments_version()
        super().__init__(
            name=name,
            total_play_time=total_play_time,
            instrument_cfg=instrument_cfg,
        )
        self.instrument_cfg: _ClusterModuleCompilationConfig  # Help typechecker
        self._op_infos: dict[tuple[str, str], list[OpInfo]] = defaultdict(list)
        self.portclock_to_path = instrument_cfg.portclock_to_path
        self.sequencers: dict[str, _SequencerT_co] = {}

        self.qblox_acq_module_resource_manager = QbloxAcquisitionModuleResourceManager(
            self.static_hw_properties.max_acquisition_bin_count
        )

    @property
    def portclocks(self) -> list[str]:
        """Returns all the port-clock combinations that this device can target."""
        return list(self.portclock_to_path.keys())

    @property
    @abstractmethod
    def supports_acquisition(self) -> bool:
        """Specifies whether the device can perform acquisitions."""

    @property
    @abstractmethod
    def max_number_of_instructions(self) -> int:
        """The maximum number of Q1ASM instructions supported by this module type."""

    def add_op_info(self, port: str, clock: str, op_info: OpInfo) -> None:
        """
        Assigns a certain pulse or acquisition to this device.

        Parameters
        ----------
        port
            The port this waveform is sent to (or acquired from).
        clock
            The clock for modulation of the pulse or acquisition. Can be a BasebandClock.
        op_info
            Data structure containing all the information regarding this specific
            pulse or acquisition operation.

        """
        if op_info.is_acquisition and not self.supports_acquisition:
            raise RuntimeError(
                f"{self.__class__.__name__} {self.name} does not support acquisitions. "
                f"Attempting to add acquisition {op_info!r} "
                f"on port {port} with clock {clock}."
            )
        self._op_infos[(port, clock)].append(op_info)

    @property
    def _portclocks_with_data(self) -> set[tuple[str, str]]:
        """
        All the port-clock combinations associated with at least one pulse and/or
        acquisition.

        Returns
        -------
        :
            A set containing all the port-clock combinations that are used by this
            InstrumentCompiler.

        """
        portclocks_used: set[tuple[str, str]] = {
            portclock
            for portclock, op_infos in self._op_infos.items()
            if not all(op_info.data.get("name") == "LatchReset" for op_info in op_infos)
        }
        return portclocks_used

    def _construct_all_sequencer_compilers(self) -> None:
        """
        Constructs :class:`~SequencerCompiler` objects for each port and clock combination
        belonging to this device.

        Raises
        ------
        ValueError
            Attempting to use more sequencers than available.

        """
        # Setup each sequencer.
        sequencers: dict[str, _SequencerT_co] = {}
        sequencer_configs = self.instrument_cfg._extract_sequencer_compilation_configs()

        for seq_idx, sequencer_cfg in sequencer_configs.items():
            port, clock = sequencer_cfg.portclock.split("-")
            if (port, clock) in self._portclocks_with_data:
                new_seq = self._construct_sequencer_compiler(
                    index=seq_idx,
                    sequencer_cfg=sequencer_cfg,
                )
                sequencers[new_seq.name] = new_seq

        self.sequencers = sequencers

    @abstractmethod
    def _construct_sequencer_compiler(
        self,
        index: int,
        sequencer_cfg: _SequencerCompilationConfig,
    ) -> _SequencerT_co:
        """Create the sequencer object of the correct sequencer type belonging to the module."""

    def distribute_data(self) -> None:
        """
        Distributes the pulses and acquisitions assigned to this module over the
        different sequencers based on their portclocks. Raises an exception in case
        the device does not support acquisitions.
        """
        for seq in self.sequencers.values():
            if seq.op_strategies is None:
                seq.op_strategies = []

            for portclock, op_info_list in self._op_infos.items():
                if seq.portclock == portclock or (
                    portclock[0] is None and portclock[1] == seq.clock
                ):
                    for op_info in op_info_list:
                        if not op_info.is_acquisition or not (
                            portclock[0] is None and portclock[1] == seq.clock
                        ):
                            op_strategy = seq.get_operation_strategy(
                                operation_info=op_info,
                            )
                            seq.add_operation_strategy(op_strategy)

    def compile(
        self,
        debug_mode: bool,
        repetitions: int = 1,
        sequence_to_file: bool | None = None,
    ) -> dict[str, Any]:
        """
        Performs the actual compilation steps for this module, by calling the sequencer
        level compilation functions and combining them into a single dictionary.

        Parameters
        ----------
        debug_mode
            Debug mode can modify the compilation process,
            so that debugging of the compilation process is easier.
        repetitions
            Number of times execution the schedule is repeated.
        sequence_to_file
            Dump waveforms and program dict to JSON file, filename stored in
            `SequencerCompiler.settings.seq_fn`.

        Returns
        -------
        :
            The compiled program corresponding to this module.
            It contains an entry for every sequencer under the key `"sequencers"`,
            acquisition channels data, and
            acquisition hardware mapping under the key `"acq_hardware_mapping"`,
            and the `"repetitions"` is an integer with
            the number of times the defined schedule is repeated.
            All the other generic settings are under the key `"settings"`.
            If the device is not actually used,
            and an empty program is compiled, None is returned instead.

        """
        program: dict[str, Any] = {}

        # `sequence_to_file` of a module can be `True` even if its `False` for a cluster
        if sequence_to_file is None or sequence_to_file is False:
            # Explicit cast to bool to help type checker.
            sequence_to_file = bool(self.instrument_cfg.hardware_description.sequence_to_file)

        align_qasm_fields = debug_mode

        if self.supports_acquisition:
            program["acq_hardware_mapping"] = {}

        program["sequencers"] = {}
        for seq_name, seq in self.sequencers.items():
            seq_program = seq.compile(
                repetitions=repetitions,
                sequence_to_file=sequence_to_file,
                align_qasm_fields=align_qasm_fields,
            )
            if seq_program is not None:
                program["sequencers"][seq_name] = seq_program
            if self.supports_acquisition:
                program["acq_hardware_mapping"][seq_name] = (
                    seq.qblox_acq_index_manager.acq_hardware_mapping()
                )

        if len(program) == 0:
            return {}

        program["settings"] = self._settings
        program["repetitions"] = repetitions

        return program
