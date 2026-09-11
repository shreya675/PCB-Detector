from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

SEVERITIES = ("minor", "major", "critical")
STATUSES = ("PASS", "PASS WITH WARNING", "FAIL")


@dataclass(frozen=True)
class SeverityPolicy:
    defect_severity: dict[str, str]
    default_severity: str = "minor"
    fail_on_critical: bool = True
    fail_major_count: int = 2
    warning_on_major: bool = True
    warning_minor_count: int = 1

    def validate(self) -> None:
        if self.default_severity not in SEVERITIES:
            raise ValueError(f"Invalid default severity: {self.default_severity}")
        if self.fail_major_count < 1 or self.warning_minor_count < 1:
            raise ValueError("Severity count thresholds must be positive")
        invalid = {key: value for key, value in self.defect_severity.items() if value not in SEVERITIES}
        if invalid:
            raise ValueError(f"Invalid defect severities: {invalid}")

    @classmethod
    def from_yaml(cls, path: Path) -> SeverityPolicy:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Severity policy must be a YAML mapping")  # noqa: TRY004 - invalid configuration file value
        policy = cls(**raw)
        policy.validate()
        return policy

    def severity_for(self, defect_type: str) -> str:
        return self.defect_severity.get(defect_type, self.default_severity)

    def decide(self, severities: list[str]) -> tuple[str, dict[str, int]]:
        invalid = [value for value in severities if value not in SEVERITIES]
        if invalid:
            raise ValueError(f"Unknown severities: {invalid}")
        counts = {severity: severities.count(severity) for severity in SEVERITIES}
        if self.fail_on_critical and counts["critical"] > 0:
            return "FAIL", counts
        if counts["major"] >= self.fail_major_count:
            return "FAIL", counts
        if counts["critical"] > 0 or (self.warning_on_major and counts["major"] > 0) or counts["minor"] >= self.warning_minor_count:
            return "PASS WITH WARNING", counts
        return "PASS", counts
