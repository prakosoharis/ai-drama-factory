"""File-backed creative-development documents, kept outside engine entities."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from drama_factory.errors import InvalidMetadataError
from drama_factory.project import load_project
from drama_factory.validator import validate

DOCUMENTS = {
    "idea": "project/development/idea.json", "creative-brief": "project/development/creative-brief.json",
    "story": "project/development/story.json", "screenplay": "project/development/screenplay.json",
    "scene-breakdown": "project/preproduction/scene-breakdown.json", "shot-plan": "project/preproduction/shot-plan.json",
    "storyboard": "project/preproduction/storyboard.json",
}
STATUSES = {"NOT_STARTED", "DRAFT", "IN_REVIEW", "APPROVED", "NEEDS_REVISION"}
TRANSITIONS = {"NOT_STARTED": {"DRAFT"}, "DRAFT": {"DRAFT", "IN_REVIEW", "NEEDS_REVISION"}, "IN_REVIEW": {"APPROVED", "NEEDS_REVISION", "DRAFT"}, "APPROVED": {"NEEDS_REVISION"}, "NEEDS_REVISION": {"DRAFT", "IN_REVIEW"}}

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True); temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8"); os.replace(temp, path)
def path(project, doc_type):
    if doc_type not in DOCUMENTS: raise InvalidMetadataError("unknown journey document type")
    return Path(project) / DOCUMENTS[doc_type]
def default(project_id, doc_type):
    return {"schema_version":"0.1","project_id":project_id,"document_type":doc_type,"status":"NOT_STARTED","revision":0,"title":"","content":{},"notes":"","source":"human","created_at":None,"updated_at":None,"approved_at":None,"approved_by":None}
def get(project, doc_type):
    idx=load_project(project); p=path(project,doc_type)
    if not p.exists(): return default(idx.manifest["project_id"],doc_type)
    try: return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc: raise InvalidMetadataError("journey document is unreadable JSON") from exc
def save(project, doc_type, incoming):
    current=get(project,doc_type); data={**current, **{k:v for k,v in incoming.items() if k in {"title","content","notes","source"}}}
    if not isinstance(data["content"], (dict,list,str)): raise InvalidMetadataError("content must be an object, list, or text")
    data["revision"]=int(current.get("revision",0))+1; data["status"] = current.get("status", "NOT_STARTED") if current.get("status")!="NOT_STARTED" else "DRAFT"
    data["created_at"] = current.get("created_at") or now(); data["updated_at"] = now(); write(path(project,doc_type),data); return data
def set_status(project, doc_type, status, by):
    if status not in STATUSES: raise InvalidMetadataError("invalid journey status")
    data=get(project,doc_type); old=data["status"]
    if status not in TRANSITIONS.get(old,set()): raise InvalidMetadataError("invalid status transition: %s -> %s"%(old,status))
    data["status"]=status; data["revision"]=int(data.get("revision",0))+1; data["updated_at"]=now(); data["created_at"]=data.get("created_at") or now()
    if status=="APPROVED": data["approved_at"]=now(); data["approved_by"]=by
    write(path(project,doc_type),data); return data
def notes_path(project): return Path(project)/"project/development/discussion-notes.json"
def notes(project):
    p=notes_path(project)
    if not p.exists(): return []
    data=json.loads(p.read_text(encoding="utf-8")); return data.get("notes",[])
def save_notes(project, rows): write(notes_path(project), {"schema_version":"0.1","notes":rows,"updated_at":now()})
def add_note(project, data):
    rows=notes(project); n={"note_id":"note-%03d"%(len(rows)+1),"stage":data.get("stage","Idea"),"title":data.get("title",""),"content":data.get("content",""),"source":data.get("source","human"),"author":data.get("author",""),"created_at":now(),"tags":data.get("tags",[]),"incorporated":False}; rows.append(n); save_notes(project,rows); return n
def update_note(project, note_id, data):
    rows=notes(project)
    for row in rows:
        if row["note_id"]==note_id:
            row.update({k:v for k,v in data.items() if k in {"title","content","source","author","tags","incorporated"}}); save_notes(project,rows); return row
    raise InvalidMetadataError("discussion note not found")
def delete_note(project,note_id):
    rows=notes(project); row=next((x for x in rows if x["note_id"]==note_id),None)
    if not row: raise InvalidMetadataError("discussion note not found")
    if row.get("incorporated"): raise InvalidMetadataError("incorporated notes cannot be deleted")
    save_notes(project,[x for x in rows if x["note_id"]!=note_id])
def handoff(project, approved_by, confirm_overwrite=False):
    plan=get(project,"shot-plan")
    if plan["status"]!="APPROVED": raise InvalidMetadataError("Shot Plan must be approved before production handoff")
    if not isinstance(plan["content"],list): raise InvalidMetadataError("Shot Plan content must be a list of shots")
    idx=load_project(project); created=[]
    for shot in plan["content"]:
        sid=shot.get("shot_id")
        if not isinstance(sid,str) or not sid: raise InvalidMetadataError("every planned shot requires shot_id")
        target=Path(project)/"project/shots"/sid/"shot-contract.json"; existing=target.exists()
        if existing and not confirm_overwrite: raise InvalidMetadataError("Shot Contract exists for %s; confirm overwrite to create a revision"%sid)
        old={}
        if existing:
            old=json.loads(target.read_text()); history=Path(project)/"project/history/shot-contracts"; history.mkdir(parents=True,exist_ok=True)
            write(history/(sid+"-r%03d.json"%int(old.get("revision",1))),old)
        data={"entity_type":"shot_contract","schema_version":"0.1","shot_id":sid,"scene_id":shot.get("scene_id","scene-001"),"title":shot.get("title",sid),"dramatic_intention":shot.get("dramatic_purpose",""),"duration_target":shot.get("target_duration",1),"characters":shot.get("characters",[]),"environment":shot.get("environment",""),"start_state":shot.get("start_state",""),"end_state":shot.get("end_state",""),"primary_action":shot.get("character_action",""),"camera":shot.get("framing",""),"lighting":shot.get("lighting",""),"dialogue_dependency":None,"audio_dependency":None,"continuity_dependencies":shot.get("continuity_notes",[]),"references":shot.get("required_references",[]),"known_risks":shot.get("known_risks",[]),"acceptance_criteria":shot.get("acceptance_criteria",[]),"status":"APPROVED_FOR_PLANNING","revision":int(old.get("revision",0))+1,"created_at":old.get("created_at") or now(),"updated_at":now(),"provenance":{"source_document":"shot-plan","source_revision":plan["revision"],"handoff_approved_by":approved_by}}
        write(target,data); created.append(sid)
    findings=validate(load_project(project),"structure")
    return {"created_or_revised":created,"findings":[f.__dict__ for f in findings]}
