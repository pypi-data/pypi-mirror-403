from qblox_scheduler.operations import MarkerPulse
from qblox_scheduler.operations.hardware_operations.pulse_library import RFSwitchToggle


def test_init():
    operation = RFSwitchToggle(1, "p", "digital")
    assert operation.duration == 1
    assert operation.name == "RFSwitchToggle"
    assert operation.data["pulse_info"]["t0"] == 0
    assert operation.data["pulse_info"]["port"] == "p"
    assert operation.data["pulse_info"]["clock"] == "digital"
    assert operation.data["pulse_info"]["marker_pulse"] is True
    assert not isinstance(operation, MarkerPulse)


def test_init_clock():
    operation = RFSwitchToggle(1, "p", "clock5")
    assert operation.data["pulse_info"]["clock"] == "clock5"
