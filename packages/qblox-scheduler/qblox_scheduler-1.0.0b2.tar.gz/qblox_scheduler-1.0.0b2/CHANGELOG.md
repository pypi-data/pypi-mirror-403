# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0b2] - 2025-01-30

### Added

- Expose `qblox_scheduler.operations.DType`, `qblox_scheduler.operations.arange`, and
  `qblox_scheduler.operations.linspace`.
  [!115](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/115)
- Added `get_unit` method to submodules to retrieve the unit of a given parameter.
  [!111](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/111)
- Exceeding the maximum waveform amplitude or gain now raises an error during compilation, and a
  warning in the pulse diagram.
  [!136](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/136)
- Add `Schedule.repeat()` method for repetitions without need for variables.
  [!158](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/158)
- Add progress bar when hybrid loops are executed.
  [!164](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/164)
- Implement merging of subsequent Rz gates.
  [!159](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/159)
- Added automatic RF output switching if `rf_output_on` is set to `"auto"`. Introduced a back-end
  compiler pass that inserts `RFSwitchToggle` operations for RF pulses.
  [!35](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/35),
  [!193](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/193)

### Changed

- Refactored the factory functions in `qblox-scheduler.backends.qblox.operations.pulse_factories` to
  use the new `loop` feature instead of `StitchedPulse`.
  [!50](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/50)
- Included warning about slowness when calling the `to_yaml` and `from_yaml` methods of
  `qblox_scheduler` models.
- Improved `arange` API to match Python and numpy's.
  [!157](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/157)
- Return empty dataset instead of `None` when no experiment data is available.
  [!135](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/135)
- Simplified the structure of `Operation.data`. The `"pulse_info"` and `"acquisition_info"` fields
  now contain a single dictionary instead of a list of dictionaries. In addition, `"pulse_info"` and
  `"acquisition_info"` cannot both be a defined in the same `Operation`.
  [!107](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/107)
- Raise acquisition bin limits and limit per-module instead of per-sequencer.
  [!187](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge-requests/187)

### Removed

- Removed the `StitchedPulse` class.
  [!50](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/50)

### Fixed

- Omitted `MeasurementControl` and `InstrumentCoordinator` from `QuantumDevice` serialization.
  [!120](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/120)
- Allowed YAML serialization of custom `DeviceElement` and `Edge`.
  [!110](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/110)
- Fixed allowing `SSBIntegrationComplex` and trigger count acquisition protocols to work on the same
  sequencer. [!151](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/151)
- Allow instrument types other than `Cluster` in the hardware configuration passed to
  `HardwareAgent`.
  [!154](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/154)
- `HardwareAgent.latest_compiled_schedule` now always holds the latest compiled `TimeableSchedule`
  when passing a `Schedule` to `run()`.
  [!148](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/148)

## [1.0.0b1] - 2025-10-01

### Added

- Added informative error message when passing an old quantify_scheduler `QuantumDevice`
  configuration to `QuantumDevice.from_json_file`.
  [!138](https://gitlab.com/qblox/projects/quantify-scheduler-private/-/merge_requests/138)
- Added amplitude loops.
  [!17](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/17)
  [!19](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/19)
  [!27](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/27)
- Added unrolled time loops.
  [!26](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/26)
- Added frequency loops.
  [!21](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/21)
  [!40](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/40)
- Added HardwareAgent.
  [!38](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/39)
  [!49](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/49)
- Added average_append BinMode.
  [!46](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/46)
- Added support for DRAGPulse amplitude loops.
  [!42](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/42)
- Added support for loop variables inside acquisition coordinates.
  [!52](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/52)
- Added analysis classes to `qblox_scheduler.analysis module`.
  [!68](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/68)
- Added helper function `qblox_scheduler.analysis.acq_coords_to_dims` to convert acquisition data's
  coordinates to dimensions.
  [!59](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/59)
- Added support for multiplication/division expressions with variables of amplitude loops. The
  scaling factor is applied directly to the generated waveform.
  [!60](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/60)
- Added hybrid loops.
  [!72](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/72)
- CLI tool that migrates python scripts, notebooks and configs to use the `qblox-scheduler`
  namespace [!67](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/67),
  [!90](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/90)
- Added `qblox_scheduler.backends.qblox.operations.long_chirp_pulse`: a chirp pulse that consists of
  shorter waveform chunks and `SetClockFrequency` instructions to reduce waveform memory usage.
  [!102](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/102/diffs)
- Added the ability to sweep over phase shift.
  [!119](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/119)
- Added object that handles the data storing/loading, namely the `AnalysisDataContainer`.
  [!89](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/89?diff_head=true)
- Added an optional `gain` parameter to `NumericalPulse`, which can be controlled by
  `DType.AMPLITUDE` sweep parameters.
  [!113](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/113)

### Changed

- The default bin mode for acquisitions now defaults to `BinMode.AVERAGE_APPEND`, if that bin mode
  is supported. Additionally, `Measure` gates that don't specify a bin mode will also adopt this new
  default behavior (Previously, the default was `BinMode.AVERAGE` for transmon and spin qubits and
  `BinMode.APPEND` for NV centers).
  [!78](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/78)
- `DRAGPulse` operation and `drag` waveform function: renamed the `G_amp` parameter to `amplitude`
  and the `D_amp` parameter to `beta`.
  [!74](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/74)
- In the `Rxy`-derived gate definitions for `BasicTransmonElement`, `motzoi` has been renamed to
  `beta`. [!74](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/74)
- Enabled much more acquisitions within a schedule by reusing registers. This is especially useful
  for time loops, where acquisitions in a loop unrolls to multiple operations.
  [!77](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/77)
- Acquisitions within a conditional either need to be averaged or use `APPEND` or `AVERAGE` bin mode
  instead of `AVERAGE_APPEND`. This limitation is only supposed to be temporary.
  [!77](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/77)
- `Schedule` has now been reimplemented; the old schedule class is available as
  `qblox_scheduler.schedules.schedule.TimeableBase` and can still be used. Despite efforts to
  preserve as much API compatibility as possible, minor API details may have changed.
- Renamed `QbloxFilterConfig` to `FilterConfig`.
  [!43](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/43)
- Renamed `QbloxFilterMarkerDelay` to
  `FilterMarkerDelay`.[!43](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/43)
- Moved all `qblox_scheduler.backends.qblox.operations` to
  `qblox_scheduler.operations.hardware_operations`, including submodules.
  [!43](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/43)
- `ConditionalOperation` now has a default `hardware_buffer_time` of 4ns.
  [!43](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/43)
- Move the `timeout` parameter from the initializers of experiment `Steps` to the `run` methods, so
  that every step uses the timeout passed to `HardwareAgent.run()`.
  [!106](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/106)
- Raise an error when the key specified in `SetParameter`, `SetHardwareOption` or
  `SetHardwareDescriptionField` does not appear in the configuration, and add the option
  `create_new` (by default `False`) to suppress this error and create a new entry in the relevant
  config. [!105](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/105)
- The default of `combine_waveforms_on_same_port` for pulse plotting is now True (was False)
  [!122](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/122)

### Removed

- Removed `max_value` validator from `RxyGaussian.duration`, `DispersiveMeasurementSpin.duration`,
  `IdlingReset.duration` and `DispersiveMeasurement.duration`.
  [!57](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/57)
- Removed ZI backend, profiled, deprecated, and dead code.
  [!25](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/25)
- Removed MockBackend.
  [!47](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/47)
- Removed `qblox_scheduler.operations.ConditionalOperation` and replaced its implementation by
  `qblox_scheduler.qblox.operations.ConditionalOperation`
  [!43](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/43)

### Fixed

- Fixed a math error in the `drag` waveform where the derivative component was incorrectly divided
  by `sigma` instead of `sigma**2`. When using the `DRAGPulse`, the `beta` parameter now needs to be
  scaled by a factor of `sigma` to maintain the same pulse shape.
  [!74](https://gitlab.com/qblox/projects/qblox-scheduler-private/-/merge_requests/74)
- Fixed a bug where adding a loop to a `Schedule`, in the situation where the whole `Schedule` could
  be lowered to a `TimeableSchedule`, would reset the repetitions to 1.
  [!91](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/91)
- Fixed support for spin qubits and spin edges in device (de)serialization
  [!95](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/95)
- Fixed a bug where the offsets in `long_ramp_pulse` were incorrectly calculated.
  [!123](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/123)
- Fixed a bug where `nop` instructions were sometimes missing when they were needed for correct
  Q1ASM programs.
  [!112](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/merge_requests/112)

[1.0.0b1]: https://gitlab.com/qblox/packages/software/qblox-scheduler/-/tags/v1.0.0b1
[1.0.0b2]: https://gitlab.com/qblox/packages/software/qblox-scheduler/-/tags/v1.0.0b2
