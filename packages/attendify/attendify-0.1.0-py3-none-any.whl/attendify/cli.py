import argparse
import json
import csv

from attendify.timetable import Timetable
from attendify.attendance import Attendance
from attendify.rules import AttendanceRules


def main():
    parser = argparse.ArgumentParser(description="Attendance Risk Checker")

    parser.add_argument("attendance_csv")
    parser.add_argument("timetable_csv")

    parser.add_argument("--min", type=float, default=75)
    parser.add_argument("--only-risk", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--export-csv", metavar="FILE")

    args = parser.parse_args()

    rules = AttendanceRules(min_percentage=args.min)
    timetable = Timetable.from_csv(args.timetable_csv)
    attendance = Attendance.from_csv(
        args.attendance_csv, timetable, rules
    )

    summary = attendance.summary()

    # Filter risky subjects if needed
    if args.only_risk:
        summary = {
            s: d for s, d in summary.items()
            if d["status"] != "SAFE"
        }

    # JSON output
    if args.json:
        print(json.dumps(summary, indent=2))
        return

    # Normal table output
    print("\nSUBJECT     ATT%    STATUS        NEEDED")
    print("----------------------------------------")

    for subject, data in summary.items():
        print(
            f"{subject.upper():<12}"
            f"{data['percentage']:<7}"
            f"{data['status']:<13}"
            f"{data['classes_needed']}"
        )

    # Export CSV if requested
    if args.export_csv:
        with open(args.export_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["subject", "percentage", "status", "classes_needed"]
            )

            for subject, data in summary.items():
                writer.writerow([
                    subject,
                    data["percentage"],
                    data["status"],
                    data["classes_needed"],
                ])

        print(f"\nReport exported to {args.export_csv}")


if __name__ == "__main__":
    main()
