from .parser import parse_timetable_csv


class Timetable:
    def __init__(self, subjects: dict[str, int]):
        self.subjects = subjects

    @classmethod
    def from_csv(cls, path: str):
        return cls(parse_timetable_csv(path))

    def has_subject(self, subject: str) -> bool:
        return subject.lower() in self.subjects
