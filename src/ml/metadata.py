from __future__ import annotations

import hashlib
import json
import platform
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def package_version(name: str) -> str | None:
    try:
        from importlib.metadata import version
        return version(name)
    except PackageNotFoundError:
        return None


def build_run_metadata(*, mode: str, config: dict[str, Any], dataset: dict[str, Any],
                       metrics: dict[str, float] | None = None, weights: Path | None = None) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "created_at": datetime.now(UTC).isoformat(),
        "mode": mode,
        "config": config,
        "dataset": dataset,
        "metrics": metrics or {},
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "ultralytics": package_version("ultralytics"),
            "torch": package_version("torch"),
        },
    }
    if weights and weights.is_file():
        digest = sha256_file(weights)
        metadata["weights"] = {"path": str(weights.resolve()), "sha256": digest,
                               "model_version": f"sha256:{digest[:12]}"}
    return metadata


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_registry(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
