# Local data layout

Raw datasets are intentionally excluded from Git.

- `raw/`: immutable downloaded/extracted upstream files.
- `interim/`: temporary conversion artifacts.
- `processed/<dataset>/`: YOLO images, labels, references, manifest, checksums, and summaries.

Never commit dataset archives or generated images without first verifying redistribution rights.
