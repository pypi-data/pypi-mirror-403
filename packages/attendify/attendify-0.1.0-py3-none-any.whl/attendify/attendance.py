from .parser import parse_attendance_csv
from .exceptions import SubjectNotFoundError
from .rules import AttendanceRules
from .timetable import Timetable


class Attendance:
    def __init__(self, timetable: Timetable, rules: AttendanceRules):
        self.timetable = timetable
        self.rules = rules
        self.records: dict[str, tuple[int, int]] = {}

    @classmethod
    def from_csv(
        cls,
        path: str,
        timetable: Timetable,
        rules: AttendanceRules,
    ) -> "Attendance":
        """
        Create Attendance object from attendance CSV
        """
        obj = cls(timetable, rules)
        obj.records = parse_attendance_csv(path)

        # Validate subjects against timetable
        for subject in obj.records:
            if not timetable.has_subject(subject):
                raise SubjectNotFoundError(
                    f"Subject '{subject}' not found in timetable"
                )

        return obj

    def percentage(self, subject: str) -> float:
        """
        Return attendance percentage for a subject
        """
        attended, total = self.records[subject]
        return round((attended / total) * 100, 2)

    def classes_needed(
        self,
        subject: str,
        target: float | None = None,
    ) -> int:
        """
        Calculate number of additional classes needed
        to reach target attendance percentage
        """
        target = target or self.rules.min_percentage
        attended, total = self.records[subject]

        needed = 0
        while ((attended + needed) / (total + needed)) * 100 < target:
            needed += 1

        return needed

    def summary(self) -> dict[str, dict]:
        """
        Return summary for all subjects:
        {
            "maths": {
                "percentage": 68.4,
                "status": "CRITICAL",
                "classes_needed": 5
            }
        }
        """
        result: dict[str, dict] = {}

        for subject in self.records:
            percent = self.percentage(subject)

            if percent >= self.rules.min_percentage:
                status = "SAFE"
                needed = 0
            else:
                needed = self.classes_needed(subject)

                if needed <= self.rules.risk_threshold:
                    status = "AT_RISK"
                elif needed <= self.rules.critical_threshold:
                    status = "CRITICAL"
                else:
                    status = "FAILING"

            result[subject] = {
                "percentage": percent,
                "status": status,
                "classes_needed": needed,
            }

        return result
