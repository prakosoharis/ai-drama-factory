"""Structure and file validation for V2.1-A metadata."""

import hashlib
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .ids import is_valid_id
from .project import ProjectIndex
from .time import parse_utc

SCHEMA_VERSION = "0.1"
LEVELS = {"structure", "files"}
ENTITY_SPECS = {
    "shot_contract": ("shot", ["schema_version", "shot_id", "scene_id", "title", "dramatic_intention", "duration_target", "characters", "environment", "start_state", "end_state", "primary_action", "camera", "lighting", "dialogue_dependency", "audio_dependency", "continuity_dependencies", "references", "known_risks", "acceptance_criteria", "status", "revision"]),
    "render_plan": ("render_plan", ["schema_version", "render_plan_id", "shot_id", "renderer", "model", "model_version", "task", "compiler_version", "prompt_artifact", "negative_prompt_artifact", "references", "audio_conditioning", "duration", "resolution", "fps", "seed_policy", "candidate_budget", "handles", "model_specific", "estimated_cost", "created_at"]),
    "render_job": ("render_job", ["schema_version", "render_job_id", "render_plan_id", "candidate_id", "status", "worker", "provider", "started_at", "completed_at", "exit_code", "runtime_seconds", "estimated_cost", "actual_cost", "log_path", "error", "retry_of"]),
    "candidate": ("candidate", ["schema_version", "candidate_id", "shot_id", "render_plan_id", "render_job_id", "version", "status", "video_path", "metadata_path", "checksum", "duration", "fps", "resolution", "created_at", "provenance", "qc_summary"]),
    "review": ("review", ["schema_version", "review_id", "candidate_id", "reviewer", "reviewer_type", "created_at", "decision", "summary", "findings"]),
    "selection": ("selection", ["schema_version", "selection_id", "shot_id", "candidate_id", "selected_by", "selected_at", "purpose", "notes", "supersedes_selection_id"]),
    "cut_manifest": ("cut", ["schema_version", "cut_id", "project_id", "cut_name", "cut_version", "status", "timeline", "audio", "created_at", "created_by", "parent_cut_id"]),
    "shot_package": ("shot_package", ["schema_version", "shot_package_id", "shot_id", "candidate_id", "picture_status", "audio_status", "video_source", "proxy", "handles", "dialogue_stem", "foley_stem", "local_sfx_stem", "provenance", "published_at"]),
}
ENUMS = {"render_job": {"status": {"QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"}},
         "candidate": {"status": {"REVIEW_REQUIRED", "PICTURE_APPROVED", "REJECTED", "SUPERSEDED"}},
         "review": {"decision": {"APPROVE_PICTURE", "REQUEST_REVISION", "REJECT", "COMMENT_ONLY"}},
         "selection": {"purpose": {"ROUGH_CUT", "FINAL_CUT", "BENCHMARK", "PREVIEW"}},
         "cut_manifest": {"status": {"DRAFT", "ROUGH_CUT", "REVIEW", "PICTURE_LOCKED", "DELIVERY_APPROVED"}}}
TIMESTAMPS = {"render_plan": ["created_at"], "render_job": ["started_at", "completed_at"], "candidate": ["created_at"], "review": ["created_at"], "selection": ["selected_at"], "cut_manifest": ["created_at"], "shot_package": ["published_at"]}


@dataclass
class Finding:
    severity: str
    file: str
    field: str
    invalid_value: Any
    expected: str
    suggestion: str


def validate(index: ProjectIndex, level: str = "structure") -> List[Finding]:
    """Validate all indexed metadata and entity references at a requested level."""
    findings: List[Finding] = []
    if level not in LEVELS:
        return [_finding(index.manifest_path, "level", level, "structure or files", "use --level structure or --level files")]
    findings.extend(_validate_manifest(index))
    for message in index.load_errors:
        findings.append(_finding(index.manifest_path, "index", message, "readable unique JSON entities", "fix unreadable JSON or duplicate ID"))
    for kind, records in index.entities.items():
        for entity_id, entity in records.items():
            path = index.files[kind][entity_id]
            findings.extend(_validate_entity(kind, entity, path, index.root))
    findings.extend(_validate_references(index))
    if level == "files":
        findings.extend(_validate_files(index))
    return findings


def _finding(path: Path, field: str, value: Any, expected: str, suggestion: str, severity: str = "error") -> Finding:
    return Finding(severity, str(path), field, value, expected, suggestion)


def _validate_manifest(index: ProjectIndex) -> List[Finding]:
    data, path, out = index.manifest, index.manifest_path, []
    for field in ["schema_version", "project_id", "project_name", "engine_version", "project_root", "paths", "default_renderer", "default_audio_policy", "created_at", "updated_at"]:
        if field not in data:
            out.append(_finding(path, field, None, "required field", "add the field"))
    if data.get("schema_version") != SCHEMA_VERSION:
        out.append(_finding(path, "schema_version", data.get("schema_version"), '"0.1"', "use supported schema version"))
    if "project_id" in data and not is_valid_id("project", data["project_id"]):
        out.append(_finding(path, "project_id", data["project_id"], "lowercase human-readable ID", "use e.g. demo-drama"))
    for field in ("created_at", "updated_at"):
        if field in data:
            out.extend(_timestamp(path, field, data[field]))
    out.extend(_safe_path(path, "project_root", data.get("project_root"), index.root, allow_dot=True))
    if not isinstance(data.get("paths"), dict):
        out.append(_finding(path, "paths", data.get("paths"), "object of relative paths", "provide configured metadata paths"))
    else:
        for key, value in data["paths"].items():
            out.extend(_safe_path(path, "paths.%s" % key, value, index.root))
    return out


def _validate_entity(kind: str, data: Dict[str, Any], path: Path, root: Path) -> List[Finding]:
    out: List[Finding] = []
    if kind not in ENTITY_SPECS:
        return [_finding(path, "entity_type", kind, "supported entity type", "use a V2.1-A entity type")]
    id_kind, required = ENTITY_SPECS[kind]
    for field in required:
        if field not in data:
            out.append(_finding(path, field, None, "required field", "add the field; use null if explicitly unavailable"))
    if data.get("schema_version") != SCHEMA_VERSION:
        out.append(_finding(path, "schema_version", data.get("schema_version"), '"0.1"', "use supported schema version"))
    id_field = {"shot_contract": "shot_id", "cut_manifest": "cut_id"}.get(kind, "%s_id" % kind)
    if id_field in data and not is_valid_id(id_kind, data[id_field]):
        out.append(_finding(path, id_field, data[id_field], "valid %s ID" % id_kind, "use documented stable ID format"))
    for field in TIMESTAMPS.get(kind, []):
        if data.get(field) is not None:
            out.extend(_timestamp(path, field, data[field]))
    for field, values in ENUMS.get(kind, {}).items():
        if field in data and data[field] not in values:
            out.append(_finding(path, field, data[field], "one of %s" % sorted(values), "use a documented enum value"))
    for field in _path_fields(kind, data):
        out.extend(_safe_path(path, field, data.get(field), root))
    return out


def _timestamp(path: Path, field: str, value: Any) -> List[Finding]:
    try:
        parse_utc(value)
    except ValueError as exc:
        return [_finding(path, field, value, "timezone-aware ISO 8601 UTC", "use e.g. 2026-07-15T18:30:00Z: %s" % exc)]
    return []


def _path_fields(kind: str, data: Dict[str, Any]) -> Iterable[str]:
    fields = {"render_plan": ["prompt_artifact", "negative_prompt_artifact"], "render_job": ["log_path"],
              "candidate": ["video_path", "proxy_path", "thumbnail_path", "metadata_path"],
              "shot_package": ["video_source", "proxy", "dialogue_stem", "foley_stem", "local_sfx_stem"]}
    return [field for field in fields.get(kind, []) if data.get(field) is not None]


def _safe_path(file_path: Path, field: str, value: Any, root: Path, allow_dot: bool = False) -> List[Finding]:
    if not isinstance(value, str) or (not value and not allow_dot):
        return [_finding(file_path, field, value, "non-empty project-relative path", "use a relative path")]
    if "$" in value or "%" in value or Path(value).is_absolute() or (".." in Path(value).parts):
        return [_finding(file_path, field, value, "safe project-relative path", "remove variables, absolute paths, and ..")]
    if any(part.startswith(".") for part in Path(value).parts if part not in (".",)):
        return [_finding(file_path, field, value, "path outside hidden runtime areas", "use a production path, not hidden runtime files")]
    try:
        candidate = (root / value).resolve()
        candidate.relative_to(root.resolve())
    except (OSError, ValueError):
        return [_finding(file_path, field, value, "path resolving inside project root", "use a non-symlink project-relative path")]
    return []


def _validate_references(index: ProjectIndex) -> List[Finding]:
    out: List[Finding] = []
    entities = index.entities
    def has(kind: str, entity_id: Any) -> bool: return entity_id in entities.get(kind, {})
    for candidate_id, candidate in entities.get("candidate", {}).items():
        path = index.files["candidate"][candidate_id]
        if not has("render_plan", candidate.get("render_plan_id")):
            out.append(_finding(path, "render_plan_id", candidate.get("render_plan_id"), "existing Render Plan", "create or correct the plan reference"))
        job = entities.get("render_job", {}).get(candidate.get("render_job_id"))
        if job is None:
            out.append(_finding(path, "render_job_id", candidate.get("render_job_id"), "existing successful Render Job", "create or correct job reference"))
        elif job.get("status") != "SUCCEEDED":
            out.append(_finding(path, "render_job_id", candidate.get("render_job_id"), "Render Job with SUCCEEDED status", "do not promote failed/cancelled jobs"))
    for review_id, review in entities.get("review", {}).items():
        path = index.files["review"][review_id]
        if not has("candidate", review.get("candidate_id")):
            out.append(_finding(path, "candidate_id", review.get("candidate_id"), "existing Candidate", "correct or restore candidate"))
        for finding in review.get("findings", []) if isinstance(review.get("findings"), list) else []:
            for field in ("finding_id", "category", "severity", "start_timecode", "end_timecode", "frame", "evidence", "confidence", "suggested_action", "waived", "waiver_reason"):
                if field not in finding:
                    out.append(_finding(path, "findings.%s" % field, None, "required finding field", "add the field"))
    for selection_id, selection in entities.get("selection", {}).items():
        path, candidate = index.files["selection"][selection_id], entities.get("candidate", {}).get(selection.get("candidate_id"))
        if candidate is None:
            out.append(_finding(path, "candidate_id", selection.get("candidate_id"), "existing Candidate", "correct selection"))
        elif candidate.get("shot_id") != selection.get("shot_id"):
            out.append(_finding(path, "shot_id", selection.get("shot_id"), "candidate shot_id %s" % candidate.get("shot_id"), "match the candidate shot"))
        elif candidate.get("status") == "REJECTED":
            out.append(_finding(path, "candidate_id", selection.get("candidate_id"), "non-rejected Candidate", "select an approved candidate"))
    for cut_id, cut in entities.get("cut_manifest", {}).items():
        path = index.files["cut_manifest"][cut_id]
        for item in cut.get("timeline", []) if isinstance(cut.get("timeline"), list) else []:
            candidate = entities.get("candidate", {}).get(item.get("candidate_id"))
            if candidate is None:
                out.append(_finding(path, "timeline.candidate_id", item.get("candidate_id"), "existing Candidate", "correct cut timeline"))
            elif candidate.get("shot_id") != item.get("shot_id"):
                out.append(_finding(path, "timeline.shot_id", item.get("shot_id"), "candidate shot_id %s" % candidate.get("shot_id"), "match candidate shot"))
            elif candidate.get("status") == "REJECTED":
                out.append(_finding(path, "timeline.candidate_id", item.get("candidate_id"), "non-rejected Candidate", "use approved candidate"))
    versions = {}
    for candidate_id, candidate in entities.get("candidate", {}).items():
        key = (candidate.get("shot_id"), candidate.get("version"))
        if key in versions:
            out.append(_finding(index.files["candidate"][candidate_id], "version", candidate.get("version"), "unique candidate version for shot", "allocate a new candidate version"))
        else:
            versions[key] = candidate_id
    return out


def _validate_files(index: ProjectIndex) -> List[Finding]:
    out: List[Finding] = []
    for candidate_id, candidate in index.entities.get("candidate", {}).items():
        path = index.files["candidate"][candidate_id]
        media = index.root / candidate.get("video_path", "")
        if not media.is_file() or media.stat().st_size == 0:
            out.append(_finding(path, "video_path", candidate.get("video_path"), "existing non-empty media file", "supply valid media before FILES validation"))
            continue
        checksum = candidate.get("checksum")
        if isinstance(checksum, str) and checksum:
            actual = hashlib.sha256(media.read_bytes()).hexdigest()
            if actual != checksum:
                out.append(_finding(path, "checksum", checksum, "sha256:%s" % actual, "update only via a new immutable candidate"))
    return out


def findings_as_dict(findings: List[Finding]) -> List[Dict[str, Any]]:
    """Return JSON-serialisable findings."""
    return [asdict(item) for item in findings]
