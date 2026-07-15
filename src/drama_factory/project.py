"""Project discovery and JSON entity loading."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .errors import InvalidMetadataError, ProjectNotFoundError

MANIFEST_NAME = "drama-factory.project.json"


@dataclass
class ProjectIndex:
    """Raw file-based metadata collected for a single creative project."""

    root: Path
    manifest_path: Path
    manifest: Dict[str, Any]
    entities: Dict[str, Dict[str, Dict[str, Any]]] = field(default_factory=dict)
    files: Dict[str, Dict[str, Path]] = field(default_factory=dict)
    load_errors: List[str] = field(default_factory=list)

    def count(self, kind: str) -> int:
        return len(self.entities.get(kind, {}))


def discover_project(path: Optional[str]) -> Path:
    """Find a manifest from an explicit file, directory, or current directory."""
    start = Path(path or Path.cwd()).expanduser()
    if start.is_file():
        if start.name == MANIFEST_NAME:
            return start.resolve()
        raise ProjectNotFoundError("project file must be named drama-factory.project.json")
    start = start.resolve()
    for directory in (start, *start.parents):
        candidate = directory / MANIFEST_NAME
        if candidate.is_file():
            return candidate
    raise ProjectNotFoundError("no drama-factory.project.json found from %s upward" % start)


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidMetadataError("%s: unreadable JSON: %s" % (path, exc)) from exc
    if not isinstance(value, dict):
        raise InvalidMetadataError("%s: root: expected a JSON object" % path)
    return value


def load_project(path: Optional[str]) -> ProjectIndex:
    """Discover a project, read its manifest, and scan configured metadata areas."""
    manifest_path = discover_project(path)
    manifest = _read_json(manifest_path)
    index = ProjectIndex(root=manifest_path.parent.resolve(), manifest_path=manifest_path, manifest=manifest)
    paths = manifest.get("paths", {})
    if not isinstance(paths, dict):
        index.load_errors.append("%s: paths: expected an object" % manifest_path)
        return index
    for logical_name, relative in paths.items():
        if not isinstance(relative, str):
            index.load_errors.append("%s: paths.%s: expected a string" % (manifest_path, logical_name))
            continue
        directory = index.root / relative
        if not directory.is_dir():
            continue
        for file_path in directory.rglob("*.json"):
            if file_path == manifest_path:
                continue
            try:
                entity = _read_json(file_path)
            except InvalidMetadataError as exc:
                index.load_errors.append(str(exc))
                continue
            kind = entity.get("entity_type")
            entity_id = _entity_id(entity)
            if not isinstance(kind, str) or not entity_id:
                index.load_errors.append("%s: entity_type: expected known entity metadata" % file_path)
                continue
            bucket = index.entities.setdefault(kind, {})
            file_bucket = index.files.setdefault(kind, {})
            if entity_id in bucket:
                index.load_errors.append("%s: duplicate %s ID %s" % (file_path, kind, entity_id))
                continue
            bucket[entity_id] = entity
            file_bucket[entity_id] = file_path
    return index


def _entity_id(entity: Dict[str, Any]) -> Optional[str]:
    keys = {"shot_contract": "shot_id", "render_plan": "render_plan_id", "render_job": "render_job_id",
            "candidate": "candidate_id", "review": "review_id", "selection": "selection_id",
            "cut_manifest": "cut_id", "shot_package": "shot_package_id"}
    key = keys.get(entity.get("entity_type"))
    value = entity.get(key) if key else None
    return value if isinstance(value, str) else None
