"""Run the complete Pytest suite once and record observed verification results."""
from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
report = ROOT / "reports" / "generated" / "pytest.xml"
report.parent.mkdir(parents=True, exist_ok=True)
commands = [
    [sys.executable, "scripts/validate_structure.py"],
    [sys.executable, "-m", "compileall", "-q", "backend", "src", "tests", "scripts", "migrations"],
    [sys.executable, "-m", "ruff", "check", "backend", "src", "tests", "scripts"],
    [sys.executable, "-m", "pytest", f"--junitxml={report}"],
]
results = []
for command in commands:
    process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                             encoding="utf-8", errors="replace", check=False)
    output = (process.stdout + "\n" + process.stderr).strip()
    print(output)
    results.append({"command": command, "returncode": process.returncode,
                    "output_tail": output.splitlines()[-12:]})
counts = None
if report.is_file() and results[-1]["returncode"] in (0, 1):
    suites = list(ET.parse(report).getroot().iter("testsuite"))
    totals = {key: sum(int(suite.get(key, "0")) for suite in suites)
              for key in ("tests", "failures", "errors", "skipped")}
    counts = {**totals, "passed": totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]}
summary = {"generated_at": datetime.now(UTC).isoformat(), "pytest": counts,
           "checks": results,
           "scope": "Software tests only; frontend build, Docker runtime and real model evaluation are separate checks."}
(ROOT / "reports" / "validation-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
raise SystemExit(int(any(item["returncode"] for item in results)))
