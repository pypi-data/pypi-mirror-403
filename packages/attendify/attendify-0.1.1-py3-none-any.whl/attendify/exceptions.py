class AttendifyError(Exception):
    pass


class InvalidCSVError(AttendifyError):
    pass


class SubjectNotFoundError(AttendifyError):
    pass
