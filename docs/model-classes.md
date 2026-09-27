# Detection classes and evidence types

## YOLO output taxonomy

The output taxonomy keeps missing holes and pin holes separate:

| ID | Model class | Display name |
|---:|---|---|
| 0 | `open_circuit` | Open circuit |
| 1 | `short_circuit` | Short circuit |
| 2 | `spur` | Spur |
| 3 | `spurious_copper` | Spurious copper |
| 4 | `mouse_bite` | Mouse bite |
| 5 | `missing_hole` | Missing hole |
| 6 | `pin_hole` | Pin hole (DeepPCB) |

The served checkpoint (`yolo11m_official_v4.pt`) is trained on DeepPCB, which has no `missing_hole` examples, so that class is declared but never predicted. Per-class results are in `models/model_card.json`.

## Rule-based reference evidence

Reference analysis can additionally emit six evidence types:

- `missing_component`
- `misaligned_component`
- `unexpected_component`
- `broken_trace_candidate`
- `bridge_candidate`
- `spurious_copper_candidate`

These are not YOLO classes and do not increase the model class count. Their confidence is null and displayed as **Heuristic**. Polarity error, tombstoning, cold solder, and confirmed solder bridge are not supported model predictions in this version.

Checkpoint class names are validated and resolved from checkpoint metadata, including reordered classes. Generic COCO checkpoints are rejected.
