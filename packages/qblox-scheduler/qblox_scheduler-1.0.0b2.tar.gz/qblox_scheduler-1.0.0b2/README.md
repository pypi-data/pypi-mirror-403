# qblox-scheduler

[![Pipelines](https://gitlab.com/qblox/packages/software/qblox-scheduler/badges/main/pipeline.svg)](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/pipelines/)
[![PyPi](https://img.shields.io/pypi/v/qblox-scheduler.svg)](https://pypi.org/project/qblox-scheduler)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/raw/main/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v0.json)](https://github.com/charliermarsh/ruff)
[![Unitary Fund](https://img.shields.io/badge/Supported%20By-UNITARY%20FUND-brightgreen.svg?style=flat)](https://unitary.fund)
[![Documentation](https://img.shields.io/badge/documentation-grey)](https://docs.qblox.com/en/main/)

![qblox-scheduler logo](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/raw/main/docs/source/images/Qblox%20Scheduler%20Logo%20Primary.svg)

`qblox-scheduler` is a Python module for writing quantum programs featuring a hybrid gate-pulse
control model with explicit timing control. This control model allows quantum gate and pulse-level
descriptions to be combined in a clearly defined and hardware-agnostic way. `qblox-scheduler` is
designed to allow experimentalists to easily define complex experiments. It produces synchronized
pulse schedules that are distributed to control hardware, after compiling these schedules into
control-hardware specific executable programs.

## Hardware/driver compatibility

**Qblox**

|  qblox-scheduler  |                            qblox-instruments                             |                                  Cluster firmware                                   |
| :---------------: | :----------------------------------------------------------------------: | :---------------------------------------------------------------------------------: |
| >= 1.0.0, \<2.0.0 | [>= 1.0.0, \<2.0.0](https://pypi.org/project/qblox-instruments/#history) | [>= 0.13.0, \<2.0.0](https://gitlab.com/qblox/releases/cluster_releases/-/releases) |

[<img src="https://gitlab.com/qblox/packages/software/qblox-scheduler/-/raw/main/docs/source/images/Qblox_logo.svg" alt="Qblox logo" width=200px/>](https://www.qblox.com)
&#160;

The software is free to use under the conditions specified in the
[license](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/raw/main/LICENSE).
