from __future__ import annotations

import argparse
import hashlib
import shutil
import urllib.request
from pathlib import Path

OFFICIAL_URL = "https://github.com/tangsanli5201/DeepPCB/archive/refs/heads/master.zip"


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the upstream DeepPCB repository archive")
    parser.add_argument("--output", type=Path, default=Path("data/raw/deeppcb.zip"))
    parser.add_argument("--accept-research-only", action="store_true",
                        help="Confirm that you accept the dataset's research/non-commercial terms")
    args = parser.parse_args()
    if not args.accept_research_only:
        parser.error("Read docs/datasets.md, then pass --accept-research-only to continue")
    if args.output.exists():
        parser.error("Output already exists; use another --output path to preserve the existing archive")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    partial = args.output.with_suffix(args.output.suffix + ".part")
    with urllib.request.urlopen(OFFICIAL_URL, timeout=60) as response, partial.open("wb") as target:
        shutil.copyfileobj(response, target)
    with partial.open("rb") as downloaded:
        digest = hashlib.file_digest(downloaded, "sha256").hexdigest()
    partial.replace(args.output)
    print(f"Source: {OFFICIAL_URL}\nSHA-256: {digest}")
    print(f"Downloaded {args.output}. Verify provenance and retain the upstream terms.")


if __name__ == "__main__":
    main()
