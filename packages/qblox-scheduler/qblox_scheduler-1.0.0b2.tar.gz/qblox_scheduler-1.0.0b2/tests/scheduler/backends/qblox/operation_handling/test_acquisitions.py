# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
"""Tests for acquisitions module."""

from __future__ import annotations

import pprint
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
import xarray as xr
from qblox_instruments import (
    ClusterType,
    DummyBinnedAcquisitionData,
    DummyScopeAcquisitionData,
)
from qcodes.parameters.parameter import ManualParameter
from xarray import DataArray, Dataset

from qblox_scheduler import TimeableSchedule, waveforms
from qblox_scheduler.backends import SerialCompiler
from qblox_scheduler.backends.qblox import constants
from qblox_scheduler.backends.qblox.operation_handling import acquisitions
from qblox_scheduler.backends.qblox.qblox_acq_index_manager import (
    QbloxAcquisitionHardwareMapping,
)
from qblox_scheduler.backends.types import qblox as types
from qblox_scheduler.enums import BinMode
from qblox_scheduler.gettables import ScheduleGettable
from qblox_scheduler.helpers.generate_acq_channels_data import AcquisitionIndices
from qblox_scheduler.helpers.mock_instruments import MockLocalOscillator
from qblox_scheduler.instrument_coordinator.components.generic import (
    GenericInstrumentCoordinatorComponent,
)
from qblox_scheduler.instrument_coordinator.components.qblox import (
    _AnalogModuleComponent,
)
from qblox_scheduler.operations.acquisition_library import SSBIntegrationComplex
from qblox_scheduler.operations.control_flow_library import LoopOperation
from qblox_scheduler.operations.expressions import DType
from qblox_scheduler.operations.gate_library import Measure
from qblox_scheduler.operations.loop_domains import linspace
from qblox_scheduler.operations.pulse_library import (
    ShiftClockPhase,
    SquarePulse,
)
from qblox_scheduler.resources import ClockResource
from qblox_scheduler.schedules.schedule import AcquisitionChannelData
from qblox_scheduler.schedules.trace_schedules import (
    trace_schedule_circuit_layer,
)
from quantify_core.data.handling import set_datadir
from quantify_core.measurement import MeasurementControl
from tests.fixtures.mock_setup import close_instruments

if TYPE_CHECKING:
    from qblox_scheduler.backends.qblox.qasm_program import QASMProgram


class MockAcquisition(acquisitions.AcquisitionStrategyPartial):
    """Used for TestAcquisitionStrategyPartial."""

    def generate_data(self, wf_dict: dict[str, Any]):
        pass

    def _acquire_with_immediate_bin_index(self, qasm_program: QASMProgram):
        pass

    def _acquire_with_register_bin_index(self, qasm_program: QASMProgram):
        pass


class TestAcquisitionStrategyPartial:
    """
    There is some logic in the AcquisitionStrategyPartial class that deserves
    testing.
    """

    def test_operation_info_property(self):
        # arrange
        data = {"bin_mode": None, "acq_channel": 0, "acq_index": 0}
        op_info = types.OpInfo(name="", data=data, timing=0)
        strategy = MockAcquisition(op_info)

        # act
        from_property = strategy.operation_info

        # assert
        assert op_info == from_property

    @pytest.mark.parametrize(
        "bin_mode",
        [BinMode.AVERAGE, BinMode.APPEND, BinMode.SUM, BinMode.DISTRIBUTION, BinMode.FIRST],
    )
    def test_bin_mode(self, empty_qasm_program_qrm, bin_mode, mocker):
        # arrange
        data = {"bin_mode": bin_mode, "acq_channel": 0, "acq_index": 0}
        op_info = types.OpInfo(name="", data=data, timing=0)
        strategy = MockAcquisition(op_info)
        append_mock = mocker.patch.object(strategy, "_acquire_with_register_bin_index")
        average_mock = mocker.patch.object(strategy, "_acquire_with_immediate_bin_index")

        strategy.bin_idx_register = "R0" if bin_mode == BinMode.APPEND else None

        # act
        strategy.insert_qasm(empty_qasm_program_qrm)

        # assert
        if bin_mode == BinMode.APPEND:
            average_mock.assert_not_called()
            append_mock.assert_called_once()
        else:
            average_mock.assert_called_once()
            append_mock.assert_not_called()

    def test_invalid_bin_mode(self, empty_qasm_program_qrm):
        # arrange
        data = {"bin_mode": "nonsense", "acq_channel": 0, "acq_index": 0}
        op_info = types.OpInfo(name="", data=data, timing=0)
        strategy = MockAcquisition(op_info)

        # act
        with pytest.raises(RuntimeError) as exc:
            strategy.insert_qasm(empty_qasm_program_qrm)

        # assert
        assert (
            exc.value.args[0]
            == "Attempting to process an acquisition with unknown bin mode nonsense."
        )

    def test_start_acq_too_soon(self, empty_qasm_program_qrm):
        # arrange
        qasm = empty_qasm_program_qrm
        qasm.time_last_acquisition_triggered = 0
        data = {
            "bin_mode": "nonsense",
            "acq_channel": 0,
            "acq_index": 0,
            "duration": 1e-6,
        }
        op_info = types.OpInfo(name="", data=data, timing=0)
        strategy = MockAcquisition(op_info)

        # act
        with pytest.raises(ValueError) as exc:
            strategy.insert_qasm(qasm)

        # assert
        assert (
            exc.value.args[0] == "Attempting to start an acquisition at t=0 ns, while the last "
            "acquisition was started at t=0 ns. Please ensure a minimum interval of "
            "300 ns between acquisitions.\n\nError caused by acquisition:\n"
            "Acquisition  (t=0 to 1e-06)\ndata={'bin_mode': 'nonsense', "
            "'acq_channel': 0, 'acq_index': 0, 'duration': 1e-06}."
        )

    @pytest.mark.parametrize(
        "bin_mode",
        [BinMode.AVERAGE, BinMode.APPEND, BinMode.SUM, BinMode.DISTRIBUTION, BinMode.FIRST],
    )
    def test_bin_index_register_invalid(self, empty_qasm_program_qrm, bin_mode):
        # arrange
        data = {"bin_mode": bin_mode, "acq_channel": 0, "acq_index": 0}
        op_info = types.OpInfo(name="", data=data, timing=0)
        strategy = MockAcquisition(op_info)
        strategy.bin_idx_register = None if bin_mode == BinMode.APPEND else "R0"

        # act
        with pytest.raises(ValueError) as exc:
            strategy.insert_qasm(empty_qasm_program_qrm)

        # assert
        assert (
            exc.value.args[0] == f"Attempting to add acquisition with "
            f"binmode {bin_mode}. "
            f"bin_idx_register {'cannot' if bin_mode == BinMode.APPEND else 'must'} "
            f"be None."
        )


class TestSquareAcquisitionStrategy:
    @pytest.mark.parametrize("bin_mode", [BinMode.AVERAGE, BinMode.APPEND])
    def test_constructor(self, bin_mode):
        data = {"bin_mode": bin_mode, "acq_channel": 0, "acq_index": AcquisitionIndices(0, None, 1)}
        acquisitions.SquareAcquisitionStrategy(types.OpInfo(name="", data=data, timing=0))

    def test_generate_data(self):
        # arrange
        data = {"bin_mode": None, "acq_channel": 0, "acq_index": AcquisitionIndices(0, None, 1)}
        strategy = acquisitions.SquareAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        wf_dict = {}

        # act
        strategy.generate_data(wf_dict)

        # assert
        assert len(wf_dict) == 0

    def test_acquire_with_immediate_bin_index(self, empty_qasm_program_qrm):
        # arrange
        qasm = empty_qasm_program_qrm
        data = {
            "bin_mode": None,
            "acq_channel": 0,
            "acq_index": AcquisitionIndices(0, None, 1),
            "duration": 1e-6,
        }
        strategy = acquisitions.SquareAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        strategy.generate_data({})
        strategy.qblox_acq_index, strategy.qblox_acq_bin = 8, 1

        # act
        strategy._acquire_with_immediate_bin_index(qasm)

        # assert
        assert qasm.instructions == [["", "acquire", "8,1,4", ""]]

    def test_acquire_with_register_bin_index(self, empty_qasm_program_qrm):
        # arrange
        qasm = empty_qasm_program_qrm
        data = {
            "bin_mode": None,
            "acq_channel": 0,
            "acq_index": AcquisitionIndices(1, [], 1),
            "duration": 1e-6,
        }
        strategy = acquisitions.SquareAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        strategy.bin_idx_register = qasm.register_manager.allocate_register()
        strategy.generate_data({})
        strategy.qblox_acq_index = 5
        strategy.bin_mode = BinMode.APPEND

        # act
        strategy._acquire_with_register_bin_index(qasm)

        # assert
        assert qasm.instructions == [
            ["", "", "", ""],
            ["", "acquire", "5,R0,4", ""],
            ["", "add", "R0,1,R0", "# Increment bin_idx for ch0"],
            ["", "", "", ""],
        ]


class TestWeightedAcquisitionStrategy:
    @pytest.mark.parametrize("bin_mode", [BinMode.AVERAGE, BinMode.APPEND])
    def test_constructor(self, bin_mode):
        data = {"bin_mode": bin_mode, "acq_channel": 0, "acq_index": AcquisitionIndices(0, None, 1)}
        acquisitions.WeightedAcquisitionStrategy(types.OpInfo(name="", data=data, timing=0))

    def test_generate_data(self):
        # arrange
        duration = 1e-6
        t_test = np.arange(0, duration, step=1e-9)
        weights = [
            {
                "wf_func": "qblox_scheduler.waveforms.square",
                "amp": 1,
                "duration": duration,
            },
            {
                "wf_func": "qblox_scheduler.waveforms.square",
                "amp": 0,
                "duration": duration,
            },
        ]
        data = {
            "bin_mode": None,
            "acq_channel": 0,
            "acq_index": AcquisitionIndices(0, None, 1),
            "waveforms": weights,
        }
        strategy = acquisitions.WeightedAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        wf_dict = {}

        # act
        strategy.generate_data(wf_dict)

        # assert
        answers = [
            waveforms.square(t_test, amp=1).tolist(),
            waveforms.square(t_test, amp=0).tolist(),
        ]
        for idx, waveform in enumerate(wf_dict.values()):
            assert waveform["data"] == answers[idx]

    def test_acquire_with_immediate_bin_index(self, empty_qasm_program_qrm):
        # arrange
        qasm = empty_qasm_program_qrm
        weights = [
            {
                "wf_func": "qblox_scheduler.waveforms.square",
                "amp": 1,
                "duration": 1e-6,
            },
            {
                "wf_func": "qblox_scheduler.waveforms.square",
                "amp": 0,
                "duration": 1e-6,
            },
        ]
        data = {
            "bin_mode": None,
            "acq_channel": 2,
            "acq_index": AcquisitionIndices(12, None, 1),
            "waveforms": weights,
        }
        strategy = acquisitions.WeightedAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        strategy.generate_data({})
        strategy.qblox_acq_index, strategy.qblox_acq_bin = 3, 4

        # act
        strategy._acquire_with_immediate_bin_index(qasm)

        # assert
        assert qasm.instructions == [
            [
                "",
                "acquire_weighed",
                "3,4,0,1,4",
                "# Store acq in acq_channel:2, bin_idx:4",
            ]
        ]

    def test_duration_must_be_present(self, empty_qasm_program_qrm):
        # arrange
        qasm = empty_qasm_program_qrm
        weights = [
            {
                "wf_func": "qblox_scheduler.waveforms.square",
                "amp": 1,
            },
            {
                "wf_func": "qblox_scheduler.waveforms.square",
                "amp": 0,
            },
        ]
        data = {
            "bin_mode": None,
            "acq_channel": 2,
            "acq_index": AcquisitionIndices(12, None, 1),
            "waveforms": weights,
        }
        strategy = acquisitions.WeightedAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        strategy.bin_idx_register = qasm.register_manager.allocate_register()
        with pytest.raises(KeyError):
            strategy.generate_data({})

    def test_acquire_with_register_bin_index(self, empty_qasm_program_qrm):
        # arrange
        qasm = empty_qasm_program_qrm
        weights = [
            {
                "wf_func": "qblox_scheduler.waveforms.square",
                "amp": 1,
                "duration": 1e-6,
            },
            {
                "wf_func": "qblox_scheduler.waveforms.square",
                "amp": 0,
                "duration": 1e-6,
            },
        ]
        data = {
            "bin_mode": None,
            "acq_channel": 2,
            "acq_index": AcquisitionIndices(12, [], 1),
            "waveforms": weights,
        }
        strategy = acquisitions.WeightedAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        strategy.bin_idx_register = qasm.register_manager.allocate_register()
        strategy.generate_data({})
        strategy.qblox_acq_index = 3
        strategy.bin_mode = BinMode.APPEND

        # act
        strategy._acquire_with_register_bin_index(qasm)

        assert qasm.instructions == [
            ["", "", "", ""],
            ["", "move", "0,R1", "# Store idx of acq I wave in R1"],
            ["", "move", "1,R2", "# Store idx of acq Q wave in R2."],
            [
                "",
                "acquire_weighed",
                "3,R0,R1,R2,4",
                "# Store acq in acq_channel:2, bin_idx:R0",
            ],
            ["", "add", "R0,1,R0", "# Increment bin_idx for ch2"],
            ["", "", "", ""],
        ]

    def test_bad_weights(self, empty_qasm_program_qrm):
        # arrange
        qasm = empty_qasm_program_qrm
        weights = [
            {
                "wf_func": "qblox_scheduler.waveforms.square",
                "amp": 1.2,
                "duration": 1e-6,
            },
            {
                "wf_func": "qblox_scheduler.waveforms.square",
                "amp": 0,
                "duration": 1e-6,
            },
        ]
        data = {
            "bin_mode": None,
            "acq_channel": 2,
            "acq_index": AcquisitionIndices(12, None, 1),
            "waveforms": weights,
        }
        strategy = acquisitions.WeightedAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        strategy.bin_idx_register = qasm.register_manager.allocate_register()
        with pytest.raises(ValueError):
            strategy.generate_data({})


class TestTriggerCountStrategy:
    @pytest.mark.parametrize("bin_mode", [BinMode.AVERAGE, BinMode.APPEND])
    def test_constructor(self, bin_mode):
        data = {"bin_mode": bin_mode, "acq_channel": 0, "acq_index": AcquisitionIndices(0, None, 1)}
        acquisitions.TriggerCountAcquisitionStrategy(types.OpInfo(name="", data=data, timing=0))

    def test_generate_data(self):
        # arrange
        data = {"bin_mode": None, "acq_channel": 0, "acq_index": AcquisitionIndices(0, None, 1)}
        strategy = acquisitions.TriggerCountAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        wf_dict = {}

        # act
        strategy.generate_data(wf_dict)

        # assert
        assert len(wf_dict) == 0

    def test_acquire_with_immediate_bin_index(self, empty_qasm_program_qrm):
        # arrange
        qasm = empty_qasm_program_qrm
        data = {
            "bin_mode": BinMode.DISTRIBUTION,
            "acq_channel": 0,
            "acq_index": AcquisitionIndices(0, None, 1),
            "duration": 100e-6,
        }
        strategy = acquisitions.TriggerCountAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        strategy.generate_data({})
        strategy.qblox_acq_index, strategy.qblox_acq_bin = 5, 3

        # act
        strategy._acquire_with_immediate_bin_index(qasm)

        # assert
        assert qasm.instructions == [
            [
                "",
                "acquire_ttl",
                "5,3,1,4",
                "# Enable TTL acquisition of acq_channel:0, bin_mode:distribution",
            ],
            ["", "wait", "65535", "# auto generated wait (99992 ns)"],
            ["", "wait", "34457", "# auto generated wait (99992 ns)"],
            [
                "",
                "acquire_ttl",
                "5,3,0,4",
                "# Disable TTL acquisition of acq_channel:0, bin_mode:distribution",
            ],
        ]

    def test_acquire_with_register_bin_index(self, empty_qasm_program_qrm):
        # arrange
        qasm = empty_qasm_program_qrm
        data = {
            "bin_mode": None,
            "acq_channel": 0,
            "acq_index": AcquisitionIndices(5, [], 1),
            "duration": 100e-6,
        }
        strategy = acquisitions.TriggerCountAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        strategy.bin_idx_register = qasm.register_manager.allocate_register()
        strategy.generate_data({})
        strategy.qblox_acq_index = 12
        strategy.bin_mode = BinMode.APPEND

        # act
        strategy._acquire_with_register_bin_index(qasm)

        # assert
        assert qasm.instructions == [
            [
                "",
                "acquire_ttl",
                "12,R0,1,4",
                "# Enable TTL acquisition of acq_channel:0, store in bin:R0",
            ],
            ["", "wait", "65535", "# auto generated wait (99992 ns)"],
            ["", "wait", "34457", "# auto generated wait (99992 ns)"],
            [
                "",
                "acquire_ttl",
                "12,R0,0,4",
                "# Disable TTL acquisition of acq_channel:0, store in bin:R0",
            ],
            ["", "add", "R0,1,R0", "# Increment bin_idx for ch0"],
        ]


class TestTimetagStrategy:
    @pytest.mark.parametrize("bin_mode", [BinMode.AVERAGE, BinMode.APPEND])
    def test_constructor(self, bin_mode):
        data = {"bin_mode": bin_mode, "acq_channel": 0, "acq_index": AcquisitionIndices(0, None, 1)}
        acquisitions.TimetagAcquisitionStrategy(types.OpInfo(name="", data=data, timing=0))

    def test_generate_data(self):
        # arrange
        data = {"bin_mode": None, "acq_channel": 0, "acq_index": AcquisitionIndices(0, None, 1)}
        strategy = acquisitions.TimetagAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        wf_dict = {}

        # act
        strategy.generate_data(wf_dict)

        # assert
        assert len(wf_dict) == 0

    def test_acquire_with_immediate_bin_index(self, empty_qasm_program_qrm):
        # arrange
        qasm = empty_qasm_program_qrm
        data = {
            "bin_mode": BinMode.FIRST,
            "acq_channel": 0,
            "acq_index": AcquisitionIndices(0, None, 1),
            "duration": 100e-6,
        }
        strategy = acquisitions.TimetagAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        strategy.generate_data({})
        strategy.qblox_acq_index, strategy.qblox_acq_bin = 1, 2

        # act
        strategy._acquire_with_immediate_bin_index(qasm)

        # assert
        assert qasm.instructions == [
            [
                "",
                "acquire_timetags",
                "1,2,1,0,4",
                "# Enable timetag acquisition of acq_channel:0, bin_mode:first",
            ],
            ["", "wait", "65535", "# auto generated wait (99992 ns)"],
            ["", "wait", "34457", "# auto generated wait (99992 ns)"],
            [
                "",
                "acquire_timetags",
                "1,2,0,0,4",
                "# Disable timetag acquisition of acq_channel:0, bin_mode:first",
            ],
        ]

    def test_acquire_with_register_bin_index(self, empty_qasm_program_qrm):
        # arrange
        qasm = empty_qasm_program_qrm
        data = {
            "bin_mode": None,
            "acq_channel": 0,
            "acq_index": AcquisitionIndices(5, [], 1),
            "duration": 100e-6,
        }
        strategy = acquisitions.TimetagAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        strategy.bin_idx_register = qasm.register_manager.allocate_register()
        strategy.generate_data({})
        strategy.qblox_acq_index = 1
        strategy.bin_mode = BinMode.APPEND

        # act
        strategy._acquire_with_register_bin_index(qasm)

        # assert
        assert qasm.instructions == [
            ["", "move", "0,R1", ""],
            [
                "",
                "acquire_timetags",
                "1,R0,1,R1,4",
                "# Enable timetag acquisition of acq_channel:0, store in bin:R0",
            ],
            ["", "wait", "65535", "# auto generated wait (99992 ns)"],
            ["", "wait", "34457", "# auto generated wait (99992 ns)"],
            [
                "",
                "acquire_timetags",
                "1,R0,0,R1,4",
                "# Disable timetag acquisition of acq_channel:0, store in bin:R0",
            ],
            ["", "add", "R0,1,R0", "# Increment bin_idx for ch0"],
        ]


class TestScopedTimetagStrategy:
    @pytest.mark.parametrize("bin_mode", [BinMode.AVERAGE, BinMode.APPEND])
    def test_constructor(self, bin_mode):
        data = {"bin_mode": bin_mode, "acq_channel": 0, "acq_index": AcquisitionIndices(0, None, 1)}
        acquisitions.ScopedTimetagAcquisitionStrategy(types.OpInfo(name="", data=data, timing=0))

    def test_generate_data(self):
        # arrange
        data = {"bin_mode": None, "acq_channel": 0, "acq_index": AcquisitionIndices(0, None, 1)}
        strategy = acquisitions.ScopedTimetagAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        wf_dict = {}

        # act
        strategy.generate_data(wf_dict)

        # assert
        assert len(wf_dict) == 0

    def test_acquire_with_immediate_bin_index(self, empty_qasm_program_qrm):
        # arrange
        qasm = empty_qasm_program_qrm
        data = {
            "bin_mode": BinMode.FIRST,
            "acq_channel": 0,
            "acq_index": AcquisitionIndices(0, None, 1),
            "duration": 100e-6,
        }
        strategy = acquisitions.ScopedTimetagAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        strategy.generate_data({})
        strategy.qblox_acq_index, strategy.qblox_acq_bin = 3, 6

        # act
        strategy._acquire_with_immediate_bin_index(qasm)

        # assert
        assert qasm.instructions == [
            ["", "set_scope_en", "1", ""],
            [
                "",
                "acquire_timetags",
                "3,6,1,0,4",
                "# Enable timetag acquisition of acq_channel:0, bin_mode:first",
            ],
            ["", "wait", "65535", "# auto generated wait (99992 ns)"],
            ["", "wait", "34457", "# auto generated wait (99992 ns)"],
            [
                "",
                "acquire_timetags",
                "3,6,0,0,4",
                "# Disable timetag acquisition of acq_channel:0, bin_mode:first",
            ],
            ["", "set_scope_en", "0", ""],
        ]

    def test_acquire_with_register_bin_index(self, empty_qasm_program_qrm):
        # arrange
        qasm = empty_qasm_program_qrm
        data = {
            "bin_mode": None,
            "acq_channel": 0,
            "acq_index": AcquisitionIndices(5, [], 1),
            "duration": 100e-6,
        }
        strategy = acquisitions.ScopedTimetagAcquisitionStrategy(
            types.OpInfo(name="", data=data, timing=0)
        )
        strategy.bin_idx_register = qasm.register_manager.allocate_register()
        strategy.generate_data({})
        strategy.qblox_acq_index = 3
        strategy.bin_mode = BinMode.APPEND

        # act
        strategy._acquire_with_register_bin_index(qasm)

        # assert
        assert qasm.instructions == [
            ["", "set_scope_en", "1", ""],
            ["", "move", "0,R1", ""],
            [
                "",
                "acquire_timetags",
                "3,R0,1,R1,4",
                "# Enable timetag acquisition of acq_channel:0, store in bin:R0",
            ],
            ["", "wait", "65535", "# auto generated wait (99992 ns)"],
            ["", "wait", "34457", "# auto generated wait (99992 ns)"],
            [
                "",
                "acquire_timetags",
                "3,R0,0,R1,4",
                "# Disable timetag acquisition of acq_channel:0, store in bin:R0",
            ],
            ["", "add", "R0,1,R0", "# Increment bin_idx for ch0"],
            ["", "set_scope_en", "0", ""],
        ]


@pytest.mark.parametrize(
    "acquisition_strategy",
    [
        acquisitions.SquareAcquisitionStrategy,
        acquisitions.WeightedAcquisitionStrategy,
        acquisitions.TriggerCountAcquisitionStrategy,
        acquisitions.TimetagAcquisitionStrategy,
        acquisitions.ScopedTimetagAcquisitionStrategy,
    ],
)
def test_acquire_with_register_bin_index_invalid_bin_idx(
    acquisition_strategy, empty_qasm_program_qrm
):
    # arrange
    data = {
        "bin_mode": BinMode.APPEND,
        "acq_channel": 0,
        "acq_index": AcquisitionIndices(5, [], 1),
        "duration": 100e-6,
    }
    strategy = acquisition_strategy(types.OpInfo(name="", data=data, timing=0))

    # act
    with pytest.raises(ValueError) as exc:
        strategy.insert_qasm(empty_qasm_program_qrm)

    assert (
        exc.value.args[0] == "Attempting to add acquisition with binmode append. "
        "bin_idx_register cannot be None."
    )


@pytest.mark.deprecated
def test_trace_acquisition_measurement_control(
    mock_setup_basic_transmon_with_standard_params,
    mocker,
    make_cluster_component,
    tmp_analysis_test_data_dir,
):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {"4": {"instrument_type": "QRM_RF"}},
                "ref": "internal",
            }
        },
        "hardware_options": {
            "modulation_frequencies": {"q2:res-q2.ro": {"interm_freq": 50000000.0}}
        },
        "connectivity": {"graph": [["cluster0.module4.complex_output_0", "q2:res"]]},
    }

    mock_setup = mock_setup_basic_transmon_with_standard_params
    ic_cluster0 = make_cluster_component("cluster0")
    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg
    quantum_device.cfg_sched_repetitions = 1

    acq_duration = 5e-6  # retrieve 5000 samples
    q2 = mock_setup["q2"]
    q2.measure.acq_delay = 600e-9
    q2.clock_freqs.readout = 7404000000.0
    q2.measure.integration_time = acq_duration

    sample_param = ManualParameter("sample", label="Sample time", unit="s")
    sample_param.batched = True

    sampling_rate = constants.SAMPLING_RATE
    sample_times = np.arange(start=0, stop=acq_duration, step=1 / sampling_rate)

    sched_gettable = ScheduleGettable(
        quantum_device=quantum_device,
        schedule_function=trace_schedule_circuit_layer,
        schedule_kwargs={"qubit_name": q2.name},
        batched=True,
    )

    # Setup dummy acquisition data
    dummy_scope_acquisition_data = DummyScopeAcquisitionData(
        data=[(0, 1)] * 15000, out_of_range=(False, False), avg_cnt=(0, 0)
    )
    ic_cluster0.instrument.set_dummy_scope_acquisition_data(
        slot_idx=4, sequencer=None, data=dummy_scope_acquisition_data
    )

    meas_ctrl = MeasurementControl.find_instrument("meas_ctrl")
    meas_ctrl.settables(sample_param)
    meas_ctrl.setpoints(sample_times)
    meas_ctrl.gettables(sched_gettable)

    with mocker.patch.object(
        meas_ctrl,
        "_get_fracdone",
        side_effect=np.linspace(start=0, stop=1.0, num=4).tolist()
        + 3 * [1.0],  # Prevent StopIteration upon more calls than elem in side_effect
    ):
        try:
            set_datadir(tmp_analysis_test_data_dir)
            dataset = meas_ctrl.run(f"Readout trace schedule of {q2.name}")
        except:
            pprint.pprint(sched_gettable.compiled_schedule.compiled_instructions)
            raise
    assert dataset.sizes == {"dim_0": acq_duration * sampling_rate}

    instr_coordinator.remove_component(ic_cluster0.name)


@pytest.mark.parametrize(
    argnames=["protocol", "qubit_name", "rotation", "threshold"],
    argvalues=[
        [protocol, qubit_name, rotation, threshold]
        for protocol in ["ThresholdedAcquisition", "WeightedThresholdedAcquisition"]
        for qubit_name in ["q0", "q4"]
        for rotation in [10, 340]
        for threshold in [0.5, -0.9]
    ],
)
def test_thresholded_acquisition(
    mock_setup_basic_transmon_with_standard_params,
    qblox_hardware_config_transmon,
    protocol,
    qubit_name,
    rotation,
    threshold,
    make_cluster_component,
):
    mock_setup = mock_setup_basic_transmon_with_standard_params
    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = qblox_hardware_config_transmon
    qubit_to_device_map = {
        "q4": "cluster0_module3",
        "q0": "cluster0_module4",
    }
    q4 = mock_setup["q4"]
    q4.clock_freqs.readout = 7.7e9

    qubit = mock_setup[qubit_name]
    qubit.measure.acq_rotation = rotation
    qubit.measure.acq_threshold = threshold

    schedule = TimeableSchedule("Thresholded acquisition")
    schedule.add(Measure(qubit_name, acq_protocol=protocol))

    compiler = SerialCompiler("compiler", quantum_device=quantum_device)
    compiled_schedule = compiler.compile(schedule)

    compiled_instructions = compiled_schedule.compiled_instructions["cluster0"][
        qubit_to_device_map[qubit_name]
    ]
    sequencer_compiled_instructions = compiled_instructions["sequencers"]["seq0"]
    acq_channels_data = compiled_schedule.compiled_instructions["cluster0"]["acq_channels_data"]

    if protocol == "WeightedThresholdedAcquisition":
        integration_time = round(
            len(qubit.measure.acq_weights_a) * 1e9 / qubit.measure.acq_weights_sampling_rate
        )
    else:
        integration_time = qubit.measure.integration_time * 1e9
        assert sequencer_compiled_instructions.thresholded_acq_rotation == rotation
    assert sequencer_compiled_instructions.thresholded_acq_threshold == threshold * integration_time
    if protocol == "WeightedThresholdedAcquisition":
        assert sequencer_compiled_instructions.thresholded_acq_rotation == 360 - 45
    else:
        assert sequencer_compiled_instructions.thresholded_acq_rotation == rotation
        assert acq_channels_data[qubit.measure.acq_channel].protocol == protocol

    instr_coordinator = mock_setup["instrument_coordinator"]

    ic_cluster0 = make_cluster_component("cluster0")
    ic_generic = GenericInstrumentCoordinatorComponent("generic")
    lo1 = MockLocalOscillator("lo1")
    ic_lo1 = GenericInstrumentCoordinatorComponent(lo1)
    instr_coordinator.add_component(ic_cluster0)
    instr_coordinator.add_component(ic_generic)
    instr_coordinator.add_component(ic_lo1)

    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=4, sequencer=0, acq_index_name="0", data=[None]
    )

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_schedule)
    instr_coordinator.start()
    data = instr_coordinator.retrieve_acquisition()
    instr_coordinator.stop()

    expected_acq_channel = mock_setup[qubit_name].measure.acq_channel

    expected_dataarray = DataArray(
        [-1],
        coords=[[0]],
        dims=[f"acq_index_{expected_acq_channel}"],
        attrs={"acq_protocol": protocol, "acq_index_dim_name": f"acq_index_{expected_acq_channel}"},
    )
    expected_dataset = Dataset({expected_acq_channel: expected_dataarray})

    xr.testing.assert_identical(data, expected_dataset)


@pytest.mark.parametrize(
    "rotation, threshold",
    [
        (0, 1e9),
        (400, 0),
    ],
)
def test_weighted_thresholded_acquisition_wrong_values(
    mock_setup_basic_transmon_with_standard_params,
    qblox_hardware_config_transmon,
    rotation,
    threshold,
):
    mock_setup = mock_setup_basic_transmon_with_standard_params
    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = qblox_hardware_config_transmon

    qubit = mock_setup["q0"]
    qubit.measure.acq_rotation = rotation
    qubit.measure.acq_threshold = threshold

    schedule = TimeableSchedule("Thresholded acquisition")
    schedule.add(Measure("q0", acq_protocol="ThresholdedAcquisition"))

    compiler = SerialCompiler("compiler", quantum_device=quantum_device)

    with pytest.raises(ValueError) as error:
        _ = compiler.compile(schedule)

    assert "Attempting to configure" in error.value.args[0]


@pytest.mark.parametrize("protocol", ["ThresholdedAcquisition", "WeightedThresholdedAcquisition"])
def test_weighted_thresholded_acquisition_multiplex(
    mock_setup_basic_transmon_with_standard_params, protocol
):
    hardware_config = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {"3": {"instrument_type": "QRM"}},
                "ref": "internal",
            },
            "iq_mixer_lo": {"instrument_type": "IQMixer"},
            "lo": {"instrument_type": "LocalOscillator", "power": 1},
        },
        "hardware_options": {
            "modulation_frequencies": {
                "q0:res-q0.ro": {"lo_freq": 7200000000.0},
                "q1:res-q1.ro": {"lo_freq": 7200000000.0},
            }
        },
        "connectivity": {
            "graph": [
                ["cluster0.module3.complex_output_0", "iq_mixer_lo.if"],
                ["lo.output", "iq_mixer_lo.lo"],
                ["iq_mixer_lo.rf", "q0:res"],
                ["iq_mixer_lo.rf", "q1:res"],
            ]
        },
    }

    mock_setup = mock_setup_basic_transmon_with_standard_params
    q0 = mock_setup["q0"]
    q1 = mock_setup["q1"]

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_config

    rotation_q0, rotation_q1 = 350, 222
    threshold_q0, threshold_q1 = 0.2, -0.5

    q0.measure.acq_rotation = rotation_q0
    q0.measure.acq_threshold = threshold_q0
    q1.measure.acq_rotation = rotation_q1
    q1.measure.acq_threshold = threshold_q1

    schedule = TimeableSchedule("Thresholded acquisition")
    schedule.add(Measure("q0", "q1", acq_protocol=protocol))

    compiler = SerialCompiler("compiler", quantum_device=quantum_device)
    compiled_schedule = compiler.compile(schedule)

    for index, threshold in enumerate((threshold_q0, threshold_q1)):
        sequencer_compiled_instructions = compiled_schedule.compiled_instructions["cluster0"][
            "cluster0_module3"
        ]["sequencers"][f"seq{index}"]
        acq_channels_data = compiled_schedule.compiled_instructions["cluster0"]["acq_channels_data"]

        qubit = q0 if index == 0 else q1

        if protocol == "WeightedThresholdedAcquisition":
            integration_length = round(
                len(qubit.measure.acq_weights_a) * 1e9 / qubit.measure.acq_weights_sampling_rate
            )
        else:
            integration_length = qubit.measure.integration_time * 1e9

        assert (
            sequencer_compiled_instructions.thresholded_acq_threshold
            == threshold * integration_length
        )

        acq_channel = index
        assert acq_channels_data[acq_channel].protocol == protocol


def test_trigger_count_append(
    mock_setup_basic_nv, make_cluster_component, hardware_cfg_trigger_count
):
    # Setup objects needed for experiment
    ic_cluster0 = make_cluster_component("cluster0")
    red_laser = MockLocalOscillator("red_laser")
    red_laser_2 = MockLocalOscillator("red_laser_2")
    ic_red_laser = GenericInstrumentCoordinatorComponent(red_laser)
    ic_red_laser_2 = GenericInstrumentCoordinatorComponent(red_laser_2)
    ic_generic = GenericInstrumentCoordinatorComponent("generic")

    instr_coordinator = mock_setup_basic_nv["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)
    instr_coordinator.add_component(ic_red_laser)
    instr_coordinator.add_component(ic_red_laser_2)
    instr_coordinator.add_component(ic_generic)

    quantum_device = mock_setup_basic_nv["quantum_device"]
    quantum_device.hardware_config = hardware_cfg_trigger_count

    # Define experiment schedule
    schedule = TimeableSchedule("test multiple measurements")
    schedule.add(
        Measure(
            "qe0",
            coords={"amp": 0.1, "freq": 1.0},
            acq_protocol="TriggerCount",
            bin_mode=BinMode.APPEND,
        )
    )
    schedule.add(
        Measure(
            "qe0",
            coords={"amp": 0.2, "freq": 2.0},
            acq_protocol="TriggerCount",
            bin_mode=BinMode.APPEND,
        )
    )
    schedule.add(
        Measure(
            "qe0",
            coords={"amp": 0.3, "freq": 3.0},
            acq_protocol="TriggerCount",
            bin_mode=BinMode.APPEND,
        )
    )

    # Setup dummy acquisition data
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=1,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(10000, 15000), thres=0, avg_cnt=100),
            DummyBinnedAcquisitionData(data=(20000, 25000), thres=0, avg_cnt=200),
            DummyBinnedAcquisitionData(data=(20000, 25000), thres=0, avg_cnt=300),
        ],
    )

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_sched)
    instr_coordinator.start()
    data = instr_coordinator.retrieve_acquisition()
    instr_coordinator.stop()

    # Assert intended behaviour
    assert isinstance(data, Dataset)
    expected_dataarray = DataArray(
        [[100, 200, 300]],
        coords={
            "repetition": [0],
            "acq_index_0": [0, 1, 2],
            "amp": ("acq_index_0", [0.1, 0.2, 0.3]),
            "freq": ("acq_index_0", [1.0, 2.0, 3.0]),
        },
        dims=["repetition", "acq_index_0"],
        attrs={"acq_protocol": "TriggerCount", "acq_index_dim_name": "acq_index_0"},
    )
    expected_dataset = Dataset({0: expected_dataarray})

    xr.testing.assert_identical(data, expected_dataset)

    instr_coordinator.remove_component("ic_cluster0")


def test_trigger_count_append_qtm(
    mocker,
    mock_setup_basic_nv,
    make_cluster_component,
):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {
                    3: {"instrument_type": "QRM"},
                    5: {"instrument_type": "QTM"},
                },
                "ref": "internal",
            },
            "iq_mixer_red_laser": {"instrument_type": "IQMixer"},
            "optical_mod_red_laser_2": {"instrument_type": "OpticalModulator"},
            "red_laser": {"instrument_type": "LocalOscillator", "power": 1},
            "red_laser_2": {"instrument_type": "LocalOscillator", "power": 1},
        },
        "hardware_options": {
            "modulation_frequencies": {
                "qe0:optical_readout-qe0.ge0": {
                    "lo_freq": None,
                    "interm_freq": 50000000.0,
                },
                "qe0:optical_control-qe0.ge0": {"lo_freq": None, "interm_freq": 0},
            },
            "digitization_thresholds": {"qe0:optical_readout-qe0.ge0": {"analog_threshold": 0.5}},
            "sequencer_options": {"qe0:optical_readout-qe0.ge0": {"ttl_acq_threshold": 0.5}},
        },
        "connectivity": {
            "graph": [
                ("cluster0.module5.digital_input_0", "iq_mixer_red_laser.if"),
                ("red_laser.output", "iq_mixer_red_laser.lo"),
                ("iq_mixer_red_laser.rf", "qe0:optical_readout"),
                ("cluster0.module3.real_output_0", "optical_mod_red_laser_2.if"),
                ("red_laser_2.output", "optical_mod_red_laser_2.lo"),
                ("optical_mod_red_laser_2.out", "qe0:optical_control"),
            ]
        },
    }

    # Setup objects needed for experiment
    ic_cluster0 = make_cluster_component("cluster0")
    red_laser = MockLocalOscillator("red_laser")
    red_laser_2 = MockLocalOscillator("red_laser_2")
    ic_red_laser = GenericInstrumentCoordinatorComponent(red_laser)
    ic_red_laser_2 = GenericInstrumentCoordinatorComponent(red_laser_2)
    ic_generic = GenericInstrumentCoordinatorComponent("generic")

    instr_coordinator = mock_setup_basic_nv["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)
    instr_coordinator.add_component(ic_red_laser)
    instr_coordinator.add_component(ic_red_laser_2)
    instr_coordinator.add_component(ic_generic)

    quantum_device = mock_setup_basic_nv["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    # Define experiment schedule
    schedule = TimeableSchedule("test multiple measurements")
    schedule.add(
        Measure(
            "qe0",
            coords={"amp": 0.1, "freq": 1.0},
            acq_protocol="TriggerCount",
            bin_mode=BinMode.APPEND,
        )
    )
    schedule.add(
        Measure(
            "qe0",
            coords={"amp": 0.2, "freq": 2.0},
            acq_protocol="TriggerCount",
            bin_mode=BinMode.APPEND,
        )
    )
    schedule.add(
        Measure(
            "qe0",
            coords={"amp": 0.3, "freq": 3.0},
            acq_protocol="TriggerCount",
            bin_mode=BinMode.APPEND,
        )
    )

    # TODO remove these patches when the QTM dummy is available (SE-499)
    mocker.patch.object(ic_cluster0.instrument.module5.sequencer0.sync_en, "set")
    mocker.patch.object(ic_cluster0.instrument.module5.sequencer0.sequence, "set")
    mocker.patch.object(ic_cluster0.instrument.module5.io_channel0.mode, "set")
    mocker.patch.object(ic_cluster0.instrument.module5.io_channel0.mode, "get")
    mocker.patch.object(ic_cluster0.instrument.module5.io_channel0.forward_trigger_en, "set")
    mocker.patch.object(ic_cluster0.instrument.module5.io_channel0.binned_acq_time_ref, "set")
    mocker.patch.object(ic_cluster0.instrument.module5.io_channel0.binned_acq_time_source, "set")
    mocker.patch.object(
        ic_cluster0.instrument.module5.io_channel0.binned_acq_on_invalid_time_delta,
        "set",
    )
    mocker.patch.object(
        ic_cluster0.instrument.module5,
        "get_acquisitions",
        return_value={
            "0": {
                "index": 0,
                "acquisition": {
                    "scope": [],
                    "bins": {
                        "count": [100, 200, 300],
                        "timedelta": [1, 2, 3],
                        "threshold": [1, 2, 3],
                        "valid": [True, True, True],
                        "avg_cnt": [100, 200, 300],
                    },
                },
            }
        },
    )

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_sched)
    instr_coordinator.start()
    data = instr_coordinator.retrieve_acquisition()
    instr_coordinator.stop()

    # Assert intended behaviour
    assert isinstance(data, Dataset)
    expected_dataarray = DataArray(
        [[100, 200, 300]],
        coords={
            "repetition": [0],
            "acq_index_0": [0, 1, 2],
            "amp": ("acq_index_0", [0.1, 0.2, 0.3]),
            "freq": ("acq_index_0", [1.0, 2.0, 3.0]),
        },
        dims=["repetition", "acq_index_0"],
        attrs={"acq_protocol": "TriggerCount", "acq_index_dim_name": "acq_index_0"},
    )
    expected_dataset = Dataset({0: expected_dataarray})

    xr.testing.assert_identical(data, expected_dataset)

    instr_coordinator.remove_component("ic_cluster0")


def test_trigger_count_append_gettables(
    mock_setup_basic_nv, make_cluster_component, hardware_cfg_trigger_count
):
    # Setup objects needed for experiment
    ic_cluster0 = make_cluster_component("cluster0")
    red_laser = MockLocalOscillator("red_laser")
    red_laser_2 = MockLocalOscillator("red_laser_2")
    ic_red_laser = GenericInstrumentCoordinatorComponent(red_laser)
    ic_red_laser_2 = GenericInstrumentCoordinatorComponent(red_laser_2)
    ic_generic = GenericInstrumentCoordinatorComponent("generic")

    instr_coordinator = mock_setup_basic_nv["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)
    instr_coordinator.add_component(ic_red_laser)
    instr_coordinator.add_component(ic_red_laser_2)
    instr_coordinator.add_component(ic_generic)

    quantum_device = mock_setup_basic_nv["quantum_device"]
    quantum_device.hardware_config = hardware_cfg_trigger_count

    # Define experiment schedule
    def _schedule_function(repetitions):
        schedule = TimeableSchedule("test multiple measurements", repetitions=repetitions)
        schedule.add(
            Measure(
                "qe0", coords={"index": 0}, acq_protocol="TriggerCount", bin_mode=BinMode.APPEND
            )
        )
        schedule.add(
            Measure(
                "qe0", coords={"index": 1}, acq_protocol="TriggerCount", bin_mode=BinMode.APPEND
            )
        )
        schedule.add(
            Measure(
                "qe0", coords={"index": 2}, acq_protocol="TriggerCount", bin_mode=BinMode.APPEND
            )
        )
        return schedule

    # Setup dummy acquisition data
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=1,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(10000, 15000), thres=0, avg_cnt=100),
            DummyBinnedAcquisitionData(data=(10000, 15000), thres=0, avg_cnt=150),
            DummyBinnedAcquisitionData(data=(20000, 25000), thres=0, avg_cnt=200),
            DummyBinnedAcquisitionData(data=(20000, 25000), thres=0, avg_cnt=250),
            DummyBinnedAcquisitionData(data=(20000, 25000), thres=0, avg_cnt=300),
            DummyBinnedAcquisitionData(data=(20000, 25000), thres=0, avg_cnt=350),
        ],
    )

    quantum_device.cfg_sched_repetitions = 2
    sched_gettable = ScheduleGettable(
        quantum_device=quantum_device,
        schedule_function=_schedule_function,
        schedule_kwargs={},
        batched=True,
    )
    data = sched_gettable.get()

    # Assert intended behaviour
    np.testing.assert_array_equal(data, [[100, 200, 300, 150, 250, 350]])

    instr_coordinator.remove_component("ic_cluster0")


def test_trigger_count_distribution(
    mock_setup_basic_nv, make_cluster_component, hardware_cfg_trigger_count
):
    # Setup objects needed for experiment
    ic_cluster0 = make_cluster_component("cluster0")
    red_laser = MockLocalOscillator("red_laser")
    red_laser_2 = MockLocalOscillator("red_laser_2")
    ic_red_laser = GenericInstrumentCoordinatorComponent(red_laser)
    ic_red_laser_2 = GenericInstrumentCoordinatorComponent(red_laser_2)
    ic_generic = GenericInstrumentCoordinatorComponent("generic")

    instr_coordinator = mock_setup_basic_nv["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)
    instr_coordinator.add_component(ic_red_laser)
    instr_coordinator.add_component(ic_red_laser_2)
    instr_coordinator.add_component(ic_generic)

    quantum_device = mock_setup_basic_nv["quantum_device"]
    quantum_device.hardware_config = hardware_cfg_trigger_count

    # Define experiment schedule
    schedule = TimeableSchedule("test multiple measurements")
    meas0 = Measure("qe0", acq_protocol="TriggerCount", bin_mode=BinMode.DISTRIBUTION)
    schedule.add(meas0)

    # Setup dummy acquisition data
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=1,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(10000, 15000), thres=0, avg_cnt=100),
            DummyBinnedAcquisitionData(data=(20000, 25000), thres=0, avg_cnt=100),
            DummyBinnedAcquisitionData(data=(30000, 35000), thres=0, avg_cnt=75),
            DummyBinnedAcquisitionData(data=(40000, 45000), thres=0, avg_cnt=50),
            DummyBinnedAcquisitionData(data=(50000, 55000), thres=0, avg_cnt=25),
            DummyBinnedAcquisitionData(data=(60000, 65000), thres=0, avg_cnt=25),
            DummyBinnedAcquisitionData(data=(70000, 75000), thres=0, avg_cnt=5),
        ],
    )

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_sched)
    instr_coordinator.start()
    data = instr_coordinator.retrieve_acquisition()
    instr_coordinator.stop()

    # Assert intended behaviour
    assert isinstance(data, Dataset)
    expected_dataarray = DataArray(
        [25, 25, 25, 20, 5],
        coords={"acq_index_0": [0, 1, 2, 3, 4], "counts_0": ("acq_index_0", [2, 3, 4, 6, 7])},
        dims=["acq_index_0"],
        attrs={"acq_protocol": "TriggerCount", "acq_index_dim_name": "acq_index_0"},
    )
    expected_dataset = Dataset({0: expected_dataarray})

    xr.testing.assert_identical(data, expected_dataset)

    instr_coordinator.remove_component("ic_cluster0")


def test_trigger_count_distribution_gettables(
    mock_setup_basic_nv, make_cluster_component, hardware_cfg_trigger_count
):
    # Setup objects needed for experiment
    ic_cluster0 = make_cluster_component("cluster0")
    red_laser = MockLocalOscillator("red_laser")
    red_laser_2 = MockLocalOscillator("red_laser_2")
    ic_red_laser = GenericInstrumentCoordinatorComponent(red_laser)
    ic_red_laser_2 = GenericInstrumentCoordinatorComponent(red_laser_2)
    ic_generic = GenericInstrumentCoordinatorComponent("generic")

    instr_coordinator = mock_setup_basic_nv["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)
    instr_coordinator.add_component(ic_red_laser)
    instr_coordinator.add_component(ic_red_laser_2)
    instr_coordinator.add_component(ic_generic)

    quantum_device = mock_setup_basic_nv["quantum_device"]
    quantum_device.hardware_config = hardware_cfg_trigger_count

    # Define experiment schedule
    def _schedule_function(repetitions):
        schedule = TimeableSchedule("test multiple measurements", repetitions=repetitions)
        meas0 = Measure("qe0", acq_protocol="TriggerCount", bin_mode=BinMode.DISTRIBUTION)
        schedule.add(meas0)
        return schedule

    # Setup dummy acquisition data
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=1,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(10000, 15000), thres=0, avg_cnt=100),
            DummyBinnedAcquisitionData(data=(20000, 25000), thres=0, avg_cnt=100),
            DummyBinnedAcquisitionData(data=(30000, 35000), thres=0, avg_cnt=75),
            DummyBinnedAcquisitionData(data=(40000, 45000), thres=0, avg_cnt=50),
            DummyBinnedAcquisitionData(data=(50000, 55000), thres=0, avg_cnt=25),
            DummyBinnedAcquisitionData(data=(60000, 65000), thres=0, avg_cnt=25),
            DummyBinnedAcquisitionData(data=(70000, 75000), thres=0, avg_cnt=5),
        ],
    )

    # Generate compiled schedule
    sched_gettable = ScheduleGettable(
        quantum_device=quantum_device,
        schedule_function=_schedule_function,
        schedule_kwargs={},
        batched=True,
    )
    data = sched_gettable.get()

    np.testing.assert_array_equal(data, [[25, 25, 25, 20, 5]])

    instr_coordinator.remove_component("ic_cluster0")


def test_mixed_binned_trace_measurements(mock_setup_basic_transmon, make_cluster_component):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {"3": {"instrument_type": "QRM"}},
                "ref": "internal",
            }
        },
        "hardware_options": {
            "modulation_frequencies": {"q0:res-q0.ro": {"interm_freq": 50000000.0}}
        },
        "connectivity": {
            "graph": [
                ["cluster0.module3.complex_output_0", "q0:res"],
                ["cluster0.module3.real_output_0", "q1:res"],
            ]
        },
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon
    ic_cluster0 = make_cluster_component("cluster0")

    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    q0 = mock_setup["q0"]
    q1 = mock_setup["q1"]
    q0.clock_freqs.readout = 50e6
    q1.clock_freqs.readout = 50e6

    # Define experiment schedule
    schedule = TimeableSchedule("test multiple measurements")
    meas0 = Measure(
        "q0", coords={"amp_0": 0.1, "freq_0": 1.0}, acq_protocol="SSBIntegrationComplex"
    )
    meas1 = Measure("q1", coords={"amp_1": 0.2, "freq_1": 2.0}, acq_protocol="Trace")
    schedule.add(meas0)
    schedule.add(meas1)

    # Change acq delay, duration and channel
    q0.measure.acq_delay = 1e-6
    q1.measure.acq_delay = 1e-6
    q1.measure.acq_channel = 1
    q0.measure.integration_time = 5e-6
    q1.measure.integration_time = 3e-6

    # Setup dummy acquisition data
    dummy_scope_acquisition_data = DummyScopeAcquisitionData(
        data=[(0, 1)] * 15000, out_of_range=(False, False), avg_cnt=(0, 0)
    )
    ic_cluster0.instrument.set_dummy_scope_acquisition_data(
        slot_idx=3, sequencer=None, data=dummy_scope_acquisition_data
    )
    dummy_binned_acquisition_data = [
        DummyBinnedAcquisitionData(data=(100.0, 200.0), thres=0, avg_cnt=0),
    ]
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3, sequencer=0, acq_index_name="0", data=dummy_binned_acquisition_data
    )

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_sched)
    instr_coordinator.start()
    data = instr_coordinator.retrieve_acquisition()
    instr_coordinator.stop()

    # Assert intended behaviour
    assert isinstance(data, Dataset)
    expected_dataarray_trace = DataArray(
        [[1j] * 3000],
        coords={
            "acq_index_1": [0],
            "trace_index_1": range(3000),
            "amp_1": ("acq_index_1", [0.2]),
            "freq_1": ("acq_index_1", [2.0]),
        },
        dims=["acq_index_1", "trace_index_1"],
        attrs={"acq_protocol": "Trace", "acq_index_dim_name": "acq_index_1"},
    )
    expected_dataarray_binned = DataArray(
        [0.02 + 0.04j],
        coords={
            "acq_index_0": [0],
            "amp_0": ("acq_index_0", [0.1]),
            "freq_0": ("acq_index_0", [1.0]),
        },
        dims=["acq_index_0"],
        attrs={"acq_protocol": "SSBIntegrationComplex", "acq_index_dim_name": "acq_index_0"},
    )
    expected_dataset = Dataset({0: expected_dataarray_binned, 1: expected_dataarray_trace})

    xr.testing.assert_identical(data, expected_dataset)

    instr_coordinator.remove_component("ic_cluster0")


def test_mixed_ssb_thresholded_compiles(mock_setup_basic_transmon, make_cluster_component):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {"3": {"instrument_type": "QRM"}},
                "ref": "internal",
            }
        },
        "hardware_options": {
            "modulation_frequencies": {"q0:res-q0.ro": {"interm_freq": 50000000.0}}
        },
        "connectivity": {
            "graph": [
                ["cluster0.module3.complex_output_0", "q0:res"],
            ]
        },
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon
    ic_cluster0 = make_cluster_component("cluster0")

    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    q0 = mock_setup["q0"]
    q0.clock_freqs.readout = 50e6
    q0.measure.acq_delay = 1e-6
    q0.measure.integration_time = 5e-6
    q0.measure.acq_threshold = -0.0005479034086863598
    q0.measure.acq_rotation = 80.27560982032605

    # Define experiment schedule
    schedule = TimeableSchedule("test multiple measurements")
    meas0 = Measure("q0", acq_channel=0, acq_protocol="SSBIntegrationComplex")
    meas1 = Measure("q0", acq_channel=1, acq_protocol="ThresholdedAcquisition")
    schedule.add(meas0)
    schedule.add(meas1)

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiler.compile(schedule=schedule, config=quantum_device.generate_compilation_config())


def test_multiple_trace_raises(
    mock_setup_basic_transmon_with_standard_params, make_cluster_component
):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {"3": {"instrument_type": "QRM_RF"}},
                "ref": "internal",
            }
        },
        "hardware_options": {
            "modulation_frequencies": {"q0:res-q0.ro": {"interm_freq": 50000000.0}}
        },
        "connectivity": {"graph": [["cluster0.module3.complex_output_0", "q0:res"]]},
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon_with_standard_params
    ic_cluster0 = make_cluster_component("cluster0")
    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    q0 = mock_setup["q0"]

    # Define experiment schedule
    schedule = TimeableSchedule("test multiple measurements")
    meas0 = Measure("q0", acq_protocol="Trace")
    schedule.add(meas0)

    # Change acq delay, duration and channel
    q0.measure.acq_delay = 1e-6
    q0.measure.integration_time = 5e-6

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Imitate a compiled schedule which contains multiple trace acquisition for one module.
    compiled_sched.compiled_instructions["cluster0"]["acq_channels_data"] = {
        0: AcquisitionChannelData("acq_index_0", "Trace", BinMode.AVERAGE, {}),
        1: AcquisitionChannelData("acq_index_0", "Trace", BinMode.AVERAGE, {}),
    }
    compiled_sched.compiled_instructions["cluster0"]["cluster0_module3"]["acq_hardware_mapping"] = {
        "seq0": QbloxAcquisitionHardwareMapping(non_fully_append={0: 0}, fully_append=[]),
        "seq1": QbloxAcquisitionHardwareMapping(non_fully_append={1: 0}, fully_append=[]),
    }

    with pytest.raises(ValueError) as exc:
        instr_coordinator.prepare(compiled_sched)

    # assert
    assert exc.value.args[0] == (
        "Both sequencer '1' and '0' "
        "of 'ic_cluster0_module3' attempts to perform scope mode acquisitions. "
        "Only one sequencer per device can "
        "trigger raw trace capture.\n\nPlease ensure that "
        "only one port-clock combination performs "
        "raw trace acquisition per instrument."
    )

    instr_coordinator.remove_component("ic_cluster0")


@pytest.mark.parametrize(
    "qubit_to_overwrite",
    ["q1", "q2"],
)
def test_same_index_in_module_and_cluster_measurement_error(
    mocker,
    mock_setup_basic_transmon_with_standard_params,
    make_cluster_component,
    qubit_to_overwrite,
):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {
                    "3": {"instrument_type": "QRM"},
                    "4": {"instrument_type": "QRM_RF"},
                },
                "ref": "internal",
            }
        },
        "hardware_options": {
            "modulation_frequencies": {
                "q0:res-q0.ro": {"interm_freq": 50000000.0},
                "q1:res-q1.ro": {"interm_freq": 50000000.0},
                "q2:res-q2.ro": {"interm_freq": 50000000.0},
            }
        },
        "connectivity": {
            "graph": [
                ["cluster0.module3.complex_output_0", "q0:res"],
                ["cluster0.module3.complex_output_0", "q1:res"],
                ["cluster0.module4.complex_output_0", "q2:res"],
            ]
        },
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon_with_standard_params
    ic_cluster0 = make_cluster_component("cluster0")
    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    for comp in ic_cluster0._cluster_modules.values():
        instrument = comp.instrument
        if instrument.is_qrm_type:
            mock_acquisition_data = {
                "0": {
                    "index": 0,
                    "acquisition": {"bins": {"integration": {"path0": [0], "path1": [0]}}},
                }
            }
            mocker.patch.object(instrument, "get_acquisitions", return_value=mock_acquisition_data)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    # Define experiment schedule
    schedule = TimeableSchedule("test multiple measurements")
    schedule.add(
        Measure("q0", acq_protocol="SSBIntegrationComplex", acq_index=0, bin_mode=BinMode.AVERAGE)
    )
    schedule.add(
        Measure(
            qubit_to_overwrite,
            acq_protocol="SSBIntegrationComplex",
            acq_index=0,
            bin_mode=BinMode.AVERAGE,
        )
    )
    schedule.add_resource(ClockResource(name="q0.ro", freq=50e6))
    schedule.add_resource(ClockResource(name="q1.ro", freq=50e6))

    # Change acq delay, duration and channel
    q0 = mock_setup["q0"]
    q0.measure.acq_delay = 1e-6
    q0.measure.integration_time = 5e-6
    q0.measure.acq_channel = 0
    q1 = mock_setup["q1"]
    q1.measure.acq_delay = 1e-6
    q1.measure.integration_time = 5e-6
    q1.measure.acq_channel = 0
    q2 = mock_setup["q2"]
    q2.measure.acq_delay = 600e-9
    q2.clock_freqs.readout = 7404000000.0
    q2.measure.integration_time = 5e-6
    q2.measure.acq_channel = 0

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")

    with pytest.raises(
        ValueError,
        match=r"Found invalid acq_index=0 for acq_channel=0. "
        "Make sure that each explicitly defined acq_index starts at 0, and increments by 1 "
        "for each new acquisition within the same acquisition channel, ordered by time.",
    ):
        compiler.compile(schedule=schedule, config=quantum_device.generate_compilation_config())


def test_complex_input_hardware_cfg(make_cluster_component, mock_setup_basic_transmon):
    # for a transmon measurement now both input and output can be used to run it.
    # if we like to take these apart, dispersive_measurement should be adjusted.
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {"3": {"instrument_type": "QRM"}},
                "ref": "internal",
            }
        },
        "hardware_options": {
            "modulation_frequencies": {
                "q0:res-q0.ro": {"interm_freq": 50000000.0},
                "q1:res-q1.ro": {"interm_freq": 50000000.0},
            }
        },
        "connectivity": {
            "graph": [
                ["cluster0.module3.complex_input_0", "q0:res"],
                ["cluster0.module3.complex_output_0", "q1:res"],
            ]
        },
    }

    # Setup objects needed for experiment
    ic_cluster0 = make_cluster_component("cluster0")
    instr_coordinator = mock_setup_basic_transmon["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup_basic_transmon["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    q0 = quantum_device.get_element("q0")
    q1 = quantum_device.get_element("q1")

    # Define experiment schedule
    schedule = TimeableSchedule("test complex input")
    schedule.add_resource(ClockResource(name="q1.ro", freq=50e6))
    schedule.add_resource(ClockResource(name="q0.ro", freq=50e6))
    schedule.add(Measure("q0", acq_protocol="SSBIntegrationComplex"))
    schedule.add(Measure("q1", acq_protocol="SSBIntegrationComplex"))

    # Change acq delay
    q0.measure.acq_delay = 4e-9
    q1.measure.acq_delay = 4e-9
    q1.measure.acq_channel = 1

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Setup dummy acquisition data
    dummy_binned_acquisition_data = [
        DummyBinnedAcquisitionData(data=(100.0, 200.0), thres=0, avg_cnt=0),
    ]
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3, sequencer=0, acq_index_name="0", data=dummy_binned_acquisition_data
    )
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3, sequencer=1, acq_index_name="0", data=dummy_binned_acquisition_data
    )

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_sched)
    instr_coordinator.start()
    data = instr_coordinator.retrieve_acquisition()
    instr_coordinator.stop()

    # Assert intended behaviour
    assert isinstance(data, Dataset)
    expected_dataarray_0 = DataArray(
        [0.1 + 0.2j],
        coords=[[0]],
        dims=["acq_index_0"],
        attrs={"acq_protocol": "SSBIntegrationComplex", "acq_index_dim_name": "acq_index_0"},
    )
    expected_dataarray_1 = DataArray(
        [0.1 + 0.2j],
        coords=[[0]],
        dims=["acq_index_1"],
        attrs={"acq_protocol": "SSBIntegrationComplex", "acq_index_dim_name": "acq_index_1"},
    )
    expected_dataset = Dataset({0: expected_dataarray_0, 1: expected_dataarray_1})
    xr.testing.assert_identical(data, expected_dataset)
    assert compiled_sched.compiled_instructions["cluster0"]["cluster0_module3"]["sequencers"][
        "seq0"
    ].connected_input_indices == (0, 1)

    instr_coordinator.remove_component("ic_cluster0")


def test_multi_real_input_hardware_cfg_trigger_count(make_cluster_component, mock_setup_basic_nv):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {3: {"instrument_type": "QRM"}},
                "ref": "internal",
            },
            "optical_mod_red_laser_1": {"instrument_type": "OpticalModulator"},
            "optical_mod_red_laser_2": {"instrument_type": "OpticalModulator"},
            "red_laser_1": {"instrument_type": "LocalOscillator", "power": 1},
            "red_laser_2": {"instrument_type": "LocalOscillator", "power": 1},
        },
        "hardware_options": {
            "modulation_frequencies": {
                "qe0:optical_control-qe0.ge0": {
                    "lo_freq": None,
                    "interm_freq": 200000000.0,
                },
                "qe1:optical_control-qe1.ge0": {
                    "lo_freq": None,
                    "interm_freq": 200000000.0,
                },
                "qe0:optical_readout-qe0.ge0": {"interm_freq": 0},
                "qe1:optical_readout-qe1.ge0": {"interm_freq": 0},
            },
            "sequencer_options": {
                "qe0:optical_readout-qe0.ge0": {"ttl_acq_threshold": 0.5},
                "qe1:optical_readout-qe1.ge0": {"ttl_acq_threshold": 0.5},
            },
        },
        "connectivity": {
            "graph": [
                ("cluster0.module3.real_output_0", "optical_mod_red_laser_1.if"),
                ("red_laser_1.output", "optical_mod_red_laser_1.lo"),
                ("optical_mod_red_laser_1.out", "qe0:optical_control"),
                ("cluster0.module3.real_output_1", "optical_mod_red_laser_2.if"),
                ("red_laser_2.output", "optical_mod_red_laser_2.lo"),
                ("optical_mod_red_laser_2.out", "qe1:optical_control"),
                ("cluster0.module3.real_input_0", "qe0:optical_readout"),
                ("cluster0.module3.real_input_1", "qe1:optical_readout"),
            ]
        },
    }

    # Setup objects needed for experiment
    ic_cluster0 = make_cluster_component("cluster0")
    red_laser = MockLocalOscillator("red_laser")
    ic_red_laser = GenericInstrumentCoordinatorComponent(red_laser)
    ic_generic = GenericInstrumentCoordinatorComponent("generic")

    instr_coordinator = mock_setup_basic_nv["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)
    instr_coordinator.add_component(ic_red_laser)
    instr_coordinator.add_component(ic_generic)

    quantum_device = mock_setup_basic_nv["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    # Define experiment schedule
    schedule = TimeableSchedule("test NV measurement with real output and input")
    schedule.add(Measure("qe0", acq_protocol="TriggerCount", bin_mode=BinMode.APPEND))
    schedule.add(Measure("qe1", acq_protocol="TriggerCount", bin_mode=BinMode.DISTRIBUTION))

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Assert intended behaviour
    seq_0 = compiled_sched.compiled_instructions["cluster0"]["cluster0_module3"]["sequencers"][
        "seq0"
    ]
    seq_1 = compiled_sched.compiled_instructions["cluster0"]["cluster0_module3"]["sequencers"][
        "seq1"
    ]
    seq_2 = compiled_sched.compiled_instructions["cluster0"]["cluster0_module3"]["sequencers"][
        "seq2"
    ]
    seq_3 = compiled_sched.compiled_instructions["cluster0"]["cluster0_module3"]["sequencers"][
        "seq3"
    ]

    assert seq_0.connected_output_indices == (0,)
    assert seq_0.nco_en is True
    assert seq_1.connected_input_indices == (0,)
    assert seq_1.ttl_acq_auto_bin_incr_en is False
    assert seq_2.connected_output_indices == (1,)
    assert seq_2.nco_en is True
    assert seq_3.connected_input_indices == (1,)
    assert seq_3.ttl_acq_auto_bin_incr_en is True

    instr_coordinator.remove_component("ic_cluster0")


# TODO split up into smaller units
@pytest.mark.parametrize(
    "module_under_test",
    [ClusterType.CLUSTER_QRM_RF, ClusterType.CLUSTER_QRM, ClusterType.CLUSTER_QRC],
)
def test_trace_acquisition_instrument_coordinator(  # noqa: PLR0915
    mocker,
    mock_setup_basic_transmon_with_standard_params,
    make_cluster_component,
    module_under_test,
):
    hardware_cfgs = {}
    hardware_cfgs[ClusterType.CLUSTER_QRM_RF] = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {"4": {"instrument_type": "QRM_RF"}},
                "ref": "internal",
            }
        },
        "hardware_options": {
            "modulation_frequencies": {"q2:res-q2.ro": {"interm_freq": 50000000.0}}
        },
        "connectivity": {"graph": [["cluster0.module4.complex_input_0", "q2:res"]]},
    }

    hardware_cfgs[ClusterType.CLUSTER_QRM] = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {"3": {"instrument_type": "QRM"}},
                "ref": "internal",
            }
        },
        "hardware_options": {},
        "connectivity": {"graph": [["cluster0.module3.complex_input_0", "q2:res"]]},
    }

    hardware_cfgs[ClusterType.CLUSTER_QRC] = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {"14": {"instrument_type": "QRC"}},
                "ref": "internal",
            }
        },
        "hardware_options": {
            "modulation_frequencies": {"q2:res-q2.ro": {"interm_freq": 50000000.0}}
        },
        "connectivity": {"graph": [["cluster0.module14.complex_input_1", "q2:res"]]},
    }

    hardware_cfg = hardware_cfgs[module_under_test]

    mock_setup = mock_setup_basic_transmon_with_standard_params
    instr_coordinator = mock_setup["instrument_coordinator"]

    name = "cluster0"

    try:
        ic_component = make_cluster_component(name)
    except KeyError:
        close_instruments([name])

    hardware_cfg_module_names = {
        f"{name}_module{idx}" for idx in hardware_cfg["hardware_description"]["cluster0"]["modules"]
    }
    module_name = hardware_cfg_module_names.intersection(ic_component._cluster_modules).pop()

    try:
        instr_coordinator.add_component(ic_component)
    except ValueError:
        ic_component.instrument.reset()

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    q2 = mock_setup["q2"]
    q2.measure.acq_delay = 600e-9
    q2.clock_freqs.readout = 7.404e9 if module_under_test is not ClusterType.CLUSTER_QRM else 3e8

    schedule = trace_schedule_circuit_layer(qubit_name="q2")

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    module = (
        ic_component._cluster_modules[module_name]
        if isinstance(module_under_test, ClusterType)
        else ic_component
    )

    # Setup dummy acquisition data
    if module_under_test is ClusterType.CLUSTER_QRC:
        dummy_scope_acquisition_data = DummyScopeAcquisitionData(
            data=[(0, 1, 2, 0)] * 15000,
            out_of_range=(False, False, False, False),
            avg_cnt=(0, 0, 0, 0),
        )
    else:
        dummy_scope_acquisition_data = DummyScopeAcquisitionData(
            data=[(0, 1)] * 15000, out_of_range=(False, False), avg_cnt=(0, 0)
        )
    module.instrument.set_dummy_scope_acquisition_data(
        sequencer=None, data=dummy_scope_acquisition_data
    )

    wrapped = _AnalogModuleComponent._set_parameter

    called_set_parameter_with = []

    def wrapper(*args, **kwargs):
        called_set_parameter_with.append(args + tuple(kwargs.values()))
        wrapped(module, *args, **kwargs)

    with mocker.patch(
        "qblox_scheduler.instrument_coordinator.components.qblox."
        "_AnalogModuleComponent._set_parameter",
        wraps=wrapper,
    ):
        try:
            instr_coordinator.prepare(compiled_sched)
        except:
            pprint.pprint(compiled_sched.compiled_instructions)
            raise

    assert (module.instrument, "scope_acq_sequencer_select", 0) in called_set_parameter_with

    instr_coordinator.start()
    acquired_data = instr_coordinator.retrieve_acquisition()
    instr_coordinator.stop()

    module.instrument.store_scope_acquisition.assert_called_with(0, "0")

    expected_scope_single_data = 1j if module_under_test is not ClusterType.CLUSTER_QRC else 2

    assert isinstance(acquired_data, Dataset)
    expected_dataarray = DataArray(
        [[expected_scope_single_data] * 1000],
        coords=[[0], range(1000)],
        dims=["acq_index_2", "trace_index_2"],
        attrs={"acq_protocol": "Trace", "acq_index_dim_name": "acq_index_2"},
    )
    expected_dataset = Dataset({2: expected_dataarray})
    xr.testing.assert_identical(acquired_data, expected_dataset)
    instr_coordinator.remove_component(ic_component.name)


def test_mix_lo_flag(mock_setup_basic_transmon_with_standard_params, make_cluster_component):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {
                    "1": {
                        "instrument_type": "QCM",
                        "complex_output_0": {"mix_lo": True},
                    }
                },
                "ref": "internal",
            },
            "iq_mixer_lo0": {"instrument_type": "IQMixer"},
            "lo0": {"instrument_type": "LocalOscillator", "power": 1},
        },
        "hardware_options": {
            "modulation_frequencies": {"q0:res-q0.ro": {"lo_freq": None, "interm_freq": 50000000.0}}
        },
        "connectivity": {
            "graph": [
                ["cluster0.module1.complex_output_0", "iq_mixer_lo0.if"],
                ["lo0.output", "iq_mixer_lo0.lo"],
                ["iq_mixer_lo0.rf", "q0:res"],
            ]
        },
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon_with_standard_params
    ic_cluster0 = make_cluster_component("cluster0")
    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)
    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    # Define experiment schedule
    schedule = TimeableSchedule("test mix_lo flag")
    schedule.add(SquarePulse(amp=0.2, duration=1e-6, port="q0:res", clock="q0.ro"))

    # Generate compiled schedule where mix_lo is true
    compiler = SerialCompiler(name="compiler")
    compiled_sched_mix_lo_true = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Change mix_lo to false, set new LO freq and generate new compiled schedule
    quantum_device.hardware_config.hardware_description["cluster0"].modules[
        1
    ].complex_output_0.mix_lo = False
    compiled_sched_mix_lo_false = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Assert LO freq got set if mix_lo is true.
    assert compiled_sched_mix_lo_true.compiled_instructions["generic"]["lo0.frequency"] == 7.95e9
    # Assert LO freq got set if mix_lo is false.
    assert compiled_sched_mix_lo_false.compiled_instructions["generic"]["lo0.frequency"] == 8e9
    # Assert NCO freq got set if mix_lo is false.
    assert (
        compiled_sched_mix_lo_false.compiled_instructions["cluster0"]["cluster0_module1"][
            "sequencers"
        ]["seq0"].modulation_freq
        == 50e6
    )
    instr_coordinator.remove_component("ic_cluster0")


def test_marker_debug_mode_enable(
    mock_setup_basic_transmon_with_standard_params,
    make_cluster_component,
    assert_equal_q1asm,
):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {
                    "1": {
                        "instrument_type": "QRM",
                        "complex_input_0": {"marker_debug_mode_enable": True},
                    }
                },
                "ref": "internal",
            }
        },
        "hardware_options": {"modulation_frequencies": {"q0:res-q0.ro": {"interm_freq": 0}}},
        "connectivity": {"graph": [["cluster0.module1.complex_input_0", "q0:res"]]},
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon_with_standard_params
    ic_cluster0 = make_cluster_component("cluster0")
    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)
    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    # Define experiment schedule
    schedule = TimeableSchedule("test marker_enable")
    schedule.add(ShiftClockPhase(phase_shift=20, clock="q0.ro"))
    schedule.add(
        Measure("q0", acq_protocol="SSBIntegrationComplex", bin_mode=BinMode.AVERAGE),
        rel_time=20e-9,
    )
    schedule.add_resource(ClockResource(name="q0.res", freq=50e6))

    # Generate compiled schedule for QRM
    compiler = SerialCompiler(name="compiler")
    compiled_sched_qrm = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Generate compiled schedule for QRM-RF
    quantum_device.hardware_config.hardware_description["cluster0"].modules = {
        "1": {"instrument_type": "QRM_RF", "complex_input_0": {"marker_debug_mode_enable": True}}
    }  # Re-assigning the whole `modules` dict is necessary to trigger Pydantic validation
    compiled_sched_qrm_rf = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Assert markers were set correctly, and wait time is correct for both modules.
    assert_equal_q1asm(
        compiled_sched_qrm.compiled_instructions["cluster0"]["cluster0_module1"]["sequencers"][
            "seq0"
        ].sequence["program"],
        """
 set_mrk 0 # set markers to 0
 wait_sync 4
 upd_param 4
 wait 4 # latency correction of 4 + 0 ns
 move 1,R0 # iterator for loop with label start
start:
 reset_ph
 upd_param 4
 set_ph_delta 55555556 # increment nco phase by 20.00 deg
 upd_param 4
 wait 16 # auto generated wait (16 ns)
 reset_ph
 set_mrk 3 # set markers to 3
 set_awg_gain 8192,0 # setting gain for SquarePulse
 play 0,0,4 # play SquarePulse (300 ns)
 set_mrk 0 # set markers to 0
 upd_param 4
 wait 92 # auto generated wait (92 ns)
 set_mrk 12 # set markers to 12
 acquire 0,0,4
 set_mrk 0 # set markers to 0
 upd_param 4
 wait 992 # auto generated wait (992 ns)
 loop R0,@start
 stop
        """,
    )

    assert_equal_q1asm(
        compiled_sched_qrm_rf.compiled_instructions["cluster0"]["cluster0_module1"]["sequencers"][
            "seq0"
        ].sequence["program"],
        """
 set_mrk 2 # set markers to 2
 wait_sync 4
 upd_param 4
 wait 4 # latency correction of 4 + 0 ns
 move 1,R0 # iterator for loop with label start
start:
 reset_ph
 upd_param 4
 set_ph_delta 55555556 # increment nco phase by 20.00 deg
 upd_param 4
 wait 16 # auto generated wait (16 ns)
 reset_ph
 set_mrk 6 # set markers to 6
 set_awg_gain 8192,0 # setting gain for SquarePulse
 play 0,0,4 # play SquarePulse (300 ns)
 set_mrk 2 # set markers to 2
 upd_param 4
 wait 92 # auto generated wait (92 ns)
 set_mrk 10 # set markers to 10
 acquire 0,0,4
 set_mrk 2 # set markers to 2
 upd_param 4
 wait 992 # auto generated wait (992 ns)
 loop R0,@start
 stop
        """,
    )

    instr_coordinator.remove_component("ic_cluster0")


def test_multiple_binned_measurements(mock_setup_basic_transmon, make_cluster_component):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {
                    "3": {"instrument_type": "QRM"},
                    "4": {"instrument_type": "QRM_RF"},
                },
                "ref": "internal",
            }
        },
        "hardware_options": {
            "modulation_frequencies": {
                "q0:res-q0.ro": {"interm_freq": 50000000.0},
                "q1:res-q1.ro": {"interm_freq": 50000000.0},
            }
        },
        "connectivity": {
            "graph": [
                ["cluster0.module3.complex_output_0", "q0:res"],
                ["cluster0.module4.complex_output_0", "q1:res"],
            ]
        },
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon
    ic_cluster0 = make_cluster_component("cluster0")

    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    q0 = mock_setup["q0"]
    q1 = mock_setup["q1"]
    q0.clock_freqs.readout = 50e6
    q1.clock_freqs.readout = 50e6

    # Define experiment schedule
    schedule = TimeableSchedule("test multiple measurements")
    schedule.add(
        Measure(
            "q0",
            coords={"index_0": 0},
            acq_protocol="SSBIntegrationComplex",
            bin_mode=BinMode.AVERAGE,
        )
    )
    schedule.add(
        Measure(
            "q0",
            coords={"index_0": 1},
            acq_protocol="SSBIntegrationComplex",
            bin_mode=BinMode.AVERAGE,
        )
    )
    schedule.add(
        SSBIntegrationComplex(
            port="q0:res",
            clock="q0.ro",
            duration=5e-6,
            acq_channel=0,
            coords={"index_0": 2},
            bin_mode=BinMode.AVERAGE,
        )
    )
    schedule.add(
        SSBIntegrationComplex(
            port="q0:res",
            clock="q0.ro",
            duration=5e-6,
            acq_channel=0,
            coords={"index_0": 3},
            bin_mode=BinMode.AVERAGE,
        )
    )
    schedule.add(
        SSBIntegrationComplex(
            port="q0:res",
            clock="q0.ro",
            duration=5e-6,
            acq_channel=2,
            coords={"index_2": 0},
            bin_mode=BinMode.AVERAGE,
        )
    )
    schedule.add(
        SSBIntegrationComplex(
            port="q0:res",
            clock="q0.ro",
            duration=5e-6,
            acq_channel=2,
            coords={"index_2": 1},
            bin_mode=BinMode.AVERAGE,
        )
    )
    schedule.add(
        Measure(
            "q1",
            acq_channel="ch_1",
            coords={"index_ch_1": 0},
            acq_protocol="SSBIntegrationComplex",
            bin_mode=BinMode.AVERAGE,
        )
    )
    schedule.add(
        Measure(
            "q1",
            acq_channel="ch_1",
            coords={"index_ch_1": 1},
            acq_protocol="SSBIntegrationComplex",
            bin_mode=BinMode.AVERAGE,
        )
    )
    schedule.add(
        SSBIntegrationComplex(
            port="q1:res",
            clock="q1.ro",
            duration=5e-6,
            acq_channel="ch_1",
            coords={"index_ch_1": 2},
            bin_mode=BinMode.AVERAGE,
        )
    )
    schedule.add(
        SSBIntegrationComplex(
            port="q1:res",
            clock="q1.ro",
            duration=5e-6,
            acq_channel="ch_1",
            coords={"index_ch_1": 3},
            bin_mode=BinMode.AVERAGE,
        )
    )
    schedule.add(
        SSBIntegrationComplex(
            port="q1:res",
            clock="q1.ro",
            duration=5e-6,
            acq_channel=3,
            coords={"index_3": 0},
            bin_mode=BinMode.AVERAGE,
        )
    )
    schedule.add(
        SSBIntegrationComplex(
            port="q1:res",
            clock="q1.ro",
            duration=5e-6,
            acq_channel=3,
            coords={"index_3": 1},
            bin_mode=BinMode.AVERAGE,
        )
    )

    # Change acq delay, duration and channel
    q0.measure.acq_delay = 1e-6
    q1.measure.acq_delay = 1e-6
    q0.measure.integration_time = 5e-6
    q1.measure.integration_time = 5e-6
    q0.measure.acq_channel = 0
    q1.measure.acq_channel = 1
    q1.clock_freqs.readout = 7404000000.0

    # Setup dummy acquisition data
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=0,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(10000, 15000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(20000, 25000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(30000, 35000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(40000, 45000), thres=0, avg_cnt=0),
        ],
    )
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=0,
        acq_index_name="1",
        data=[
            DummyBinnedAcquisitionData(data=(50000, 55000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(60000, 65000), thres=0, avg_cnt=0),
        ],
    )
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=4,
        sequencer=0,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(100000, 150000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(200000, 250000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(300000, 350000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(400000, 450000), thres=0, avg_cnt=0),
        ],
    )
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=4,
        sequencer=0,
        acq_index_name="1",
        data=[
            DummyBinnedAcquisitionData(data=(500000, 550000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(600000, 650000), thres=0, avg_cnt=0),
        ],
    )

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_sched)
    instr_coordinator.start()
    data = instr_coordinator.retrieve_acquisition()
    instr_coordinator.stop()

    # Assert intended behaviour
    assert isinstance(data, Dataset)
    expected_dataset = Dataset(
        {
            0: DataArray(
                [2 + 3j, 4 + 5j, 6 + 7j, 8 + 9j],
                coords={
                    "acq_index_0": [0, 1, 2, 3],
                    "index_0": ("acq_index_0", [0, 1, 2, 3]),
                },
                dims=["acq_index_0"],
                attrs={
                    "acq_protocol": "SSBIntegrationComplex",
                    "acq_index_dim_name": "acq_index_0",
                },
            ),
            2: DataArray(
                [10 + 11j, 12 + 13j],
                coords={
                    "acq_index_2": [0, 1],
                    "index_2": ("acq_index_2", [0, 1]),
                },
                dims=["acq_index_2"],
                attrs={
                    "acq_protocol": "SSBIntegrationComplex",
                    "acq_index_dim_name": "acq_index_2",
                },
            ),
            "ch_1": DataArray(
                [20 + 30j, 40 + 50j, 60 + 70j, 80 + 90j],
                coords={
                    "acq_index_ch_1": [0, 1, 2, 3],
                    "index_ch_1": ("acq_index_ch_1", [0, 1, 2, 3]),
                },
                dims=["acq_index_ch_1"],
                attrs={
                    "acq_protocol": "SSBIntegrationComplex",
                    "acq_index_dim_name": "acq_index_ch_1",
                },
            ),
            3: DataArray(
                [100 + 110j, 120 + 130j],
                coords={
                    "acq_index_3": [0, 1],
                    "index_3": ("acq_index_3", [0, 1]),
                },
                dims=["acq_index_3"],
                attrs={
                    "acq_protocol": "SSBIntegrationComplex",
                    "acq_index_dim_name": "acq_index_3",
                },
            ),
        }
    )

    xr.testing.assert_identical(data, expected_dataset)

    instr_coordinator.remove_component("ic_cluster0")


def test_append_measurements(mock_setup_basic_transmon, make_cluster_component):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {"3": {"instrument_type": "QRM"}},
                "ref": "internal",
            }
        },
        "hardware_options": {
            "modulation_frequencies": {"q0:res-q0.ro": {"interm_freq": 50000000.0}}
        },
        "connectivity": {"graph": [["cluster0.module3.complex_output_0", "q0:res"]]},
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon
    ic_cluster0 = make_cluster_component("cluster0")

    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    q0 = mock_setup["q0"]
    q0.clock_freqs.readout = 50e6

    # Define experiment schedule
    schedule = TimeableSchedule("test multiple measurements", repetitions=3)
    schedule.add(
        Measure(
            "q0",
            coords={"index": 0},
            acq_protocol="SSBIntegrationComplex",
            bin_mode=BinMode.APPEND,
        )
    )
    schedule.add(
        Measure(
            "q0",
            coords={"index": 1},
            acq_protocol="SSBIntegrationComplex",
            bin_mode=BinMode.APPEND,
        )
    )

    # Change acq delay, duration and channel
    q0.measure.acq_delay = 1e-6
    q0.measure.integration_time = 5e-6
    q0.measure.acq_channel = 1

    # Setup dummy acquisition data
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=0,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(10000, 15000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(30000, 35000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(50000, 55000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(20000, 25000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(40000, 45000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(60000, 65000), thres=0, avg_cnt=0),
        ],
    )

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_sched)
    instr_coordinator.start()
    data = instr_coordinator.retrieve_acquisition()
    instr_coordinator.stop()

    # Assert intended behaviour
    assert isinstance(data, Dataset)
    expected_dataset = Dataset(
        {
            1: DataArray(
                [[2 + 3j, 4 + 5j], [6 + 7j, 8 + 9j], [10 + 11j, 12 + 13j]],
                coords={
                    "repetition": [0, 1, 2],
                    "acq_index_1": [0, 1],
                    "index": ("acq_index_1", [0, 1]),
                },
                dims=["repetition", "acq_index_1"],
                attrs={
                    "acq_protocol": "SSBIntegrationComplex",
                    "acq_index_dim_name": "acq_index_1",
                },
            ),
        }
    )
    xr.testing.assert_identical(data, expected_dataset)

    instr_coordinator.remove_component("ic_cluster0")


def test_looped_measurements(mock_setup_basic_transmon, make_cluster_component):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "ref": "internal",
                "modules": {
                    "3": {"instrument_type": "QRM"},
                },
            }
        },
        "hardware_options": {
            "modulation_frequencies": {
                "q0:res-q0.ro": {
                    "interm_freq": 50e6,
                }
            }
        },
        "connectivity": {
            "graph": [
                ["cluster0.module3.complex_output_0", "q0:res"],
            ]
        },
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon
    ic_cluster0 = make_cluster_component("cluster0")

    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    q0 = mock_setup["q0"]
    q0.clock_freqs.readout = 50e6

    # Define experiment schedule
    schedule = TimeableSchedule("test multiple measurements", repetitions=2)
    schedule.add(
        LoopOperation(
            body=Measure(
                "q0",
                coords={"index": 0},
                acq_protocol="SSBIntegrationComplex",
                bin_mode=BinMode.APPEND,
            ),
            repetitions=3,
        )
    )

    # Change acq delay, duration and channel
    q0.measure.acq_delay = 1e-6
    q0.measure.integration_time = 5e-6
    q0.measure.acq_channel = 0

    # Setup dummy acquisition data
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=0,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(10000, 15000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(20000, 25000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(30000, 35000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(40000, 45000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(50000, 55000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(60000, 65000), thres=0, avg_cnt=0),
        ],
    )

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_sched)
    instr_coordinator.start()

    data = instr_coordinator.retrieve_acquisition()

    instr_coordinator.stop()

    # Assert intended behaviour
    assert isinstance(data, Dataset)
    expected_dataset = Dataset(
        {
            0: DataArray(
                [[2 + 3j, 4 + 5j, 6 + 7j], [8 + 9j, 10 + 11j, 12 + 13j]],
                coords={
                    "loop_repetition_0": ("acq_index_0", [0, 1, 2]),
                    "repetition": [0, 1],
                    "acq_index_0": [0, 1, 2],
                    "index": ("acq_index_0", [0, 0, 0]),
                },
                dims=["repetition", "acq_index_0"],
                attrs={
                    "acq_protocol": "SSBIntegrationComplex",
                    "acq_index_dim_name": "acq_index_0",
                },
            ),
        }
    )

    xr.testing.assert_identical(data, expected_dataset)

    instr_coordinator.remove_component("ic_cluster0")


def test_average_append_measurements_averaging(
    mock_setup_basic_transmon, make_cluster_component, assert_equal_q1asm
):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "ref": "internal",
                "modules": {
                    "3": {"instrument_type": "QRM"},
                },
            }
        },
        "hardware_options": {
            "modulation_frequencies": {
                "q0:res-q0.ro": {
                    "interm_freq": 50e6,
                }
            }
        },
        "connectivity": {
            "graph": [
                ["cluster0.module3.complex_output_0", "q0:res"],
            ]
        },
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon
    ic_cluster0 = make_cluster_component("cluster0")

    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    q0 = mock_setup["q0"]
    q0.clock_freqs.readout = 50e6

    # Define experiment schedule
    schedule = TimeableSchedule("test multiple measurements", repetitions=2)
    with (
        schedule.loop(linspace(0.0, 0.1, 2, DType.AMPLITUDE)),
        schedule.loop(linspace(0.0, 0.1, 3, DType.AMPLITUDE)) as amp,
    ):
        schedule.add(
            SSBIntegrationComplex(
                port="q0:res",
                clock="q0.ro",
                duration=5e-6,
                acq_channel=0,
                bin_mode=BinMode.AVERAGE_APPEND,
                coords={"amp": amp},
            )
        )

    # Setup dummy acquisition data
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=0,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(10000, 15000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(20000, 25000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(30000, 35000), thres=0, avg_cnt=0),
        ],
    )

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module3"]["sequencers"][
            "seq0"
        ].sequence["program"],
        [
            " set_mrk 0 # set markers to 0 (init)",
            " wait_sync 4 ",
            " upd_param 4 ",
            " move 0,R0 # Initialize acquisition bin_idx for channel 0",
            " wait 4 # latency correction of 4 + 0 ns",
            " move 2,R1 # iterator for loop with label start",
            "start:   ",
            " reset_ph  ",
            " upd_param 4 ",
            " move 0,R3 # Initialize sweep var",
            " move 2,R2 # iterator for loop with label loop9",
            "loop9:   ",
            " move 0,R5 # Initialize sweep var",
            " move 3,R4 # iterator for loop with label loop12",
            "loop12:   ",
            "   ",
            " acquire 0,R0,4 ",
            " add R0,1,R0 # Increment bin_idx for ch0",
            "   ",
            " wait 4996 # auto generated wait (4996 ns)",
            " add R5,107374182,R5 # Update sweep var",
            " loop R4,@loop12 ",
            " sub R0,3,R0 # Decrement bin_idx for averaging",
            " add R3,214748365,R3 # Update sweep var",
            " loop R2,@loop9 ",
            " loop R1,@start ",
            " add R0,3,R0 # Increment bin_idx for averaging",
            " stop  ",
        ],
    )

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_sched)
    instr_coordinator.start()

    data = instr_coordinator.retrieve_acquisition()

    instr_coordinator.stop()

    # Assert intended behaviour
    assert isinstance(data, Dataset)
    expected_dataset = Dataset(
        {
            0: DataArray(
                [2 + 3j, 4 + 5j, 6 + 7j],
                coords={
                    "loop_repetition_0": ("acq_index_0", [0, 1, 2]),
                    "acq_index_0": [0, 1, 2],
                    "amp": ("acq_index_0", [0.0, 0.05, 0.1]),
                },
                dims=["acq_index_0"],
                attrs={
                    "acq_protocol": "SSBIntegrationComplex",
                    "acq_index_dim_name": "acq_index_0",
                },
            ),
        }
    )

    xr.testing.assert_identical(data, expected_dataset)

    instr_coordinator.remove_component("ic_cluster0")


def test_multiple_modules_same_channel(mock_setup_basic_transmon, make_cluster_component):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {
                    "3": {"instrument_type": "QRM"},
                    "4": {"instrument_type": "QRM_RF"},
                },
                "ref": "internal",
            }
        },
        "hardware_options": {
            "modulation_frequencies": {
                "q0:res-q0.ro": {"interm_freq": 50000000.0},
                "q1:res-q1.ro": {"interm_freq": 50000000.0},
            }
        },
        "connectivity": {
            "graph": [
                ["cluster0.module3.complex_output_0", "q0:res"],
                ["cluster0.module4.complex_output_0", "q1:res"],
            ]
        },
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon
    ic_cluster0 = make_cluster_component("cluster0")

    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    q0 = mock_setup["q0"]
    q1 = mock_setup["q1"]
    q0.clock_freqs.readout = 50e6
    q1.clock_freqs.readout = 50e6

    # Define experiment schedule
    schedule = TimeableSchedule("test multiple measurements")
    schedule.add(
        SSBIntegrationComplex(
            port="q0:res", clock="q0.ro", duration=5e-6, acq_channel=0, coords={"index": 0}
        )
    )
    schedule.add(
        SSBIntegrationComplex(
            port="q1:res", clock="q1.ro", duration=5e-6, acq_channel=0, coords={"index": 1}
        )
    )

    # Change acq delay, duration and channel
    q1.clock_freqs.readout = 7404000000.0

    # Setup dummy acquisition data
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=0,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(10000, 15000), thres=0, avg_cnt=0),
        ],
    )
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=4,
        sequencer=0,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(20000, 25000), thres=0, avg_cnt=0),
        ],
    )

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_sched)
    instr_coordinator.start()
    data = instr_coordinator.retrieve_acquisition()
    instr_coordinator.stop()

    # Assert intended behaviour
    assert isinstance(data, Dataset)
    expected_dataset = Dataset(
        {
            0: DataArray(
                [2 + 3j, 4 + 5j],
                coords={
                    "acq_index_0": [0, 1],
                    "index": ("acq_index_0", [0, 1]),
                },
                dims=["acq_index_0"],
                attrs={
                    "acq_protocol": "SSBIntegrationComplex",
                    "acq_index_dim_name": "acq_index_0",
                },
            ),
        }
    )

    xr.testing.assert_identical(data, expected_dataset)

    instr_coordinator.remove_component("ic_cluster0")


def test_conflicting_retrieve_multiple_acquisitions(
    mock_setup_basic_transmon, make_cluster_component
):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "modules": {
                    "3": {"instrument_type": "QRM"},
                    "4": {"instrument_type": "QRM_RF"},
                },
                "ref": "internal",
            }
        },
        "hardware_options": {
            "modulation_frequencies": {
                "q0:res-q0.ro": {"interm_freq": 50000000.0},
                "q1:res-q1.ro": {"interm_freq": 50000000.0},
            }
        },
        "connectivity": {
            "graph": [
                ["cluster0.module3.complex_output_0", "q0:res"],
                ["cluster0.module4.complex_output_0", "q1:res"],
            ]
        },
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon
    ic_cluster0 = make_cluster_component("cluster0")

    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    q0 = mock_setup["q0"]
    q1 = mock_setup["q1"]
    q0.clock_freqs.readout = 50e6
    q1.clock_freqs.readout = 50e6

    # Define experiment schedule
    schedule = TimeableSchedule("test multiple measurements")
    schedule.add(
        SSBIntegrationComplex(
            port="q0:res", clock="q0.ro", duration=5e-6, acq_channel=0, coords={"index": 0}
        )
    )
    schedule.add(
        SSBIntegrationComplex(
            port="q1:res", clock="q1.ro", duration=5e-6, acq_channel=0, coords={"index": 1}
        )
    )

    # Change acq delay, duration and channel
    q1.clock_freqs.readout = 7404000000.0

    # Setup dummy acquisition data
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=0,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(10000, 15000), thres=0, avg_cnt=0),
        ],
    )
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=4,
        sequencer=0,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(20000, 25000), thres=0, avg_cnt=0),
        ],
    )

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Emulate incorrect data mapping for InstrumentCoordinator
    # to retrieve data for the same acquisition index.
    compiled_sched["compiled_instructions"]["cluster0"]["cluster0_module4"][
        "acq_hardware_mapping"
    ] = compiled_sched["compiled_instructions"]["cluster0"]["cluster0_module3"][
        "acq_hardware_mapping"
    ]

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_sched)
    instr_coordinator.start()
    with pytest.raises(
        RuntimeError,
        match=r"Attempting to gather acquisitions. "
        "Make sure an acq_channel, acq_index corresponds to not more than one acquisition.\n"
        "The following indices are defined multiple times.\n"
        "acq_channel=0; acq_index_0=0",
    ):
        instr_coordinator.retrieve_acquisition()

    instr_coordinator.stop()

    instr_coordinator.remove_component("ic_cluster0")


def test_expressions_as_coords_end_to_end(
    mock_setup_basic_transmon, make_cluster_component, assert_equal_q1asm
):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "ref": "internal",
                "modules": {
                    "3": {"instrument_type": "QRM"},
                },
            }
        },
        "hardware_options": {
            "modulation_frequencies": {
                "q0:res-q0.ro": {
                    "interm_freq": 50e6,
                }
            }
        },
        "connectivity": {
            "graph": [
                ["cluster0.module3.complex_output_0", "q0:res"],
            ]
        },
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon
    ic_cluster0 = make_cluster_component("cluster0")

    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    q0 = mock_setup["q0"]
    q0.clock_freqs.readout = 50e6

    schedule = TimeableSchedule("Schedule", repetitions=1)

    schedule.add_resource(ClockResource(name="q0.01", freq=50e6))

    with (
        schedule.loop(linspace(0.0, 1.0, 2, DType.AMPLITUDE)) as amp_1,
        schedule.loop(linspace(0.0, 0.2, 3, DType.AMPLITUDE)) as amp_2,
    ):
        schedule.add(
            SSBIntegrationComplex(
                acq_channel="ch_0",
                coords={"freq": 100, "amp_1": amp_1, "amp_avg": (amp_2 + amp_1) / 2},
                acq_index=None,
                bin_mode=BinMode.APPEND,
                port="q0:res",
                clock="q0.01",
                duration=5e-6,
            )
        )

    # Setup dummy acquisition data
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=0,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(10000, 15000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(20000, 25000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(30000, 35000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(40000, 45000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(50000, 55000), thres=0, avg_cnt=0),
            DummyBinnedAcquisitionData(data=(60000, 65000), thres=0, avg_cnt=0),
        ],
    )

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_sched)
    instr_coordinator.start()

    data = instr_coordinator.retrieve_acquisition()

    instr_coordinator.stop()

    # Assert intended behaviour
    assert isinstance(data, Dataset)
    expected_dataset = Dataset(
        {
            "ch_0": DataArray(
                [[2 + 3j, 4 + 5j, 6 + 7j, 8 + 9j, 10 + 11j, 12 + 13j]],
                coords={
                    "repetition": [0],
                    "acq_index_ch_0": [0, 1, 2, 3, 4, 5],
                    "loop_repetition_ch_0": ("acq_index_ch_0", [0, 1, 2, 3, 4, 5]),
                    "freq": ("acq_index_ch_0", [100, 100, 100, 100, 100, 100]),
                    "amp_1": ("acq_index_ch_0", [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]),
                    "amp_avg": ("acq_index_ch_0", [0.0, 0.05, 0.1, 0.5, 0.55, 0.6]),
                },
                dims=["repetition", "acq_index_ch_0"],
                attrs={
                    "acq_protocol": "SSBIntegrationComplex",
                    "acq_index_dim_name": "acq_index_ch_0",
                },
            ),
        }
    )

    xr.testing.assert_identical(data, expected_dataset)

    instr_coordinator.remove_component("ic_cluster0")


def test_arbitrary_averaging_by_coords(
    mock_setup_basic_transmon, make_cluster_component, assert_equal_q1asm
):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "ref": "internal",
                "modules": {
                    "3": {"instrument_type": "QRM"},
                },
            }
        },
        "hardware_options": {
            "modulation_frequencies": {
                "q0:res-q0.ro": {
                    "interm_freq": 50e6,
                }
            }
        },
        "connectivity": {
            "graph": [
                ["cluster0.module3.complex_output_0", "q0:res"],
            ]
        },
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon
    ic_cluster0 = make_cluster_component("cluster0")

    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    q0 = mock_setup["q0"]
    q0.clock_freqs.readout = 50e6

    schedule = TimeableSchedule("Schedule", repetitions=1)

    schedule.add_resource(ClockResource(name="q0.01", freq=50e6))

    with (
        schedule.loop(linspace(0.0, 0.1, 2, DType.AMPLITUDE)) as amp_1,
        schedule.loop(linspace(0.0, 0.2, 3, DType.AMPLITUDE)) as amp_2,
        schedule.loop(linspace(0.0, 0.3, 4, DType.AMPLITUDE)),
        schedule.loop(linspace(0.0, 0.4, 5, DType.AMPLITUDE)) as amp_4,
    ):
        schedule.add(
            SSBIntegrationComplex(
                acq_channel="ch_0",
                coords={
                    "freq": 100,
                    "amp_1": amp_1,
                    "amp_avg": (amp_1 + amp_2) / 2,
                    "amp_4": amp_4,
                },
                acq_index=None,
                bin_mode=BinMode.AVERAGE_APPEND,
                port="q0:res",
                clock="q0.01",
                duration=5e-6,
            )
        )
        schedule.add(
            LoopOperation(
                body=SquarePulse(amp=0.1, duration=1e-6, port="q0:res", clock="q0.01"),
                repetitions=10,
            )
        )

    # Setup dummy acquisition data
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=0,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(i * 10000, i * 15000), thres=0, avg_cnt=0)
            for i in range(2 * 3 * 5)
        ],
    )

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module3"]["sequencers"][
            "seq0"
        ].sequence["program"],
        [
            " set_mrk 0 # set markers to 0 (init)",
            " wait_sync 4",
            " upd_param 4",
            " move 0,R0 # Initialize acquisition bin_idx for channel ch_0",
            " wait 4 # latency correction of 4 + 0 ns",
            " move 1,R1 # iterator for loop with label start",
            "start:",
            " reset_ph",
            " upd_param 4",
            " move 0,R3 # Initialize sweep var",
            " move 2,R2 # iterator for loop with label loop9",
            "loop9:",
            " move 0,R5 # Initialize sweep var",
            " move 3,R4 # iterator for loop with label loop12",
            "loop12:",
            " move 0,R7 # Initialize sweep var",
            " move 4,R6 # iterator for loop with label loop15",
            "loop15:",
            " move 0,R9 # Initialize sweep var",
            " move 5,R8 # iterator for loop with label loop18",
            "loop18:",
            " acquire 0,R0,4",
            " add R0,1,R0 # Increment bin_idx for chch_0",
            " wait 4996 # auto generated wait (4996 ns)",
            " move 10,R10 # iterator for loop with label loop26",
            "loop26:",
            " set_awg_offs 3277,0 # setting offset for SquarePulse",
            " upd_param 4",
            " wait 992 # auto generated wait (992 ns)",
            " set_awg_offs 0,0 # setting offset for SquarePulse",
            " set_awg_gain 3277,0 # setting gain for SquarePulse",
            " play 0,0,4 # play SquarePulse (4 ns)",
            " loop R10,@loop26",
            " add R9,214748364,R9 # Update sweep var",
            " loop R8,@loop18",
            " sub R0,5,R0 # Decrement bin_idx for averaging",
            " add R7,214748364,R7 # Update sweep var",
            " loop R6,@loop15",
            " add R0,5,R0 # Increment bin_idx for averaging",
            " add R5,214748365,R5 # Update sweep var",
            " loop R4,@loop12",
            " add R3,214748365,R3 # Update sweep var",
            " loop R2,@loop9",
            " sub R0,30,R0 # Decrement bin_idx for averaging",
            " loop R1,@start",
            " add R0,30,R0 # Increment bin_idx for averaging",
            " stop  ",
        ],
    )

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_sched)
    instr_coordinator.start()

    data = instr_coordinator.retrieve_acquisition()

    instr_coordinator.stop()

    # Assert intended behaviour
    assert isinstance(data, Dataset)
    expected_dataset = Dataset(
        {
            "ch_0": DataArray(
                [i * (2 + 3j) for i in range(2 * 3 * 5)],
                coords={
                    "acq_index_ch_0": range(2 * 3 * 5),
                    "loop_repetition_ch_0": ("acq_index_ch_0", range(2 * 3 * 5)),
                    "freq": ("acq_index_ch_0", [100] * 2 * 3 * 5),
                    "amp_1": ("acq_index_ch_0", [i * 0.1 for i in range(2) for j in range(3 * 5)]),
                    "amp_avg": (
                        "acq_index_ch_0",
                        [(i + j) / 20 for i in range(2) for j in range(3) for k in range(5)],
                    ),
                    "amp_4": ("acq_index_ch_0", [k * 0.1 for i in range(2 * 3) for k in range(5)]),
                },
                dims=["acq_index_ch_0"],
                attrs={"acq_protocol": "SSBIntegrationComplex"},
            ),
        }
    )

    xr.testing.assert_allclose(data, expected_dataset)

    instr_coordinator.remove_component("ic_cluster0")


def test_one_register_for_all_append(
    mock_setup_basic_transmon, make_cluster_component, assert_equal_q1asm
):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "ref": "internal",
                "modules": {
                    "3": {"instrument_type": "QRM"},
                },
            }
        },
        "hardware_options": {
            "modulation_frequencies": {
                "q0:res-q0.ro": {
                    "interm_freq": 50e6,
                }
            }
        },
        "connectivity": {
            "graph": [
                ["cluster0.module3.complex_output_0", "q0:res"],
                ["cluster0.module3.complex_output_0", "q1:res"],
            ]
        },
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon
    ic_cluster0 = make_cluster_component("cluster0")

    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    schedule = TimeableSchedule("Schedule", repetitions=1)

    schedule.add_resource(ClockResource(name="q0.01", freq=50e6))
    schedule.add_resource(ClockResource(name="q1.01", freq=50e6))

    with schedule.loop(linspace(0.0, 0.1, 2, DType.AMPLITUDE)) as amp_1:
        schedule.add(
            SSBIntegrationComplex(
                acq_channel="ch_0",
                coords={
                    "i_ch_0": 0,
                    "amp_1_ch_0": amp_1,
                },
                bin_mode=BinMode.AVERAGE_APPEND,
                port="q0:res",
                clock="q0.01",
                duration=1e-6,
            )
        )

        with schedule.loop(linspace(0.0, 0.2, 3, DType.AMPLITUDE)) as amp_2:
            schedule.add(
                SSBIntegrationComplex(
                    acq_channel="ch_0",
                    coords={
                        "i_ch_0": 1,
                        "amp_1_ch_0": amp_1,
                        "amp_2_ch_0": amp_2,
                    },
                    bin_mode=BinMode.AVERAGE_APPEND,
                    port="q0:res",
                    clock="q0.01",
                    duration=1e-6,
                )
            )

            with schedule.loop(linspace(0.0, 0.3, 4, DType.AMPLITUDE)) as amp_3:
                schedule.add(
                    SSBIntegrationComplex(
                        acq_channel="ch_1",
                        coords={
                            "i_ch_1": 2,
                            "amp_1_ch_1": amp_1,
                            "amp_2_ch_1": amp_2,
                            "amp_3_ch_1": amp_3,
                        },
                        bin_mode=BinMode.AVERAGE_APPEND,
                        port="q0:res",
                        clock="q0.01",
                        duration=1e-6,
                    )
                )

            # The only averaged acquisition in the schedule,
            # this is on a different Qblox acquisition index.
            schedule.add(
                SSBIntegrationComplex(
                    acq_channel="ch_0",
                    coords={
                        "averaged": 1,
                        "i_ch_0": 3,
                        "amp_1_ch_0": amp_1,
                    },
                    bin_mode=BinMode.AVERAGE_APPEND,
                    port="q0:res",
                    clock="q0.01",
                    duration=1e-6,
                )
            )

            # The is used on the same "ch_0", but
            # on a different portclock, so uses a separate register,
            # and independent of the other acquisitions.
            schedule.add(
                SSBIntegrationComplex(
                    acq_channel="ch_0",
                    coords={
                        "i_ch_0": 4,
                        "amp_1_ch_0": amp_1,
                        "amp_2_ch_0": amp_2,
                    },
                    bin_mode=BinMode.AVERAGE_APPEND,
                    port="q1:res",
                    clock="q1.01",
                    duration=1e-6,
                )
            )

        schedule.add(
            SSBIntegrationComplex(
                acq_channel="ch_0",
                coords={
                    "i_ch_0": 5,
                    "amp_1_ch_0": amp_1,
                },
                bin_mode=BinMode.AVERAGE_APPEND,
                port="q0:res",
                clock="q0.01",
                duration=1e-6,
            )
        )

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module3"]["sequencers"][
            "seq0"
        ].sequence["program"],
        [
            " set_mrk 0 # set markers to 0 (init)",
            " wait_sync 4 ",
            " upd_param 4 ",
            " move 0,R0 # Initialize acquisition bin_idx for acq. group",
            " move 34,R1 # Initialize acquisition bin_idx for acq. group",
            " wait 4 # latency correction of 4 + 0 ns",
            " move 1,R2 # iterator for loop with label start",
            "start:   ",
            " reset_ph  ",
            " upd_param 4 ",
            " move 0,R4 # Initialize sweep var",
            " move 2,R3 # iterator for loop with label loop10",
            "loop10:   ",
            "   ",
            " acquire 0,R0,4 ",
            " add R0,1,R0 # Increment bin_idx for chch_0",
            "   ",
            " wait 996 # auto generated wait (996 ns)",
            " move 0,R6 # Initialize sweep var",
            " move 3,R5 # iterator for loop with label loop18",
            "loop18:   ",
            "   ",
            " acquire 0,R0,4 ",
            " add R0,1,R0 # Increment bin_idx for chch_0",
            "   ",
            " wait 996 # auto generated wait (996 ns)",
            " move 0,R8 # Initialize sweep var",
            " move 4,R7 # iterator for loop with label loop26",
            "loop26:   ",
            "   ",
            " acquire 0,R0,4 ",
            " add R0,1,R0 # Increment bin_idx for chch_1",
            "   ",
            " wait 996 # auto generated wait (996 ns)",
            " add R8,214748364,R8 # Update sweep var",
            " loop R7,@loop26 ",
            "   ",
            " acquire 0,R1,4 ",
            " add R1,1,R1 # Increment bin_idx for chch_0",
            "   ",
            " wait 1996 # auto generated wait (1996 ns)",
            " sub R1,1,R1 # Decrement bin_idx for averaging",
            " add R6,214748365,R6 # Update sweep var",
            " loop R5,@loop18 ",
            " add R1,1,R1 # Increment bin_idx for averaging",
            "   ",
            " acquire 0,R0,4 ",
            " add R0,1,R0 # Increment bin_idx for chch_0",
            "   ",
            " wait 996 # auto generated wait (996 ns)",
            " add R4,214748365,R4 # Update sweep var",
            " loop R3,@loop10 ",
            " sub R0,34,R0 # Decrement bin_idx for averaging",
            " sub R1,2,R1 # Decrement bin_idx for averaging",
            " loop R2,@start ",
            " add R0,34,R0 # Increment bin_idx for averaging",
            " add R1,2,R1 # Increment bin_idx for averaging",
            " stop  ",
        ],
    )

    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module3"]["sequencers"][
            "seq1"
        ].sequence["program"],
        [
            " set_mrk 0 # set markers to 0 (init)",
            " wait_sync 4 ",
            " upd_param 4 ",
            " move 0,R0 # Initialize acquisition bin_idx for acq. group",
            " wait 4 # latency correction of 4 + 0 ns",
            " move 1,R1 # iterator for loop with label start",
            "start:   ",
            " reset_ph  ",
            " upd_param 4 ",
            " move 0,R3 # Initialize sweep var",
            " move 2,R2 # iterator for loop with label loop9",
            "loop9:   ",
            " wait 1000 # auto generated wait (1000 ns)",
            " move 0,R5 # Initialize sweep var",
            " move 3,R4 # iterator for loop with label loop13",
            "loop13:   ",
            " wait 6000 # auto generated wait (6000 ns)",
            "   ",
            " acquire 0,R0,4 ",
            " add R0,1,R0 # Increment bin_idx for chch_0",
            "   ",
            " wait 996 # auto generated wait (996 ns)",
            " add R5,214748365,R5 # Update sweep var",
            " loop R4,@loop13 ",
            " wait 1000 # auto generated wait (1000 ns)",
            " add R3,214748365,R3 # Update sweep var",
            " loop R2,@loop9 ",
            " sub R0,6,R0 # Decrement bin_idx for averaging",
            " loop R1,@start ",
            " add R0,6,R0 # Increment bin_idx for averaging",
            " stop  ",
        ],
    )

    # Setup dummy acquisition data
    ic_cluster0.instrument.delete_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=0,
        acq_index_name="0",
    )
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=0,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(1000, 1000 * i), thres=0, avg_cnt=0)
            for i in range(2 + 2 * 3 + 2 * 3 * 4 + 2)
        ]
        + [DummyBinnedAcquisitionData(data=(2000, 1000 * i), thres=0, avg_cnt=0) for i in range(2)],
    )
    ic_cluster0.instrument.delete_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=1,
        acq_index_name="0",
    )
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=1,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(3000, 1000 * i), thres=0, avg_cnt=0)
            for i in range(2 * 3)
        ],
    )

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_sched)
    instr_coordinator.start()

    data = instr_coordinator.retrieve_acquisition()

    instr_coordinator.stop()

    # Assert intended behaviour
    assert isinstance(data, Dataset)
    expected_dataset = Dataset(
        {
            "ch_0": DataArray(
                [
                    1.0 + 0.0j,
                    1.0 + 17.0j,
                    1.0 + 1.0j,
                    1.0 + 6.0j,
                    1.0 + 11.0j,
                    1.0 + 18.0j,
                    1.0 + 23.0j,
                    1.0 + 28.0j,
                    2.0 + 0.0j,
                    2.0 + 1.0j,
                    3.0 + 0.0j,
                    3.0 + 1.0j,
                    3.0 + 2.0j,
                    3.0 + 3.0j,
                    3.0 + 4.0j,
                    3.0 + 5.0j,
                    1.0 + 16.0j,
                    1.0 + 33.0j,
                ],
                coords={
                    "acq_index_ch_0": [
                        0,
                        1,
                        2,
                        3,
                        4,
                        5,
                        6,
                        7,
                        8,
                        9,
                        10,
                        11,
                        12,
                        13,
                        14,
                        15,
                        16,
                        17,
                    ],
                    "i_ch_0": (
                        "acq_index_ch_0",
                        [
                            0.0,
                            0.0,
                            1.0,
                            1.0,
                            1.0,
                            1.0,
                            1.0,
                            1.0,
                            3.0,
                            3.0,
                            4.0,
                            4.0,
                            4.0,
                            4.0,
                            4.0,
                            4.0,
                            5.0,
                            5.0,
                        ],
                    ),
                    "loop_repetition_ch_0": (
                        "acq_index_ch_0",
                        [
                            0.0,
                            1.0,
                            0.0,
                            1.0,
                            2.0,
                            3.0,
                            4.0,
                            5.0,
                            0.0,
                            1.0,
                            0.0,
                            1.0,
                            2.0,
                            3.0,
                            4.0,
                            5.0,
                            0.0,
                            1.0,
                        ],
                    ),
                    "amp_1_ch_0": (
                        "acq_index_ch_0",
                        [
                            0.0,
                            0.1,
                            0.0,
                            0.0,
                            0.0,
                            0.1,
                            0.1,
                            0.1,
                            0.0,
                            0.1,
                            0.0,
                            0.0,
                            0.0,
                            0.1,
                            0.1,
                            0.1,
                            0.0,
                            0.1,
                        ],
                    ),
                    "amp_2_ch_0": (
                        "acq_index_ch_0",
                        [
                            np.nan,
                            np.nan,
                            0.0,
                            0.1,
                            0.2,
                            0.0,
                            0.1,
                            0.2,
                            np.nan,
                            np.nan,
                            0.0,
                            0.1,
                            0.2,
                            0.0,
                            0.1,
                            0.2,
                            np.nan,
                            np.nan,
                        ],
                    ),
                    "averaged": (
                        "acq_index_ch_0",
                        [
                            np.nan,
                            np.nan,
                            np.nan,
                            np.nan,
                            np.nan,
                            np.nan,
                            np.nan,
                            np.nan,
                            1.0,
                            1.0,
                            np.nan,
                            np.nan,
                            np.nan,
                            np.nan,
                            np.nan,
                            np.nan,
                            np.nan,
                            np.nan,
                        ],
                    ),
                },
                dims=["acq_index_ch_0"],
                attrs={"acq_protocol": "SSBIntegrationComplex"},
            ),
            "ch_1": DataArray(
                [
                    1.0 + 2.0j,
                    1.0 + 3.0j,
                    1.0 + 4.0j,
                    1.0 + 5.0j,
                    1.0 + 7.0j,
                    1.0 + 8.0j,
                    1.0 + 9.0j,
                    1.0 + 10.0j,
                    1.0 + 12.0j,
                    1.0 + 13.0j,
                    1.0 + 14.0j,
                    1.0 + 15.0j,
                    1.0 + 19.0j,
                    1.0 + 20.0j,
                    1.0 + 21.0j,
                    1.0 + 22.0j,
                    1.0 + 24.0j,
                    1.0 + 25.0j,
                    1.0 + 26.0j,
                    1.0 + 27.0j,
                    1.0 + 29.0j,
                    1.0 + 30.0j,
                    1.0 + 31.0j,
                    1.0 + 32.0j,
                ],
                coords={
                    "acq_index_ch_1": [
                        0,
                        1,
                        2,
                        3,
                        4,
                        5,
                        6,
                        7,
                        8,
                        9,
                        10,
                        11,
                        12,
                        13,
                        14,
                        15,
                        16,
                        17,
                        18,
                        19,
                        20,
                        21,
                        22,
                        23,
                    ],
                    "i_ch_1": (
                        "acq_index_ch_1",
                        [
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                            2.0,
                        ],
                    ),
                    "loop_repetition_ch_1": (
                        "acq_index_ch_1",
                        [
                            0.0,
                            1.0,
                            2.0,
                            3.0,
                            4.0,
                            5.0,
                            6.0,
                            7.0,
                            8.0,
                            9.0,
                            10.0,
                            11.0,
                            12.0,
                            13.0,
                            14.0,
                            15.0,
                            16.0,
                            17.0,
                            18.0,
                            19.0,
                            20.0,
                            21.0,
                            22.0,
                            23.0,
                        ],
                    ),
                    "amp_3_ch_1": (
                        "acq_index_ch_1",
                        [
                            0.0,
                            0.1,
                            0.2,
                            0.3,
                            0.0,
                            0.1,
                            0.2,
                            0.3,
                            0.0,
                            0.1,
                            0.2,
                            0.3,
                            0.0,
                            0.1,
                            0.2,
                            0.3,
                            0.0,
                            0.1,
                            0.2,
                            0.3,
                            0.0,
                            0.1,
                            0.2,
                            0.3,
                        ],
                    ),
                    "amp_1_ch_1": (
                        "acq_index_ch_1",
                        [
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.1,
                            0.1,
                            0.1,
                            0.1,
                            0.1,
                            0.1,
                            0.1,
                            0.1,
                            0.1,
                            0.1,
                            0.1,
                            0.1,
                        ],
                    ),
                    "amp_2_ch_1": (
                        "acq_index_ch_1",
                        [
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.1,
                            0.1,
                            0.1,
                            0.1,
                            0.2,
                            0.2,
                            0.2,
                            0.2,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.1,
                            0.1,
                            0.1,
                            0.1,
                            0.2,
                            0.2,
                            0.2,
                            0.2,
                        ],
                    ),
                },
                dims=["acq_index_ch_1"],
                attrs={"acq_protocol": "SSBIntegrationComplex"},
            ),
        }
    )

    xr.testing.assert_allclose(data, expected_dataset)

    instr_coordinator.remove_component("ic_cluster0")


def test_acquisition_grouping(
    mock_setup_basic_transmon, make_cluster_component, assert_equal_q1asm
):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "ref": "internal",
                "modules": {
                    "3": {"instrument_type": "QRM"},
                },
            }
        },
        "hardware_options": {
            "modulation_frequencies": {
                "q0:res-q0.ro": {
                    "interm_freq": 50e6,
                }
            }
        },
        "connectivity": {
            "graph": [
                ["cluster0.module3.complex_output_0", "q0:res"],
            ]
        },
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon
    ic_cluster0 = make_cluster_component("cluster0")

    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    schedule = TimeableSchedule("Schedule", repetitions=1)

    schedule.add_resource(ClockResource(name="q0.01", freq=50e6))

    with schedule.loop(linspace(0.0, 0.1, 2, DType.AMPLITUDE)) as amp_1:
        schedule.add(
            SSBIntegrationComplex(
                acq_channel="ch_0",
                coords={
                    "amp_1": amp_1,
                    "index": 0,
                },
                bin_mode=BinMode.AVERAGE_APPEND,
                port="q0:res",
                clock="q0.01",
                duration=1e-6,
            )
        )

        schedule.add(
            SSBIntegrationComplex(
                acq_channel="ch_0",
                coords={"index": 1},
                bin_mode=BinMode.AVERAGE_APPEND,
                port="q0:res",
                clock="q0.01",
                duration=1e-6,
            )
        )

        with schedule.loop(linspace(0.0, 0.2, 3, DType.AMPLITUDE)) as amp_2:
            schedule.add(
                SSBIntegrationComplex(
                    acq_channel="ch_0",
                    coords={
                        "amp_1": amp_1,
                        "index": 2,
                    },
                    bin_mode=BinMode.AVERAGE_APPEND,
                    port="q0:res",
                    clock="q0.01",
                    duration=1e-6,
                )
            )

            schedule.add(
                SSBIntegrationComplex(
                    acq_channel="ch_0",
                    coords={
                        "amp_2": amp_2,
                        "index": 3,
                    },
                    bin_mode=BinMode.AVERAGE_APPEND,
                    port="q0:res",
                    clock="q0.01",
                    duration=1e-6,
                )
            )

    schedule.add(
        SSBIntegrationComplex(
            acq_channel="ch_0",
            coords={"index": 4},
            bin_mode=BinMode.AVERAGE_APPEND,
            port="q0:res",
            clock="q0.01",
            duration=1e-6,
        )
    )

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module3"]["sequencers"][
            "seq0"
        ].sequence["program"],
        [
            " set_mrk 0 # set markers to 0 (init)",
            " wait_sync 4 ",
            " upd_param 4 ",
            " move 0,R0 # Initialize acquisition bin_idx for acq. group",
            " move 5,R1 # Initialize acquisition bin_idx for acq. group",
            " wait 4 # latency correction of 4 + 0 ns",
            " move 1,R2 # iterator for loop with label start",
            "start:   ",
            " reset_ph  ",
            " upd_param 4 ",
            " move 0,R4 # Initialize sweep var",
            " move 2,R3 # iterator for loop with label loop10",
            "loop10:   ",
            "   ",
            " acquire 0,R0,4 ",
            " add R0,1,R0 # Increment bin_idx for chch_0",
            "   ",
            " wait 996 # auto generated wait (996 ns)",
            "   ",
            " acquire 0,R1,4 ",
            " add R1,1,R1 # Increment bin_idx for chch_0",
            "   ",
            " wait 996 # auto generated wait (996 ns)",
            " move 0,R6 # Initialize sweep var",
            " move 3,R5 # iterator for loop with label loop23",
            "loop23:   ",
            "   ",
            " acquire 0,R0,4 ",
            " add R0,1,R0 # Increment bin_idx for chch_0",
            "   ",
            " wait 996 # auto generated wait (996 ns)",
            "   ",
            " acquire 0,R1,4 ",
            " add R1,1,R1 # Increment bin_idx for chch_0",
            "   ",
            " wait 996 # auto generated wait (996 ns)",
            " sub R0,1,R0 # Decrement bin_idx for averaging",
            " add R6,214748365,R6 # Update sweep var",
            " loop R5,@loop23 ",
            " add R0,1,R0 # Increment bin_idx for averaging",
            " sub R1,4,R1 # Decrement bin_idx for averaging",
            " add R4,214748365,R4 # Update sweep var",
            " loop R3,@loop10 ",
            " add R1,4,R1 # Increment bin_idx for averaging",
            "   ",
            " acquire 0,R0,4 ",
            " add R0,1,R0 # Increment bin_idx for chch_0",
            "   ",
            " wait 996 # auto generated wait (996 ns)",
            " sub R0,5,R0 # Decrement bin_idx for averaging",
            " sub R1,4,R1 # Decrement bin_idx for averaging",
            " loop R2,@start ",
            " add R0,5,R0 # Increment bin_idx for averaging",
            " add R1,4,R1 # Increment bin_idx for averaging",
            " stop  ",
        ],
    )

    # Setup dummy acquisition data
    ic_cluster0.instrument.delete_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=0,
        acq_index_name="0",
    )
    ic_cluster0.instrument.set_dummy_binned_acquisition_data(
        slot_idx=3,
        sequencer=0,
        acq_index_name="0",
        data=[
            DummyBinnedAcquisitionData(data=(1000 * i, 0), thres=0, avg_cnt=0)
            for i in range((2 + 2 + 1) + (2 + 2))
        ],
    )

    # Upload schedule and run experiment
    instr_coordinator.prepare(compiled_sched)
    instr_coordinator.start()

    data = instr_coordinator.retrieve_acquisition()

    instr_coordinator.stop()

    # Assert intended behaviour
    assert isinstance(data, Dataset)
    expected_dataset = Dataset(
        {
            "ch_0": DataArray(
                [0, 2, 5, 1, 3, 6, 7, 8, 4],
                coords={
                    "acq_index_ch_0": [0, 1, 2, 3, 4, 5, 6, 7, 8],
                    "index": ("acq_index_ch_0", [0, 0, 1, 2, 2, 3, 3, 3, 4]),
                    "loop_repetition_ch_0": ("acq_index_ch_0", [0, 1, 0, 0, 1, 0, 1, 2, np.nan]),
                    "amp_1": (
                        "acq_index_ch_0",
                        [0.0, 0.1, np.nan, 0.0, 0.1, np.nan, np.nan, np.nan, np.nan],
                    ),
                    "amp_2": (
                        "acq_index_ch_0",
                        [np.nan, np.nan, np.nan, np.nan, np.nan, 0.0, 0.1, 0.2, np.nan],
                    ),
                },
                dims=["acq_index_ch_0"],
                attrs={"acq_protocol": "SSBIntegrationComplex"},
            ),
        }
    )

    xr.testing.assert_allclose(data, expected_dataset)

    instr_coordinator.remove_component("ic_cluster0")


def test_acquisition_bin_register_increment_decrement_merging(
    mock_setup_basic_transmon, make_cluster_component, assert_equal_q1asm
):
    hardware_cfg = {
        "config_type": "QbloxHardwareCompilationConfig",
        "hardware_description": {
            "cluster0": {
                "instrument_type": "Cluster",
                "ref": "internal",
                "modules": {
                    "3": {"instrument_type": "QRM"},
                },
            }
        },
        "hardware_options": {
            "modulation_frequencies": {
                "q0:res-q0.ro": {
                    "interm_freq": 50e6,
                }
            }
        },
        "connectivity": {
            "graph": [
                ["cluster0.module3.complex_output_0", "q0:res"],
            ]
        },
    }

    # Setup objects needed for experiment
    mock_setup = mock_setup_basic_transmon
    ic_cluster0 = make_cluster_component("cluster0")

    instr_coordinator = mock_setup["instrument_coordinator"]
    instr_coordinator.add_component(ic_cluster0)

    quantum_device = mock_setup["quantum_device"]
    quantum_device.hardware_config = hardware_cfg

    schedule = TimeableSchedule("Schedule", repetitions=1)

    schedule.add_resource(ClockResource(name="q0.01", freq=50e6))

    schedule.add(
        SSBIntegrationComplex(
            acq_channel="ch_0",
            coords={"index": 0},
            bin_mode=BinMode.AVERAGE_APPEND,
            port="q0:res",
            clock="q0.01",
            duration=1e-6,
        )
    )

    with (
        schedule.loop(linspace(0.0, 0.1, 2, DType.AMPLITUDE)),
        schedule.loop(linspace(0.0, 0.2, 3, DType.AMPLITUDE)) as amp_2,
    ):
        schedule.add(
            SSBIntegrationComplex(
                acq_channel="ch_0",
                coords={
                    "amp_2": amp_2,
                    "index": 1,
                },
                bin_mode=BinMode.AVERAGE_APPEND,
                port="q0:res",
                clock="q0.01",
                duration=1e-6,
            )
        )
        schedule.add(
            SSBIntegrationComplex(
                acq_channel="ch_0",
                coords={
                    "index": 1,
                },
                bin_mode=BinMode.AVERAGE_APPEND,
                port="q0:res",
                clock="q0.01",
                duration=1e-6,
            )
        )

    # Generate compiled schedule
    compiler = SerialCompiler(name="compiler")
    compiled_sched = compiler.compile(
        schedule=schedule, config=quantum_device.generate_compilation_config()
    )

    assert_equal_q1asm(
        compiled_sched.compiled_instructions["cluster0"]["cluster0_module3"]["sequencers"][
            "seq0"
        ].sequence["program"],
        [
            " set_mrk 0 # set markers to 0 (init)",
            " wait_sync 4 ",
            " upd_param 4 ",
            " move 0,R0 # Initialize acquisition bin_idx for acq. group",
            " move 4,R1 # Initialize acquisition bin_idx for acq. group",
            " wait 4 # latency correction of 4 + 0 ns",
            " move 1,R2 # iterator for loop with label start",
            "start:   ",
            " reset_ph  ",
            " upd_param 4 ",
            "   ",
            " acquire 0,R0,4 ",
            " add R0,1,R0 # Increment bin_idx for chch_0",
            "   ",
            " wait 996 # auto generated wait (996 ns)",
            " move 0,R4 # Initialize sweep var",
            " move 2,R3 # iterator for loop with label loop15",
            "loop15:   ",
            " move 0,R6 # Initialize sweep var",
            " move 3,R5 # iterator for loop with label loop18",
            "loop18:   ",
            "   ",
            " acquire 0,R0,4 ",
            " add R0,1,R0 # Increment bin_idx for chch_0",
            "   ",
            " wait 996 # auto generated wait (996 ns)",
            "   ",
            " acquire 0,R1,4 ",
            " add R1,1,R1 # Increment bin_idx for chch_0",
            "   ",
            " wait 996 # auto generated wait (996 ns)",
            " sub R1,1,R1 # Decrement bin_idx for averaging",
            " add R6,214748365,R6 # Update sweep var",
            " loop R5,@loop18 ",
            " sub R0,3,R0 # Decrement bin_idx for averaging",
            " add R4,214748365,R4 # Update sweep var",
            " loop R3,@loop15 ",
            " sub R0,1,R0 # Decrement bin_idx for averaging",
            " loop R2,@start ",
            " add R0,4,R0 # Increment bin_idx for averaging",
            " add R1,1,R1 # Increment bin_idx for averaging",
            " stop  ",
        ],
    )
