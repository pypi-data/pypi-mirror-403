from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Dict, List, Union
from .registry import NOTEBOOKS

def list_notebooks() -> List[Dict[str, str]]:
    return [
        {"name": info.name, "description": info.description, "path": info.relpath}
        for info in NOTEBOOKS.values()
    ]

def _resource_path(relpath: str) -> Path:
    root = files("centraltechpack")
    return Path(root.joinpath(relpath))

def export_notebook(name: str, out: Union[str, Path]) -> Path:
    name = name.strip().lower()
    if name not in NOTEBOOKS:
        raise KeyError(f"Unknown notebook '{name}'. Available: {sorted(NOTEBOOKS.keys())}")

    src = _resource_path(NOTEBOOKS[name].relpath)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(src.read_bytes())
    return out
