from __future__ import annotations

from importlib.resources import files
from pathlib import Path


PACKAGE_ROOT = files("fivegnr_phy_stl")


def packaged_config_root() -> Path:
    return Path(str(PACKAGE_ROOT.joinpath("configs")))


def resolve_config_path(path_like: str | Path) -> Path:
    candidate = Path(path_like)
    search_roots = [
        Path.cwd(),
        Path(__file__).resolve().parent.parent,
    ]

    if candidate.is_absolute() and candidate.exists():
        return candidate

    for root in search_roots:
        resolved = (root / candidate).resolve()
        if resolved.exists():
            return resolved

    packaged_root = packaged_config_root()
    relative_candidate = Path(*candidate.parts[1:]) if candidate.parts and candidate.parts[0] == "configs" else candidate
    packaged_candidate = (packaged_root / relative_candidate).resolve()
    if packaged_candidate.exists():
        return packaged_candidate

    raise FileNotFoundError(f"Unable to resolve configuration path: {path_like}")
