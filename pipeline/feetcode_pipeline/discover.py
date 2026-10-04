"""Find problem modules and load their PROBLEM specs."""
from __future__ import annotations

import hashlib
import importlib
import pathlib
import sys
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROBLEMS_DIR = ROOT / "problems"
ENGINE_DIR = ROOT / "engine"

for p in (str(ENGINE_DIR), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)


@dataclass
class Source:
    module: str          # problems.two_pointers.trapping_rain_water
    path: pathlib.Path   # file on disk
    digest: str          # sha256 of the module source (cache key component)

    @property
    def rel(self) -> str:
        return self.path.relative_to(ROOT).as_posix()


def discover(only: list[str] | None = None) -> list[Source]:
    out = []
    for path in sorted(PROBLEMS_DIR.glob("*/*.py")):
        if path.name.startswith("_"):
            continue
        module = ".".join(path.relative_to(ROOT).with_suffix("").parts)
        if only and not any(o == module or o.replace("-", "_") in path.stem for o in only):
            continue
        out.append(Source(module, path, hashlib.sha256(path.read_bytes()).hexdigest()))
    return out


def load(source: Source):
    mod = importlib.import_module(source.module)
    return mod.PROBLEM


def engine_digest() -> str:
    """Hash of the engine sources: artifacts depend on the engine as well as the content."""
    h = hashlib.sha256()
    for path in sorted((ENGINE_DIR / "feetcode").glob("*.py")):
        h.update(path.name.encode())
        h.update(path.read_bytes())
    return h.hexdigest()
