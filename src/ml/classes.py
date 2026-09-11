"""Resolve checkpoint label metadata without assuming training class order."""
from src.datasets.schema import canonical_class_name


def resolve_model_classes(names) -> dict[int, str]:
    if isinstance(names, (list, tuple)):
        names = dict(enumerate(names))
    if not isinstance(names, dict) or not names:
        raise ValueError("Checkpoint must declare PCB detection class names")
    resolved = {int(key): canonical_class_name(str(value)) for key, value in names.items()}
    if set(resolved) != set(range(len(resolved))):
        raise ValueError("Checkpoint class IDs must be contiguous from zero")
    if len(set(resolved.values())) != len(resolved):
        raise ValueError("Checkpoint class names must be unique")
    return resolved
