class AttendanceRules:
    def __init__(
        self,
        min_percentage: float = 75.0,
        risk_threshold: int = 3,
        critical_threshold: int = 7,
    ):
        if not 0 < min_percentage <= 100:
            raise ValueError("min_percentage must be between 0 and 100")

        self.min_percentage = min_percentage
        self.risk_threshold = risk_threshold
        self.critical_threshold = critical_threshold
