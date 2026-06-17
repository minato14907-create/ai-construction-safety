import csv
import os
import datetime
from config import Config, VIOLATION_MESSAGES


class AlertManager:
    def __init__(self):
        self.violation_log = Config.VIOLATION_LOG
        self._init_log()

    def _init_log(self):
        if not os.path.exists(self.violation_log):
            with open(self.violation_log, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "violation_type", "message",
                    "confidence", "frame_number"
                ])

    def log_violation(self, violation_type, confidence=1.0, frame_number=0):
        ts = datetime.datetime.now().isoformat()
        msg = VIOLATION_MESSAGES.get(violation_type, {}).get(
            Config.LANGUAGE, violation_type
        )
        with open(self.violation_log, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([ts, violation_type, msg, f"{confidence:.2f}", frame_number])

    def log_violations(self, violations, frame_number=0):
        for v in violations:
            for v_code in v["violations"]:
                self.log_violation(v_code, frame_number=frame_number)

    def get_recent_violations(self, limit=50):
        if not os.path.exists(self.violation_log):
            return []
        with open(self.violation_log, mode="r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        return rows[-limit:]

    @staticmethod
    def get_violation_summary():
        if not os.path.exists(Config.VIOLATION_LOG):
            return {}
        summary = {}
        with open(Config.VIOLATION_LOG, mode="r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                vt = row["violation_type"]
                summary[vt] = summary.get(vt, 0) + 1
        return summary
