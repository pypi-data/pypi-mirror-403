from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest
from qcodes.parameters.parameter import ManualParameter

from qblox_scheduler.enums import BinMode, TimeRef, TimeSource
from qblox_scheduler.gettables import ScheduleGettable
from qblox_scheduler.helpers.mock_instruments import MockLocalOscillator
from qblox_scheduler.instrument_coordinator.components.generic import (
    GenericInstrumentCoordinatorComponent,
)
from qblox_scheduler.operations.gate_library import Measure
from qblox_scheduler.operations.pulse_library import SquarePulse
from qblox_scheduler.schedules.schedule import TimeableSchedule
from quantify_core.data.handling import set_datadir

if TYPE_CHECKING:
    from qblox_scheduler.device_under_test.nv_element import BasicElectronicNVElement
    from qblox_scheduler.device_under_test.quantum_device import QuantumDevice
    from qblox_scheduler.instrument_coordinator import InstrumentCoordinator
    from quantify_core.measurement.control import MeasurementControl


@pytest.mark.deprecated
def test_timetag_measurement_control(
    mocker,
    make_cluster_component,
    mock_setup_basic_nv_qblox_hardware,
    tmp_analysis_test_data_dir,
):
    ic: InstrumentCoordinator = mock_setup_basic_nv_qblox_hardware["instrument_coordinator"]
    cluster = make_cluster_component(name="cluster0")

    mocker.patch.object(
        cluster.instrument.module5,
        "get_acquisitions",
        return_value={
            "0": {
                "index": 0,
                "acquisition": {
                    "bins": {
                        "count": [4.0, 4.0, 4.0],
                        "timedelta": [235520.0, 233472.0, 237568.0],
                        "threshold": [1.0, 1.0, 1.0],
                        "avg_cnt": [1, 1, 1],
                    }
                },
            }
        },
    )
    mocker.patch.object(
        cluster.instrument.module5.io_channel4,
        "get_scope_data",
        return_value=[],
    )

    ic.add_component(cluster)

    red_laser = MockLocalOscillator("red_laser2")
    ic.add_component(GenericInstrumentCoordinatorComponent("generic"))
    ic.add_component(GenericInstrumentCoordinatorComponent(red_laser))

    qdev: QuantumDevice = mock_setup_basic_nv_qblox_hardware["quantum_device"]
    qdev.cfg_sched_repetitions = 3

    qe1: BasicElectronicNVElement = mock_setup_basic_nv_qblox_hardware["qe1"]
    qe1.measure.acq_duration = 10e-6
    qe1.measure.pulse_amplitude = 1.0
    qe1.measure.pulse_duration = 200e-9
    qe1.measure.time_source = TimeSource.LAST
    qe1.measure.time_ref = TimeRef.START
    qe1.clock_freqs.ge0 = 470.4e12

    def sched_fn(repetitions=1):
        sched = TimeableSchedule("sched", repetitions=repetitions)

        sched.add(Measure("qe1", acq_protocol="Timetag", bin_mode=BinMode.APPEND))

        square_pulse = SquarePulse(
            amp=1.0, duration=200e-9, port="qe1:optical_control", clock="qe1.ge0"
        )
        sched.add(square_pulse, rel_time=200e-9, ref_pt="start")
        for rel_time in (1e-6, 2e-6, 3e-6):
            sched.add(square_pulse, rel_time=rel_time, ref_pt="start")

        return sched

    gettable = ScheduleGettable(
        quantum_device=qdev,
        schedule_function=sched_fn,
        schedule_kwargs={},
        batched=True,
    )

    settable = ManualParameter("dummy", unit="rep")
    setattr(settable, "batched", True)  # noqa: B010
    setpoints = np.array([0, 1, 2])

    mc: MeasurementControl = mock_setup_basic_nv_qblox_hardware["meas_ctrl"]
    mc.settables(settable)
    mc.setpoints(setpoints)
    mc.gettables(gettable)

    set_datadir(tmp_analysis_test_data_dir)
    dataset = mc.run()
    assert np.array_equal(dataset.x0, setpoints)
    assert np.array_equal(dataset.y0, np.array([115.0, 114.0, 116.0]))


@pytest.mark.deprecated
def test_qtm_trace_measurement_control(
    mocker,
    make_cluster_component,
    mock_setup_basic_nv_qblox_hardware,
):
    ic: InstrumentCoordinator = mock_setup_basic_nv_qblox_hardware["instrument_coordinator"]
    cluster = make_cluster_component(name="cluster0")

    dummy_data = [0] * int(10e3)
    mocker.patch.object(
        cluster.instrument.module5,
        "get_acquisitions",
        return_value={
            "0": {
                "index": 0,
                "acquisition": {
                    "bins": {
                        "count": [],
                        "timedelta": [],
                        "threshold": [],
                        "avg_cnt": [],
                    }
                },
            }
        },
    )
    mocker.patch.object(
        cluster.instrument.module5.io_channel4,
        "get_scope_data",
        return_value=dummy_data,
    )

    ic.add_component(cluster)

    red_laser = MockLocalOscillator("red_laser2")
    ic.add_component(GenericInstrumentCoordinatorComponent("generic"))
    ic.add_component(GenericInstrumentCoordinatorComponent(red_laser))

    qdev: QuantumDevice = mock_setup_basic_nv_qblox_hardware["quantum_device"]

    qe1: BasicElectronicNVElement = mock_setup_basic_nv_qblox_hardware["qe1"]
    qe1.measure.acq_duration = 10e-6
    qe1.measure.pulse_amplitude = 1.0
    qe1.measure.pulse_duration = 200e-9
    qe1.clock_freqs.ge0 = 470.4e12

    def sched_fn(repetitions=1):
        sched = TimeableSchedule("sched", repetitions=repetitions)

        sched.add(Measure("qe1", acq_protocol="Trace", bin_mode=BinMode.FIRST))

        square_pulse = SquarePulse(
            amp=1.0, duration=200e-9, port="qe1:optical_control", clock="qe1.ge0"
        )
        sched.add(square_pulse, rel_time=200e-9, ref_pt="start")
        for rel_time in (1e-6, 2e-6, 3e-6):
            sched.add(square_pulse, rel_time=rel_time, ref_pt="start")

        return sched

    gettable = ScheduleGettable(
        quantum_device=qdev,
        schedule_function=sched_fn,
        schedule_kwargs={},
        batched=True,
        max_batch_size=int(10e3),
    )

    settable = ManualParameter("time", unit="ns")
    setattr(settable, "batched", True)  # noqa: B010
    setpoints = np.arange(10e3)

    mc: MeasurementControl = mock_setup_basic_nv_qblox_hardware["meas_ctrl"]
    mc.settables(settable)
    mc.setpoints(setpoints)
    mc.gettables(gettable)

    set_datadir()
    dataset = mc.run()
    assert np.array_equal(dataset.x0, setpoints)
    assert np.array_equal(dataset.y0, np.zeros((int(10e3),)))
