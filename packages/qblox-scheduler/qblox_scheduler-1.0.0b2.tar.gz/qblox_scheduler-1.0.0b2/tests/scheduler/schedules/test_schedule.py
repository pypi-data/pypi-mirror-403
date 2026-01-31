# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch

"""Most TimeableSchedule tests are in the legacy test file `test_types.py`"""

from qblox_scheduler.schedules.schedule import TimeableSchedule


def test_init_schedule_defaults():
    schedule = TimeableSchedule()
    assert schedule.repetitions == 1
    assert schedule.name == "schedule"


def test_two_schedules_with_same_name():
    sched1 = TimeableSchedule()
    sched2 = TimeableSchedule("schedule")
    assert sched1 == sched2
    assert sched1 is not sched2


def test_two_schedules_with_different_names_are_not_equal():
    assert TimeableSchedule("x") != TimeableSchedule("y")
