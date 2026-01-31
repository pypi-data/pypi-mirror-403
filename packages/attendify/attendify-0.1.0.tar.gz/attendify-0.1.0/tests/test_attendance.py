from attendify.attendance import Attendance
from attendify.rules import AttendanceRules
from attendify.timetable import Timetable


def test_summary():
    timetable = Timetable({"maths": 30})
    rules = AttendanceRules(75)

    attendance = Attendance(timetable, rules)
    attendance.records = {"maths": (20, 30)}  # needs 10 classes

    summary = attendance.summary()

    assert summary["maths"]["status"] == "FAILING"
    assert summary["maths"]["classes_needed"] == 10
