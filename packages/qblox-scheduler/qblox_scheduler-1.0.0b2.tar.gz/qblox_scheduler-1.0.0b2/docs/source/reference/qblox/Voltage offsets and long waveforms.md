---
file_format: mystnb
kernelspec:
    name: python3

---
(sec-qblox-offsets-long)=

# Voltage offsets and long waveforms

```{code-cell} ipython3
---
mystnb:
  remove_code_source: true
  remove_code_outputs: true  
---

# in the hidden cells we include some code that checks for correctness of the examples
from tempfile import TemporaryDirectory
from qblox_scheduler import Schedule
from qblox_scheduler.device_under_test.quantum_device import QuantumDevice
from qblox_scheduler.operations.pulse_library import SquarePulse
from qblox_scheduler.resources import BasebandClockResource, ClockResource
from qblox_scheduler.backends.graph_compilation import SerialCompiler
from qblox_scheduler.analysis.data_handling import OutputDirectoryManager

temp_dir = TemporaryDirectory()
OutputDirectoryManager.set_datadir(temp_dir.name)



hardware_compilation_cfg = {
    "config_type": "QbloxHardwareCompilationConfig",
    "hardware_description": {
        "cluster0": {
            "instrument_type": "Cluster",
            "ref": "internal",
            "modules": {
                "1": {
                    "instrument_type": "QCM"
                },
                "2": {
                    "instrument_type": "QCM_RF"
                },
            }
        },
        "lo0": {"instrument_type": "LocalOscillator", "power": 20},
        "iq_mixer0": {"instrument_type": "IQMixer"},
    },
    "hardware_options": {
        "modulation_frequencies": {
            "q1:mw-q1.01": {
                "lo_freq": 5e9
            },
            "q2:mw-q2.01": {
                "lo_freq": 7e9
            },
            "q3:mw-q3.01": {
                "interm_freq": 50e6
            },
        },
    },
    "connectivity": {
        "graph": [
            ("cluster0.module1.complex_output_0", "q0:mw"),
            ("cluster0.module1.complex_output_1", "iq_mixer0.if"),
            ("lo0.output", "iq_mixer0.lo"),
            ("iq_mixer0.rf", "q1:mw"),
            ("cluster0.module2.complex_output_0", "q2:mw"),
            ("cluster0.module2.complex_output_1", "q3:mw"),
        ]
    }
}

quantum_device = QuantumDevice("DUT")
quantum_device.hardware_config = hardware_compilation_cfg
```

In this section we introduce how to use voltage offsets and build up long waveforms using [Qblox Cluster](https://www.qblox.com/products#cluster) modules.

(sec-qblox-offsets-long-voltage-offsets)=
## Voltage offsets

Qblox modules can set and hold a voltage on their outputs using the {class}`~qblox_scheduler.operations.pulse_library.VoltageOffset` operation. The operation supports real and complex outputs, and it has effectively zero duration, meaning it takes effect at the exact moment you schedule it, and you can schedule other operations simultaneously. It can be used as follows:

```{code-cell} ipython3
---
mystnb:
  number_source_lines: true
  remove_code_outputs: true
---

from qblox_scheduler.operations.pulse_library import VoltageOffset


voltage_offset_real = VoltageOffset(
    offset_path_I=0.5,
    offset_path_Q=0.0,
    port="q3:mw",
    clock="q3.01",
)

voltage_offset_complex = VoltageOffset(
    offset_path_I=0.5,
    offset_path_Q=0.5,
    port="q3:mw",
    clock="q3.01",
)

sched = Schedule("offset_sched")
sched.add_resource(ClockResource(name="q3.01", freq=9e9))

ref_op = sched.add(voltage_offset_real)

# It's possible to schedule a voltage offset simultaneously with a pulse
sched.add(voltage_offset_complex, ref_op=ref_op, rel_time=1e-7)
sched.add(SquarePulse(amp=1, duration=1e-7, port="q3:mw", clock="q3.01"))

compiler = SerialCompiler(name="compiler")
compiled_sched = compiler.compile(
    schedule=sched, config=quantum_device.generate_compilation_config()
)
```

Note that the offset will remain on the output until the schedule execution ends, or until a new voltage offset is set.

```{important}
While voltage offsets have effectively zero duration, the hardware does require 4 ns of "buffer" time after they are scheduled. That is, voltage offsets cannot be scheduled right at the end of the schedule, or at the end of a {ref}`sec-control-flow` block (e.g., a loop).

If you do want a voltage offset at those moments, it is necessary to leave some time (at least 4 ns) by inserting an {class}`~qblox_scheduler.operations.pulse_library.IdlePulse`.
```

For example, the following is not possible:

```{code-cell} ipython3
---
mystnb:
  number_source_lines: true
---

from qblox_scheduler.operations.pulse_library import IdlePulse

sched = Schedule("offset_sched")
sched.add_resource(ClockResource(name="q3.01", freq=9e9))

sched.add(
    VoltageOffset(offset_path_I=0.5, offset_path_Q=0.0, port="q3:mw", clock="q3.01")
)
sched.add(SquarePulse(amp=1, duration=1e-7, port="q3:mw", clock="q3.01"))
sched.add(
    VoltageOffset(offset_path_I=0.0, offset_path_Q=0.0, port="q3:mw", clock="q3.01")
)

compiler = SerialCompiler(name="compiler")
try:
    compiled_sched = compiler.compile(
        schedule=sched, config=quantum_device.generate_compilation_config()
    )
except RuntimeError as err:
    print(err)
```

Instead, some time should be left at the end like so:

```{code-cell} ipython3
---
mystnb:
  number_source_lines: true
---

sched = Schedule("offset_sched")
sched.add_resource(ClockResource(name="q3.01", freq=9e9))

sched.add(
    VoltageOffset(offset_path_I=0.5, offset_path_Q=0.0, port="q3:mw", clock="q3.01")
)
sched.add(SquarePulse(amp=1, duration=1e-7, port="q3:mw", clock="q3.01"))
sched.add(
    VoltageOffset(offset_path_I=0.0, offset_path_Q=0.0, port="q3:mw", clock="q3.01")
)
sched.add(IdlePulse(4e-9))

compiler = SerialCompiler(name="compiler")
compiled_sched = compiler.compile(
    schedule=sched, config=quantum_device.generate_compilation_config()
)
```

### Factory functions

For convenience, `qblox-scheduler` provides helper functions for the `square` ({func}`~qblox_scheduler.operations.hardware_operations.pulse_factories.long_square_pulse`), `ramp` ({func}`~qblox_scheduler.operations.hardware_operations.pulse_factories.long_ramp_pulse`) and `staircase` ({func}`~qblox_scheduler.operations.hardware_operations.pulse_factories.staircase_pulse`) waveforms for when they become too long to fit into the waveform memory of the hardware.

```{code-cell} ipython3
from qblox_scheduler.operations.hardware_operations import (
    long_ramp_pulse,
    long_square_pulse,
    staircase_pulse,
)


sched = Schedule("Basic long pulses")
sched.add(
    long_square_pulse(
        amp=0.5,
        duration=10e-6,
        port="q0:fl",
        clock=BasebandClockResource.IDENTITY,
    ),
)
sched.add(
    long_ramp_pulse(
        amp=1.0,
        duration=10e-6,
        port="q0:fl",
        offset=-0.5,
        clock=BasebandClockResource.IDENTITY,
    ),
    rel_time=5e-7,
)
sched.add(
    staircase_pulse(
        start_amp=-0.5,
        final_amp=0.5,
        num_steps=20,
        duration=10e-6,
        port="q0:fl",
        clock=BasebandClockResource.IDENTITY,
    ),
    rel_time=5e-7,
)

quantum_device = QuantumDevice("quantum_device")
device_compiler = SerialCompiler("Device compiler", quantum_device)

comp_sched = device_compiler.compile(sched)
comp_sched.plot_pulse_diagram(
    plot_backend="plotly", combine_waveforms_on_same_port=True
)
```

```{tip}
Add the argument `combine_waveforms_on_same_port=True` to `plot_pulse_diagram` to show the appearance of the final hardware output (default `combine_waveforms_on_same_port=False` shows individual pulse elements). 
```

Using these factory functions, the resulting square and staircase pulses use no waveform memory at all. The ramp pulse uses waveform memory for a short section of the waveform, which is repeated multiple times.
