"""Deterministic, non-overwriting creative-project bootstrap."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .errors import InvalidMetadataError
from .ids import is_valid_id
from .project import MANIFEST_NAME


def create_project(target: str, project_id: str, name: str, description: str, force_empty: bool = False) -> List[Path]:
    """Create a minimal native V2 project or fail without overwriting files."""
    root = Path(target).expanduser()
    if root.exists() and any(root.iterdir()):
        raise InvalidMetadataError("%s: target directory is not empty" % root)
    if root.exists() and not force_empty:
        raise InvalidMetadataError("%s: empty target requires --force-empty-directory" % root)
    if not is_valid_id("project", project_id):
        raise InvalidMetadataError("project_id: use lowercase human-readable ID, e.g. ai-drama-pilot")
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / MANIFEST_NAME
    if manifest.exists():
        raise InvalidMetadataError("%s: existing project manifest must not be overwritten" % manifest)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    dirs = ["project/brief", "project/story", "project/characters", "project/environments", "project/scenes/scene-001", "project/shots/shot-001/render-plans", "project/shots/shot-001/jobs", "project/shots/shot-001/candidates", "project/shots/shot-001/reviews", "project/shots/shot-001/selections", "project/shots/shot-001/publishes", "project/cuts", "project/audio/dialogue", "project/audio/shot-sync", "project/audio/ambience", "project/audio/music", "project/audio/stems", "project/editorial/storyboard", "project/editorial/animatic", "project/editorial/proxies", "project/editorial/conform", "project/delivery", ".drama-factory/cache", ".drama-factory/runtime", ".drama-factory/locks", ".drama-factory/temp"]
    for directory in dirs: (root / directory).mkdir(parents=True, exist_ok=True)
    paths = {"brief":"project/brief","story":"project/story","characters":"project/characters","environments":"project/environments","scenes":"project/scenes","shots":"project/shots","cuts":"project/cuts","audio":"project/audio","editorial":"project/editorial","delivery":"project/delivery"}
    manifest_data = {"schema_version":"0.1","project_id":project_id,"project_name":name,"description":description,"engine_version":"0.1.0","project_root":".","paths":paths,"default_renderer":None,"default_audio_policy":"local-post-production","created_at":now,"updated_at":now}
    scene = {"entity_type":"scene_contract","schema_version":"0.1","scene_id":"scene-001","title":"Workflow validation scene","objective":"This scene exists only to validate the native V2 production workflow.","mood":"neutral","pacing":"measured","environment":"placeholder interior","lighting_intention":"soft neutral","ambience_intention":"quiet room tone","status":"DRAFT","revision":1,"created_at":now,"updated_at":now}
    shot = {"entity_type":"shot_contract","schema_version":"0.1","shot_id":"shot-001","scene_id":"scene-001","title":"Static workflow validation shot","dramatic_intention":"Validate native V2 metadata flow.","duration_target":4,"characters":["performer-001"],"environment":"placeholder interior","start_state":"still","end_state":"still","primary_action":"remain still with limited natural movement","camera":"fixed medium shot","lighting":"soft neutral","dialogue_dependency":None,"audio_dependency":None,"continuity_dependencies":[],"references":[],"known_risks":["low motion tolerance"],"acceptance_criteria":["stable framing","limited movement"],"status":"DRAFT","revision":1,"created_at":now,"updated_at":now}
    files: Dict[str, str] = {MANIFEST_NAME: json.dumps(manifest_data, indent=2)+"\n", "README.md":"# %s\n\nFirst native V2 AI Drama Factory creative project. Validate with `drama validate --project . --level structure`. Rendering and assembly are not implemented.\n" % name, "PROJECT-CONTEXT.md":"# Project Context\n\nPurpose: native V2 workflow validation. Engine: ai-drama-factory. Current milestone: V2.1-B bootstrap. Current scene and shot: scene-001 / shot-001. Do not modify engine source here; inspect before modifying and update this context after major production decisions.\n", "AGENTS.md":"# Project Agent Rules\n\nInspect before modifying. Do not modify engine source from this repository. Never overwrite candidate folders or delete published assets. Do not run GPU tasks or generate large assets without approval. Preserve provenance, do not silently change a rendered Shot Contract, and keep runtime files out of Git.\n", ".gitignore":".DS_Store\n.env\n.env.*\ncredentials/\n.venv/\n__pycache__/\nnode_modules/\n*.log\n*.tmp\n/.drama-factory/cache/\n/.drama-factory/runtime/\n/.drama-factory/locks/\n/.drama-factory/temp/\nproject/shots/*/candidates/*/*.mp4\nproject/shots/*/candidates/*/*.mov\nproject/editorial/proxies/\nproject/delivery/.scratch/\n", "project/brief/creative-brief.md":"# Creative Brief\n\nTODO: define the native V2 pilot brief.\n", "project/story/story.md":"# Story\n\nTODO: define story after workflow validation.\n", "project/story/screenplay.md":"# Screenplay\n\nTODO: define screenplay after workflow validation.\n", "project/scenes/scene-001/scene-contract.json":json.dumps(scene, indent=2)+"\n", "project/shots/shot-001/shot-contract.json":json.dumps(shot, indent=2)+"\n"}
    created = []
    for relative, content in files.items():
        path = root / relative
        path.write_text(content, encoding="utf-8"); created.append(path)
    bootstrap = {"schema_version":"0.1","bootstrap_version":"0.1","project_id":project_id,"template":"minimal-drama","created_at":now,"engine_version":"0.1.0","files_created":[str(p.relative_to(root)) for p in created]}
    path = root / ".drama-factory/bootstrap.json"; path.write_text(json.dumps(bootstrap, indent=2)+"\n", encoding="utf-8"); created.append(path)
    return created
