# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
#
# Copyright 2020-2025, Quantify Consortium
# Copyright 2025, Qblox B.V.
"""Python dataclasses for compilation to Qblox hardware."""

from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses import field as dataclasses_field
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Literal,
    Optional,
    TypeVar,
    Union,
)
from typing_extensions import Self

from dataclasses_json import DataClassJsonMixin
from qblox_instruments.qcodes_drivers.time import Polarity

from qblox_scheduler.backends.qblox.enums import LoCalEnum, SidebandCalEnum, TimetagTraceType
from qblox_scheduler.backends.types.common import PartialChannelPath
from qblox_scheduler.enums import TimeRef, TimeSource

from .channels import DigitalChannelDescription
from .filters import QbloxRealTimeFilter

if TYPE_CHECKING:
    from qblox_scheduler.backends.qblox_backend import (
        _ClusterCompilationConfig,
        _ClusterModuleCompilationConfig,
        _SequencerCompilationConfig,
    )


_ModuleSettingsT = TypeVar("_ModuleSettingsT", bound="BaseModuleSettings")
"""
Custom type to allow correct type inference from ``extract_settings_from_mapping`` for
child classes.
"""


@dataclass(frozen=True)
class LOSettings(DataClassJsonMixin):
    """Dataclass containing all the settings for a generic LO instrument."""

    power: dict[str, float]
    """Power of the LO source."""
    frequency: dict[str, Optional[float]]
    """The frequency to set the LO to."""


@dataclass
class DistortionSettings(DataClassJsonMixin):
    """Distortion correction settings for all Qblox modules."""

    exp0: QbloxRealTimeFilter = dataclasses_field(default_factory=QbloxRealTimeFilter)
    """The exponential overshoot correction 1 filter."""
    exp1: QbloxRealTimeFilter = dataclasses_field(default_factory=QbloxRealTimeFilter)
    """The exponential overshoot correction 2 filter."""
    exp2: QbloxRealTimeFilter = dataclasses_field(default_factory=QbloxRealTimeFilter)
    """The exponential overshoot correction 3 filter."""
    exp3: QbloxRealTimeFilter = dataclasses_field(default_factory=QbloxRealTimeFilter)
    """The exponential overshoot correction 4 filter."""
    fir: QbloxRealTimeFilter = dataclasses_field(default_factory=QbloxRealTimeFilter)
    """The FIR filter."""


@dataclass
class ExternalTriggerSyncSettings(DataClassJsonMixin):
    """Settings for synchronizing a cluster on an external trigger."""

    slot: int
    """Slot of the module receiving the incoming trigger (can be the CMM)."""
    channel: int
    """
    Channel that receives the incoming trigger.

    Note that this is the channel number on the front panel. When using a CMM, this should be 1.
    """
    input_threshold: Optional[float] = None
    """
    If a QTM module is used, this setting specifies the input threshold.

    If a CMM is used instead, this setting is ignored and the trigger signal must be TTL (>2.4 V).
    """
    trigger_timestamp: float = 0
    """What time the cluster should be set to upon receiving the trigger."""
    timeout: float = 1
    """The time the cluster will wait for the trigger to arrive."""
    format: str = "s"
    """The time unit for the ``trigger_timestamp`` and ``timeout`` parameters."""
    edge_polarity: Polarity = Polarity.RISING_EDGE
    """The edge polarity to trigger on."""
    sync_to_ref_clock: bool = False
    """If True, synchronizes to the next internal 10 MHz reference clock tick, by default False."""


@dataclass
class ClusterSettings(DataClassJsonMixin):
    """Shared settings between all the Qblox modules."""

    reference_source: Literal["internal", "external"]
    sync_on_external_trigger: Optional[ExternalTriggerSyncSettings] = None

    @classmethod
    def extract_settings_from_mapping(
        cls,
        mapping: _ClusterCompilationConfig,
    ) -> ClusterSettings:
        """
        Factory method that takes all the settings defined in the mapping and generates
        an instance of this class.

        Parameters
        ----------
        mapping
            The mapping dict to extract the settings from
        **kwargs
            Additional keyword arguments passed to the constructor. Can be used to
            override parts of the mapping dict.

        """
        return cls(
            reference_source=mapping.hardware_description.ref,
            sync_on_external_trigger=mapping.hardware_description.sync_on_external_trigger,
        )


@dataclass
class BaseModuleSettings(DataClassJsonMixin):
    """Shared settings between all the Qblox modules."""

    @classmethod
    def extract_settings_from_mapping(
        cls: type[_ModuleSettingsT],
        mapping: _ClusterModuleCompilationConfig,  # noqa: ARG003 not used
        **kwargs,
    ) -> _ModuleSettingsT:
        """
        Factory method that takes all the settings defined in the mapping and generates
        an instance of this class.

        Parameters
        ----------
        mapping
            The mapping dict to extract the settings from
        **kwargs
            Additional keyword arguments passed to the constructor. Can be used to
            override parts of the mapping dict.

        """
        return cls(**kwargs)


@dataclass
class AnalogModuleSettings(BaseModuleSettings):
    """Shared settings between all QCM/QRM modules."""

    offset_ch0_path_I: Optional[float] = None
    """The DC offset on the path_I of channel 0."""
    offset_ch0_path_Q: Optional[float] = None
    """The DC offset on the path_Q of channel 0."""
    offset_ch1_path_I: Optional[float] = None
    """The DC offset on path_I of channel 1."""
    offset_ch1_path_Q: Optional[float] = None
    """The DC offset on path_Q of channel 1."""
    out0_lo_freq_cal_type_default: LoCalEnum = LoCalEnum.OFF
    """
    Setting that controls whether the mixer of channel 0 is calibrated upon changing the
    LO and/or intermodulation frequency.
    """
    out1_lo_freq_cal_type_default: LoCalEnum = LoCalEnum.OFF
    """
    Setting that controls whether the mixer of channel 1 is calibrated upon changing the
    LO and/or intermodulation frequency.
    """
    in0_gain: Optional[int] = None
    """The gain of input 0."""
    in1_gain: Optional[int] = None
    """The gain of input 1."""
    distortion_corrections: list[DistortionSettings] = dataclasses_field(
        default_factory=lambda: [DistortionSettings() for _ in range(4)]
    )
    """Distortion correction settings."""


@dataclass
class BasebandModuleSettings(AnalogModuleSettings):
    """
    Settings for a baseband module.

    Class exists to ensure that the cluster baseband modules don't need special
    treatment in the rest of the code.
    """


@dataclass
class RFModuleSettings(AnalogModuleSettings):
    """
    Global settings for the module to be set in the InstrumentCoordinator component.
    This is kept separate from the settings that can be set on a per-sequencer basis,
    which are specified in :class:`~.AnalogSequencerSettings`.
    """

    lo0_freq: Optional[float] = None
    """The frequency of Output 0 (O1) LO. If left `None`, the parameter will not be set."""
    lo1_freq: Optional[float] = None
    """The frequency of Output 1 (O2) LO. If left `None`, the parameter will not be set."""
    lo2_freq: Optional[float] = None
    """The frequency of Output 2 (O3) LO. If left `None`, the parameter will not be set."""
    lo3_freq: Optional[float] = None
    """The frequency of Output 3 (O4) LO. If left `None`, the parameter will not be set."""
    lo4_freq: Optional[float] = None
    """The frequency of Output 4 (O5) LO. If left `None`, the parameter will not be set."""
    lo5_freq: Optional[float] = None
    """The frequency of Output 5 (O6) LO. If left `None`, the parameter will not be set."""
    out0_att: Optional[int] = None
    """The attenuation of Output 0 (O1)."""
    out1_att: Optional[int] = None
    """The attenuation of Output 1 (O2)."""
    out2_att: Optional[int] = None
    """The attenuation of Output 2 (O3)."""
    out3_att: Optional[int] = None
    """The attenuation of Output 3 (O4)."""
    out4_att: Optional[int] = None
    """The attenuation of Output 4 (O5)."""
    out5_att: Optional[int] = None
    """The attenuation of Output 5 (O6)."""
    in0_att: Optional[int] = None
    """The attenuation of Input 0 (I1)."""
    in1_att: Optional[int] = None
    """The attenuation of Input 1 (I2)."""

    @classmethod
    def extract_settings_from_mapping(
        cls, mapping: _ClusterModuleCompilationConfig, **kwargs: Optional[dict]
    ) -> RFModuleSettings:
        """
        Factory method that takes all the settings defined in the mapping and generates
        an :class:`~.RFModuleSettings` object from it.

        Parameters
        ----------
        mapping
            The compiler config to extract the settings from
        **kwargs
            Additional keyword arguments passed to the constructor. Can be used to
            override parts of the mapping dict.

        """
        # LO frequency setting names are
        # qblox-instruments hardcoded parameters.
        channel_name_to_lo_freq_setting: dict[str, str] = {
            "complex_output_0": "lo0_freq",
            "complex_output_1": "lo1_freq",
            "complex_output_2": "lo2_freq",
            "complex_output_3": "lo3_freq",
            "complex_output_4": "lo4_freq",
            "complex_output_5": "lo5_freq",
        }

        rf_settings = {}

        modulation_frequencies = mapping.hardware_options.modulation_frequencies
        if modulation_frequencies is not None:
            for portclock, path in mapping.portclock_to_path.items():
                pc_freqs = modulation_frequencies.get(portclock)
                lo_freq = pc_freqs.lo_freq if pc_freqs is not None else None
                if (
                    lo_freq_setting := channel_name_to_lo_freq_setting.get(path.channel_name)
                ) is not None:
                    rf_settings[lo_freq_setting] = lo_freq

        combined_settings = {**rf_settings, **kwargs}
        return cls(**combined_settings)


@dataclass
class TimetagModuleSettings(BaseModuleSettings):
    """
    Global settings for the module to be set in the InstrumentCoordinator component.
    This is kept separate from the settings that can be set on a per-sequencer basis,
    which are specified in :class:`~.TimetagSequencerSettings`.
    """


@dataclass
class DCModuleSettings(BaseModuleSettings):
    """Settings for a DC module (QSM)."""

    NUM_CHANNELS: ClassVar[int] = 8
    """Number of IO channels available on a QSM."""

    source_mode: dict[int, Literal["v_source", "i_source", "ground", "open"]] = field(
        default_factory=dict
    )
    """
    Dictionary containing the sourcing behaviour mode (values) that should be applied
    to a certain IO channel (keys).
    """
    measure_mode: dict[
        int, Literal["automatic", "coarse", "fine_nanoampere", "fine_picoampere"]
    ] = field(default_factory=dict)
    """
    Dictionary containing the measurement precision mode (values) that should be applied
    to a certain IO channel (keys).
    """
    slew_rate: dict[int, float] = field(default_factory=dict)
    """
    Dictionary containing the maximum rate in volt/second (values) at which a certain
    IO channel (keys) can linearly change its output voltage or current [QSM modules].
    """
    integration_time: dict[int, float] = field(default_factory=dict)
    """
    Dictionary containing the integration time in seconds (values) that should be applied
    to a certain IO channel (keys).
    """
    safe_voltage_range: dict[int, tuple[float, float]] = field(default_factory=dict)
    """
    Dictionary containing the voltage limits -min, +max (values) that should be applied
    to a certain IO channel (keys) to protect the device against accidental overvolting.
    """

    @classmethod
    def extract_settings_from_mapping(
        cls,
        mapping: _ClusterModuleCompilationConfig,
        **kwargs,
    ) -> Self:
        """
        Override the base factory method to extract the settings from QSM-like format.

        Example: ``{"source_mode": {"cluster0.module1": "ground"}}``

        At this point each hardware option should only have paths corresponding to the module
        being loaded. If the path doesn't contain a channel name, we assume the setting
        needs to be applied to all IO channels and distribute it as such.
        """
        for field_name in mapping.hardware_options.model_fields_set:
            if (setting := getattr(mapping.hardware_options, field_name)) is not None:
                kwargs[field_name] = {}
                for path, value in setting.items():
                    cp = PartialChannelPath.from_path(path)
                    channels = (
                        [cp.channel_idx]
                        if cp.channel_name is not None
                        else list(range(cls.NUM_CHANNELS))
                    )
                    kwargs[field_name].update(dict.fromkeys(channels, value))

        return super().extract_settings_from_mapping(mapping, **kwargs)


@dataclass
class ThresholdedAcqTriggerReadSettings(DataClassJsonMixin):
    """Settings for reading from a trigger address."""

    thresholded_acq_trigger_invert: bool = False
    """
    If true, inverts the comparison result that is read from the trigger network address
    counter.
    """
    thresholded_acq_trigger_count: Optional[int] = None
    """
    Sets the threshold for the counter on the specified trigger address.
    """


@dataclass
class SequencerSettings(DataClassJsonMixin):
    """
    Sequencer level settings.

    In the Qblox driver these settings are typically recognized by parameter names of
    the form ``"{module}.sequencer{index}.{setting}"`` (for allowed values see
    `Cluster QCoDeS parameters
    <https://docs.qblox.com/en/main/api_reference/sequencer.html#cluster-qcodes-parameters>`__).
    These settings are set once and will remain unchanged after, meaning that these
    correspond to the "slow" QCoDeS parameters and not settings that are changed
    dynamically by the sequencer.

    These settings are mostly defined in the hardware configuration under each
    port-clock key combination or in some cases through the device configuration
    (e.g. parameters related to thresholded acquisition).
    """

    sync_en: bool
    """Enables party-line synchronization."""
    channel_name: str
    """Specifies the channel identifier of the hardware config (e.g. `complex_output_0`)."""
    channel_name_measure: Union[list[str], None]
    """Extra channel name necessary to define a `Measure` operation."""
    connected_output_indices: tuple[int, ...]
    """Specifies the indices of the outputs this sequencer produces waveforms for."""
    connected_input_indices: tuple[int, ...]
    """Specifies the indices of the inputs this sequencer collects data for."""
    sequence: Optional[dict[str, Any]] = None
    """JSON compatible dictionary holding the waveforms and program for the
    sequencer."""
    seq_fn: Optional[str] = None
    """Filename of JSON file containing a dump of the waveforms and program."""
    thresholded_acq_trigger_write_en: Optional[bool] = None
    """Enables mapping of thresholded acquisition results to the trigger network."""
    thresholded_acq_trigger_write_address: Optional[int] = None
    """The trigger address that thresholded acquisition results are written to."""
    thresholded_acq_trigger_write_invert: bool = False
    """If True, inverts the trigger before writing to the trigger network."""
    thresholded_acq_trigger_read_settings: dict[int, ThresholdedAcqTriggerReadSettings] = (
        dataclasses_field(default_factory=dict)
    )
    """Settings for reading from a trigger address."""

    @classmethod
    def initialize_from_compilation_config(
        cls,
        sequencer_cfg: _SequencerCompilationConfig,
        connected_output_indices: tuple[int, ...],
        connected_input_indices: tuple[int, ...],
    ) -> SequencerSettings:
        """
        Instantiates an instance of this class, with initial parameters determined from
        the sequencer compilation config.

        Parameters
        ----------
        sequencer_cfg
            The sequencer compilation_config.
        connected_output_indices
            Specifies the indices of the outputs this sequencer produces waveforms for.
        connected_input_indices
            Specifies the indices of the inputs this sequencer collects data for.

        Returns
        -------
        : SequencerSettings
            A SequencerSettings instance with initial values.

        """
        return cls(
            sync_en=True,
            channel_name=sequencer_cfg.channel_name,
            channel_name_measure=sequencer_cfg.channel_name_measure,
            connected_output_indices=connected_output_indices,
            connected_input_indices=connected_input_indices,
        )


@dataclass
class AnalogSequencerSettings(SequencerSettings):
    """
    Sequencer level settings.

    In the Qblox driver these settings are typically recognized by parameter names of
    the form ``"{module}.sequencer{index}.{setting}"`` (for allowed values see
    `Cluster QCoDeS parameters
    <https://docs.qblox.com/en/master/api_reference/sequencer.html#cluster-qcodes-parameters>`__).
    These settings are set once and will remain unchanged after, meaning that these
    correspond to the "slow" QCoDeS parameters and not settings that are changed
    dynamically by the sequencer.

    These settings are mostly defined in the hardware configuration under each
    port-clock key combination or in some cases through the device configuration
    (e.g. parameters related to thresholded acquisition).
    """

    nco_en: bool = False
    """
    Specifies whether the NCO will be used or not.
    Note: this setting has no effect on QRC, because NCO is always on for QRC.
    """
    init_offset_awg_path_I: float = 0.0
    """Specifies what value the sequencer offset for AWG path_I will be reset to
    before the start of the experiment."""
    init_offset_awg_path_Q: float = 0.0
    """Specifies what value the sequencer offset for AWG path_Q will be reset to
    before the start of the experiment."""
    init_gain_awg_path_I: float = 1.0
    """Specifies what value the sequencer gain for AWG path_I will be reset to
    before the start of the experiment."""
    init_gain_awg_path_Q: float = 1.0
    """Specifies what value the sequencer gain for AWG path_Q will be reset to
    before the start of the experiment."""
    modulation_freq: Optional[float] = None
    """Specifies the frequency of the modulation."""
    mixer_corr_phase_offset_degree: Optional[float] = None
    """The phase shift to apply between the I and Q channels, to correct for quadrature
    errors."""
    mixer_corr_gain_ratio: Optional[float] = None
    """The gain ratio to apply in order to correct for imbalances between the I and Q
    paths of the mixer."""
    auto_sideband_cal: SidebandCalEnum = SidebandCalEnum.OFF
    """
    Setting that controls whether the mixer is calibrated upon changing the
    intermodulation frequency.
    """
    integration_length_acq: Optional[int] = None
    """Integration length for acquisitions. Must be a multiple of 4 ns."""
    thresholded_acq_threshold: Optional[float] = None
    """The sequencer discretization threshold for discretizing the phase rotation result."""
    thresholded_acq_rotation: Optional[float] = None
    """The sequencer integration result phase rotation in degrees."""
    ttl_acq_input_select: Optional[int] = None
    """Selects the input used to compare against
    the threshold value in the TTL trigger acquisition path."""
    ttl_acq_threshold: Optional[float] = None
    """
    For QRM modules only, sets the threshold value with which to compare the input ADC
    values of the selected input path.
    """
    ttl_acq_auto_bin_incr_en: Optional[bool] = None
    """Selects if the bin index is automatically incremented when acquiring multiple triggers."""

    @classmethod
    def initialize_from_compilation_config(
        cls,
        sequencer_cfg: _SequencerCompilationConfig,
        connected_output_indices: tuple[int, ...],
        connected_input_indices: tuple[int, ...],
    ) -> AnalogSequencerSettings:
        """
        Instantiates an instance of this class, with initial parameters determined from
        the sequencer compilation config.

        Parameters
        ----------
        sequencer_cfg
            The sequencer compilation_config.
        connected_output_indices
            Specifies the indices of the outputs this sequencer produces waveforms for.
        connected_input_indices
            Specifies the indices of the inputs this sequencer collects data for.

        Returns
        -------
        : AnalogSequencerSettings
            A AnalogSequencerSettings instance with initial values.

        """
        modulation_freq = (
            sequencer_cfg.modulation_frequencies.interm_freq
            if sequencer_cfg.modulation_frequencies is not None
            else None
        )
        # Allow NCO to be permanently disabled via `"interm_freq": 0` in the hardware config
        nco_en: bool = not (
            modulation_freq == 0
            or isinstance(sequencer_cfg.hardware_description, DigitalChannelDescription)
            or len(connected_output_indices) == 0
        )

        # TODO: there must be a way to make this nicer
        init_offset_awg_path_I = (
            sequencer_cfg.sequencer_options.init_offset_awg_path_I
            if sequencer_cfg.sequencer_options is not None
            else 0.0
        )
        init_offset_awg_path_Q = (
            sequencer_cfg.sequencer_options.init_offset_awg_path_Q
            if sequencer_cfg.sequencer_options is not None
            else 0.0
        )
        init_gain_awg_path_I = (
            sequencer_cfg.sequencer_options.init_gain_awg_path_I
            if sequencer_cfg.sequencer_options is not None
            else 1.0
        )
        init_gain_awg_path_Q = (
            sequencer_cfg.sequencer_options.init_gain_awg_path_Q
            if sequencer_cfg.sequencer_options is not None
            else 1.0
        )
        mixer_phase_error = (
            sequencer_cfg.mixer_corrections.phase_error
            if sequencer_cfg.mixer_corrections is not None
            else None
        )
        mixer_amp_ratio = (
            sequencer_cfg.mixer_corrections.amp_ratio
            if sequencer_cfg.mixer_corrections is not None
            else None
        )
        auto_sideband_cal = (
            sequencer_cfg.mixer_corrections.auto_sideband_cal
            if sequencer_cfg.mixer_corrections is not None
            else SidebandCalEnum.OFF
        )
        ttl_acq_threshold = (
            sequencer_cfg.sequencer_options.ttl_acq_threshold
            if sequencer_cfg.sequencer_options is not None
            else None
        )

        return cls(
            nco_en=nco_en,
            sync_en=True,
            channel_name=sequencer_cfg.channel_name,
            channel_name_measure=sequencer_cfg.channel_name_measure,
            connected_output_indices=connected_output_indices,
            connected_input_indices=connected_input_indices,
            init_offset_awg_path_I=init_offset_awg_path_I,
            init_offset_awg_path_Q=init_offset_awg_path_Q,
            init_gain_awg_path_I=init_gain_awg_path_I,
            init_gain_awg_path_Q=init_gain_awg_path_Q,
            modulation_freq=modulation_freq,
            mixer_corr_phase_offset_degree=mixer_phase_error,
            mixer_corr_gain_ratio=mixer_amp_ratio,
            ttl_acq_threshold=ttl_acq_threshold,
            auto_sideband_cal=auto_sideband_cal,
        )


@dataclass
class TimetagSequencerSettings(SequencerSettings):
    """
    Sequencer level settings.

    In the Qblox driver these settings are typically recognized by parameter names of
    the form ``"{module}.sequencer{index}.{setting}"`` (for allowed values see
    `Cluster QCoDeS parameters
    <https://docs.qblox.com/en/master/api_reference/sequencer.html#cluster-qcodes-parameters>`__).
    These settings are set once and will remain unchanged after, meaning that these
    correspond to the "slow" QCoDeS parameters and not settings that are changed
    dynamically by the sequencer.

    These settings are mostly defined in the hardware configuration under each
    port-clock key combination or in some cases through the device configuration
    (e.g. parameters related to thresholded acquisition).
    """

    analog_threshold: Optional[float] = None
    """The settings that determine when an analog voltage is counted as a pulse."""
    time_source: Optional[TimeSource] = None
    """Selects the timetag data source for timetag acquisitions."""
    time_ref: Optional[TimeRef] = None
    """Selects the time reference that the timetag is recorded in relation to."""
    time_ref_channel: Optional[int] = None
    """
    If using TimeRef.PORT, this setting specifies the channel index (on the same module) belonging
    to that port.
    """
    scope_trace_type: Optional[TimetagTraceType] = None
    """Set to True if the program on this sequencer contains a scope/trace acquisition."""
    trace_acq_duration: Optional[int] = None
    """Duration of the trace acquisition (if any) done with this sequencer."""
    thresholded_acq_trigger_write_address_low: int = 0
    thresholded_acq_trigger_write_address_mid: int = 0
    thresholded_acq_trigger_write_address_high: int = 0
    thresholded_acq_trigger_write_address_invalid: int = 0
    thresholded_acq_trigger_write_threshold_low: Optional[int] = None
    """
    Optional threshold value used for the upd_thres Q1ASM instruction if ThresholdedTriggerCount is
    scheduled.
    """
    thresholded_acq_trigger_write_threshold_high: Optional[int] = None
    """
    Optional threshold value used for the upd_thres Q1ASM instruction if ThresholdedTriggerCount is
    scheduled.
    """

    def __post_init__(self) -> None:
        self._validate_io_indices_no_channel_map()

    def _validate_io_indices_no_channel_map(self) -> None:
        """
        There is no channel map in the QTM yet, so there can be only one connected
        index: either input or output.
        """
        if len(self.connected_input_indices) > 1 or len(self.connected_output_indices) > 1:
            raise ValueError(
                "Too many connected inputs or outputs for a QTM sequencer. "
                f"{self.connected_input_indices=}, {self.connected_output_indices=}."
            )

        if len(self.connected_output_indices) == 1 and len(self.connected_input_indices) == 1:
            raise ValueError(
                "A QTM sequencer cannot be connected to both an output and an input port."
            )

    @classmethod
    def initialize_from_compilation_config(
        cls,
        sequencer_cfg: _SequencerCompilationConfig,
        connected_output_indices: tuple[int, ...],
        connected_input_indices: tuple[int, ...],
    ) -> TimetagSequencerSettings:
        """
        Instantiates an instance of this class, with initial parameters determined from
        the sequencer compilation config.

        Parameters
        ----------
        sequencer_cfg
            The sequencer compilation config.
        connected_output_indices
            Specifies the indices of the outputs this sequencer produces waveforms for.
        connected_input_indices
            Specifies the indices of the inputs this sequencer collects data for.

        Returns
        -------
        : SequencerSettings
            A SequencerSettings instance with initial values.

        """
        return cls(
            sync_en=True,
            channel_name=sequencer_cfg.channel_name,
            channel_name_measure=sequencer_cfg.channel_name_measure,
            connected_output_indices=connected_output_indices,
            connected_input_indices=connected_input_indices,
            analog_threshold=(
                sequencer_cfg.digitization_thresholds.analog_threshold
                if sequencer_cfg.digitization_thresholds is not None
                else None
            ),
        )


__all__ = [
    "AnalogModuleSettings",
    "AnalogSequencerSettings",
    "BaseModuleSettings",
    "BasebandModuleSettings",
    "ClusterSettings",
    "DCModuleSettings",
    "DistortionSettings",
    "ExternalTriggerSyncSettings",
    "LOSettings",
    "RFModuleSettings",
    "SequencerSettings",
    "ThresholdedAcqTriggerReadSettings",
    "TimetagModuleSettings",
    "TimetagSequencerSettings",
]
