"""Stable human-readable ID validation."""

import re
from typing import Dict

ID_PATTERNS: Dict[str, str] = {
    "project": r"[a-z][a-z0-9-]*",
    "scene": r"scene-[0-9]{3}",
    "shot": r"shot-[0-9]{3}",
    "render_plan": r"rp-shot-[0-9]{3}-[0-9]{3}",
    "render_job": r"job-shot-[0-9]{3}-[0-9]{3}",
    "candidate": r"cand-shot-[0-9]{3}-[0-9]{3}",
    "review": r"rev-cand-shot-[0-9]{3}-[0-9]{3}-[0-9]{3}",
    "selection": r"sel-shot-[0-9]{3}-[0-9]{3}",
    "cut": r"cut-[a-z0-9-]+-[0-9]{3}",
    "shot_package": r"pkg-shot-[0-9]{3}-[0-9]{3}",
}


def is_valid_id(kind: str, value: object) -> bool:
    """Return whether *value* uses the stable ID format for *kind*."""
    return isinstance(value, str) and bool(re.fullmatch(ID_PATTERNS[kind], value))
