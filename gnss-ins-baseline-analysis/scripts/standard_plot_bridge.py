"""Resolve the shared plotting implementation from python-publication-figures."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from types import ModuleType


def load_figure_core() -> ModuleType:
    candidates: list[Path] = []
    override = os.environ.get("PYTHON_PUBLICATION_FIGURES_HOME")
    if override:
        candidates.append(Path(override))
    candidates.append(Path.home() / ".codex" / "skills" / "python-publication-figures")
    candidates.append(
        Path(__file__).resolve().parents[2] / "python-publication-figures"
    )

    for skill_root in candidates:
        scripts_dir = skill_root / "scripts"
        if not (scripts_dir / "figure_core.py").is_file():
            continue
        sys.path.insert(0, str(scripts_dir))
        try:
            return importlib.import_module("figure_core")
        finally:
            sys.path.pop(0)
    raise RuntimeError(
        "python-publication-figures/scripts/figure_core.py was not found. "
        "Install that skill or set PYTHON_PUBLICATION_FIGURES_HOME."
    )
