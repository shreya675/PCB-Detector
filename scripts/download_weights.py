"""Fetch the model weights at container start when they are not baked into the image.

Reads MODEL_PATH (destination) and MODEL_URL (source). Skips the download when the file
already exists. If models/model_card.json lists a sha256 for the weights, the download is
verified against it so a wrong or truncated file never reaches the API.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def main() -> int:
    destination = Path(os.environ.get("MODEL_PATH", "models/weights/yolo11m_official_v4.pt"))
    url = os.environ.get("MODEL_URL", "").strip()
    if destination.is_file():
        print(f"weights already present: {destination}")
        return 0
    if not url:
        print("MODEL_URL is not set and no weights file exists; the API will start without a model.")
        return 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(".part")
    print(f"downloading {url} -> {destination}")
    digest = hashlib.sha256()
    for attempt in range(1, 6):
        try:
            with urllib.request.urlopen(url, timeout=120) as response, partial.open("wb") as handle:
                while chunk := response.read(1024 * 1024):
                    handle.write(chunk)
                    digest.update(chunk)
            break
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 502, 503, 504) or attempt == 5:
                raise
            wait = 5 * attempt
            print(f"attempt {attempt} got HTTP {exc.code}; retrying in {wait}s")
            digest = hashlib.sha256()
            time.sleep(wait)
    expected = _expected_sha256(Path(os.environ.get("MODEL_CARD_PATH", "models/model_card.json")))
    if expected and digest.hexdigest() != expected:
        partial.unlink(missing_ok=True)
        print(f"checksum mismatch: got {digest.hexdigest()[:12]}, model card expects {expected[:12]}", file=sys.stderr)
        return 1
    partial.replace(destination)
    print(f"saved {destination} ({destination.stat().st_size / 1e6:.1f} MB, sha256 {digest.hexdigest()[:12]})")
    return 0


def _expected_sha256(card_path: Path) -> str | None:
    try:
        return json.loads(card_path.read_text(encoding="utf-8"))["weights"]["sha256"]
    except (OSError, ValueError, KeyError, TypeError):
        return None


if __name__ == "__main__":
    sys.exit(main())
