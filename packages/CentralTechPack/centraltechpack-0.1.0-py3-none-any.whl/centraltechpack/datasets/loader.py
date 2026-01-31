from __future__ import annotations

from importlib.resources import files
from pathlib import Path
import csv
from typing import List, Dict, Any, Union

from .registry import REGISTRY


def list_datasets() -> List[Dict[str, str]]:
    return [
        {"name": info.name, "description": info.description, "path": info.relpath}
        for info in REGISTRY.values()
    ]

def _resource_path(relpath: str) -> Path:
    # Works even when installed from wheel
    root = files("centraltechpack")
    return Path(root.joinpath(relpath))

def load_dataset(name: str) -> List[Dict[str, Any]]:
    name = name.strip().lower()
    if name not in REGISTRY:
        raise KeyError(f"Unknown dataset '{name}'. Available: {sorted(REGISTRY.keys())}")

    p = _resource_path(REGISTRY[name].relpath)
    if not p.exists():
        raise FileNotFoundError(f"Dataset file missing in package: {p}")

    with p.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)

def export_dataset(name: str, out: Union[str, Path]) -> Path:
    name = name.strip().lower()
    if name not in REGISTRY:
        raise KeyError(f"Unknown dataset '{name}'. Available: {sorted(REGISTRY.keys())}")

    src = _resource_path(REGISTRY[name].relpath)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(src.read_bytes())
    return out


