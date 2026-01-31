import pytest
from attendify.parser import parse_timetable_csv, parse_attendance_csv
from attendify.exceptions import InvalidCSVError


def test_valid_timetable(tmp_path):
    file = tmp_path / "t.csv"
    file.write_text("subject,periods\nMaths,2\nMaths,1\n")
    assert parse_timetable_csv(file) == {"maths": 3}


def test_invalid_attendance(tmp_path):
    file = tmp_path / "a.csv"
    file.write_text("subject,attended,total\nMaths,5,3\n")
    with pytest.raises(InvalidCSVError):
        parse_attendance_csv(file)
