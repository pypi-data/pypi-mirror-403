import csv
from pathlib import Path
from collections import defaultdict
from .exceptions import InvalidCSVError


def _validate_file(path: str):
    file = Path(path)
    if not file.exists():
        raise InvalidCSVError("CSV file not found")
    if file.suffix.lower() != ".csv":
        raise InvalidCSVError("Only CSV files are allowed")


def parse_timetable_csv(path: str) -> dict[str, int]:
    _validate_file(path)
    subjects = defaultdict(int)

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if "subject" not in reader.fieldnames or "periods" not in reader.fieldnames:
            raise InvalidCSVError("Timetable CSV must have subject, periods")

        for row in reader:
            subject = row["subject"].strip().lower()
            periods = int(row["periods"])

            if periods <= 0:
                raise InvalidCSVError("Periods must be positive")

            subjects[subject] += periods

    if not subjects:
        raise InvalidCSVError("Timetable CSV is empty")

    return dict(subjects)


def parse_attendance_csv(path: str) -> dict[str, tuple[int, int]]:
    _validate_file(path)
    records = {}

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if not {"subject", "attended", "total"}.issubset(reader.fieldnames):
            raise InvalidCSVError("Attendance CSV missing columns")

        for row in reader:
            subject = row["subject"].strip().lower()
            attended = int(row["attended"])
            total = int(row["total"])

            if attended < 0 or total < 0:
                raise InvalidCSVError("Negative attendance not allowed")

            if attended > total:
                raise InvalidCSVError("Attended cannot exceed total")

            records[subject] = (attended, total)

    if not records:
        raise InvalidCSVError("Attendance CSV is empty")

    return records
