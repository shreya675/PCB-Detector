# Dataset preparation and provenance

## Canonical taxonomy

| ID | Canonical name | DeepPCB source label | HRIPCB aliases |
|---:|---|---|---|
| 0 | `open_circuit` | 1 / open | open circuit |
| 1 | `short_circuit` | 2 / short | short |
| 2 | `spur` | 4 / spur | spur |
| 3 | `spurious_copper` | 5 / copper | spurious copper |
| 4 | `mouse_bite` | 3 / mousebite | mouse bite |
| 5 | `missing_hole` | Not supplied | missing hole |
| 6 | `pin_hole` | 6 / pin-hole | Not treated as a missing hole |

The mapping is explicit because the upstream DeepPCB class order differs from this project's canonical order.

## DeepPCB

The official repository documents 1,500 aligned 640×640 tested/template pairs, six defect classes, comma-separated `x1,y1,x2,y2,type` labels, and a 1,000-image training split with the remainder used for testing. It also states that some defects were manually augmented. The upstream repository includes an MIT code license, while its README and the SJTU dataset page restrict dataset use to research/non-commercial use. This project therefore treats the **dataset** under the more restrictive research/non-commercial terms.

```bash
python scripts/download_deeppcb.py --accept-research-only
unzip data/raw/deeppcb.zip -d data/raw/deeppcb
python -m src.datasets.cli deeppcb --source data/raw/deeppcb --output data/processed/deeppcb
python -m src.datasets.cli validate --dataset data/processed/deeppcb
```

## HRIPCB

The publication describes 1,386 synthesized colour images across six classes, including upright and rotated boards, Pascal VOC XML bounding boxes, and ten templates. Because mirrors have inconsistent packaging and licensing metadata, obtain HRIPCB from the publication's linked project page or another source whose terms you have reviewed, record the URL/version locally, and then run:

```bash
python -m src.datasets.cli hripcb --source data/raw/hripcb --output data/processed/hripcb
python -m src.datasets.cli validate --dataset data/processed/hripcb
```

## Reproducibility and leakage controls

- Raw files remain immutable and excluded from Git.
- Every converted image receives a SHA-256 digest in `manifest.jsonl`.
- Bounding boxes are validated before YOLO normalization.
- Missing/corrupt images, unsupported classes, incomplete DeepPCB pairs, duplicate IDs, and invalid boxes fail loudly.
- Deterministic SHA-256 group splitting keeps samples sharing a board-group key in the same split.
- `summary.json` and `summary.csv` contain observed counts only; no model metrics are generated.
- For a formal DeepPCB benchmark, preserve and document the official upstream train/test list instead of comparing results against a newly randomized split.

## Attribution

- Tang et al., *Online PCB Defect Detector on a New PCB Defect Dataset*, arXiv:1902.06197.
- Huang et al., *HRIPCB: a challenging dataset for PCB defects detection and classification*, The Journal of Engineering, 2020.

The converter supports sibling `<board>_not` annotation folders and whitespace or comma delimiters. DeepPCB label 6 is preserved as `pin_hole`, following the [upstream annotation specification](https://github.com/tangsanli5201/DeepPCB#image-annotation). Regenerate old converted labels: the former mapping incorrectly conflated pin holes with missing holes. Grouped splits are custom research splits, not the official benchmark.
