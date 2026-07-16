"""Small, file-backed HTTP facade over the Drama Factory domain services."""
import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from drama_factory.cuts import assemble
from drama_factory.errors import DramaFactoryError
from drama_factory.project import load_project
from drama_factory.reviewing import add_review, effective, select
from drama_factory.validator import validate
from . import journey


class ReviewRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=2000)


class SelectionRequest(BaseModel):
    selected_by: str = Field(min_length=1, max_length=120)
    purpose: str = "ROUGH_CUT"
    notes: str = Field(default="", max_length=2000)

class DocumentRequest(BaseModel):
    title: str = ""
    content: Any = {}
    notes: str = ""
    source: str = "human"
class StatusRequest(BaseModel):
    status: str
    approved_by: str = "portal-user"
class NoteRequest(BaseModel):
    stage: str = "Idea"; title: str = ""; content: str = ""; source: str = "human"; author: str = ""; tags: list[str] = []
class HandoffRequest(BaseModel):
    approved_by: str = "portal-user"
    confirm_overwrite: bool = False


def _configured_projects() -> dict[str, dict[str, str]]:
    root = Path(os.getenv("DRAMA_FACTORY_PROJECT_ROOT", "/projects")).resolve()
    try:
        items = json.loads(os.getenv("DRAMA_FACTORY_PROJECTS", "[]"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("DRAMA_FACTORY_PROJECTS must be JSON") from exc
    if not isinstance(items, list):
        raise RuntimeError("DRAMA_FACTORY_PROJECTS must be a JSON array")
    projects = {}
    for item in items:
        if not isinstance(item, dict) or not all(isinstance(item.get(k), str) for k in ("id", "name", "path")):
            raise RuntimeError("each configured project needs id, name, and path")
        path = Path(item["path"]).resolve()
        if path != root and root not in path.parents:
            raise RuntimeError("configured project path escapes DRAMA_FACTORY_PROJECT_ROOT")
        projects[item["id"]] = {"id": item["id"], "name": item["name"], "path": str(path)}
    return projects


def _project(project_id: str):
    config = _configured_projects().get(project_id)
    if not config:
        raise HTTPException(404, "project not found")
    try:
        return config, load_project(config["path"])
    except DramaFactoryError as exc:
        raise HTTPException(422, str(exc)) from exc


def _entity(index, kind: str, entity_id: str) -> dict[str, Any]:
    value = index.entities.get(kind, {}).get(entity_id)
    if not value:
        raise HTTPException(404, f"{kind} not found")
    result = dict(value)
    if kind == "candidate": result["effective_status"] = effective(index, entity_id)
    return result


app = FastAPI(title="AI Drama Factory API", version="0.1.0")
origins = [x.strip() for x in os.getenv("DRAMA_FACTORY_CORS_ORIGINS", "http://localhost:3000").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["content-type"])


@app.exception_handler(DramaFactoryError)
async def domain_error(_, exc: DramaFactoryError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/health")
def health(): return {"status": "ok"}


@app.get("/api/projects")
def projects(): return [{"id": p["id"], "name": p["name"]} for p in _configured_projects().values()]


@app.get("/api/projects/{project_id}")
def project(project_id: str):
    config, index = _project(project_id)
    return {"id": config["id"], "name": config["name"], "manifest": index.manifest, "counts": {k: len(v) for k, v in index.entities.items()}}


@app.get("/api/projects/{project_id}/validate")
def validation(project_id: str, level: str = "structure"):
    _, index = _project(project_id)
    return {"level": level, "findings": [f.__dict__ for f in validate(index, level)]}


@app.get("/api/projects/{project_id}/shots")
def shots(project_id: str):
    _, index = _project(project_id)
    return [_entity(index, "shot_contract", sid) for sid in sorted(index.entities.get("shot_contract", {}))]


@app.get("/api/projects/{project_id}/shots/{shot_id}")
def shot(project_id: str, shot_id: str):
    _, index = _project(project_id); return _entity(index, "shot_contract", shot_id)


@app.get("/api/projects/{project_id}/shots/{shot_id}/candidates")
def candidates(project_id: str, shot_id: str):
    _, index = _project(project_id)
    return [_entity(index, "candidate", cid) for cid, c in index.entities.get("candidate", {}).items() if c.get("shot_id") == shot_id]


@app.get("/api/projects/{project_id}/candidates/{candidate_id}")
def candidate(project_id: str, candidate_id: str):
    _, index = _project(project_id); return _entity(index, "candidate", candidate_id)


@app.post("/api/projects/{project_id}/candidates/{candidate_id}/approve")
def approve(project_id: str, candidate_id: str, body: ReviewRequest):
    config, _ = _project(project_id)
    return {"review_id": add_review(config["path"], candidate_id, "APPROVE_PICTURE", body.summary, body.reviewer)}


@app.post("/api/projects/{project_id}/candidates/{candidate_id}/reject")
def reject(project_id: str, candidate_id: str, body: ReviewRequest):
    config, _ = _project(project_id)
    return {"review_id": add_review(config["path"], candidate_id, "REJECT", body.summary, body.reviewer)}


@app.post("/api/projects/{project_id}/candidates/{candidate_id}/select")
def selection(project_id: str, candidate_id: str, body: SelectionRequest):
    config, _ = _project(project_id)
    return {"selection_id": select(config["path"], candidate_id, body.purpose, body.selected_by, body.notes)}


@app.get("/api/projects/{project_id}/cuts")
def cuts(project_id: str):
    _, index = _project(project_id); return list(index.entities.get("cut_manifest", {}).values())


@app.get("/api/projects/{project_id}/cuts/{cut_id}")
def cut(project_id: str, cut_id: str):
    _, index = _project(project_id); return _entity(index, "cut_manifest", cut_id)


@app.post("/api/projects/{project_id}/cuts/{cut_id}/assemble")
def cut_assemble(project_id: str, cut_id: str):
    config, _ = _project(project_id)
    output = assemble(config["path"], cut_id)
    return {"cut_id": cut_id, "artifact": str(output.relative_to(config["path"]))}

@app.get("/api/projects/{project_id}/journey")
def project_journey(project_id: str):
    config, _ = _project(project_id)
    stages=[("idea","Idea"),("creative-brief","Creative Brief"),("story","Story"),("screenplay","Screenplay"),("scene-breakdown","Scene Breakdown"),("shot-plan","Shot Planning"),("storyboard","Storyboard")]
    return [{"document_type":k,"name":n,**journey.get(config["path"],k)} for k,n in stages]

@app.get("/api/projects/{project_id}/documents/{document_type}")
def document_get(project_id: str, document_type: str):
    config, _ = _project(project_id); return journey.get(config["path"],document_type)

@app.put("/api/projects/{project_id}/documents/{document_type}")
def document_put(project_id: str, document_type: str, body: DocumentRequest):
    config, _ = _project(project_id); return journey.save(config["path"],document_type,body.model_dump())

@app.post("/api/projects/{project_id}/documents/{document_type}/status")
def document_status(project_id: str, document_type: str, body: StatusRequest):
    config, _ = _project(project_id); return journey.set_status(config["path"],document_type,body.status,body.approved_by)

@app.get("/api/projects/{project_id}/discussion-notes")
def discussion_notes(project_id: str):
    config, _ = _project(project_id); return journey.notes(config["path"])

@app.post("/api/projects/{project_id}/discussion-notes")
def discussion_note_add(project_id: str, body: NoteRequest):
    config, _ = _project(project_id); return journey.add_note(config["path"],body.model_dump())

@app.put("/api/projects/{project_id}/discussion-notes/{note_id}")
def discussion_note_update(project_id: str, note_id: str, body: NoteRequest):
    config, _ = _project(project_id); return journey.update_note(config["path"],note_id,body.model_dump())

@app.delete("/api/projects/{project_id}/discussion-notes/{note_id}")
def discussion_note_delete(project_id: str, note_id: str):
    config, _ = _project(project_id); journey.delete_note(config["path"],note_id); return {"deleted":note_id}

@app.get("/api/projects/{project_id}/preproduction/{kind}")
def preproduction_get(project_id: str, kind: str):
    if kind not in {"scenes", "shots"}: raise HTTPException(404, "pre-production collection not found")
    config, _ = _project(project_id); return journey.get(config["path"], "scene-breakdown" if kind=="scenes" else "shot-plan")

@app.post("/api/projects/{project_id}/preproduction/{kind}")
def preproduction_add(project_id: str, kind: str, body: DocumentRequest):
    if kind not in {"scenes", "shots"}: raise HTTPException(404, "pre-production collection not found")
    config, _ = _project(project_id); doc_type="scene-breakdown" if kind=="scenes" else "shot-plan"
    current=journey.get(config["path"],doc_type); rows=current.get("content",[])
    if not isinstance(rows,list): raise HTTPException(422,"document content must be a list")
    rows.append(body.content); return journey.save(config["path"],doc_type,{"title":current.get("title",""),"content":rows,"notes":current.get("notes",""),"source":body.source})

@app.put("/api/projects/{project_id}/preproduction/{kind}/{item_id}")
def preproduction_update(project_id: str, kind: str, item_id: str, body: DocumentRequest):
    if kind not in {"scenes", "shots"}: raise HTTPException(404, "pre-production collection not found")
    config, _ = _project(project_id); doc_type="scene-breakdown" if kind=="scenes" else "shot-plan"; current=journey.get(config["path"],doc_type); rows=current.get("content",[])
    key="scene_id" if kind=="scenes" else "shot_id"
    for n,row in enumerate(rows):
        if isinstance(row,dict) and row.get(key)==item_id: rows[n]=body.content; return journey.save(config["path"],doc_type,{"title":current.get("title",""),"content":rows,"notes":current.get("notes",""),"source":body.source})
    raise HTTPException(404, "planned item not found")

@app.post("/api/projects/{project_id}/preproduction/handoff")
def production_handoff(project_id: str, body: HandoffRequest):
    config, _ = _project(project_id); return journey.handoff(config["path"],body.approved_by,body.confirm_overwrite)
