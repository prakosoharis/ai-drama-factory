"""Single-shot mock rendering with atomic candidate publication."""
import hashlib, json, os, platform, shutil, socket, sys, time
from datetime import datetime, timezone
from pathlib import Path
from .errors import InvalidMetadataError
from .project import load_project

def _now(): return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
def _write(path, data):
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(json.dumps(data,indent=2)+"\n"); os.replace(tmp,path)
def _hash(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def _next(root, shot, prefix, existing):
    nums=[int(x.rsplit("-",1)[1]) for x in existing if x.startswith(prefix+shot+"-") and x.rsplit("-",1)[1].isdigit()]
    return "%s%s-%03d"%(prefix,shot,max(nums,default=0)+1)
def _lock(root, shot):
    p=root/".drama-factory/locks"/(shot+".render.lock"); p.parent.mkdir(parents=True,exist_ok=True)
    try: fd=os.open(str(p),os.O_CREAT|os.O_EXCL|os.O_WRONLY); os.write(fd,str(os.getpid()).encode()); os.close(fd)
    except FileExistsError: raise InvalidMetadataError("%s: stale or active render lock; inspect before recovery"%p)
    return p

def create_plan(project_path, shot_id, renderer, task, duration, resolution, fps):
    index=load_project(project_path); root=index.root; shot=index.entities.get("shot_contract",{}).get(shot_id)
    if not shot: raise InvalidMetadataError("%s: Shot Contract not found"%shot_id)
    if renderer!="mock" or task not in ("image-to-video","synthetic-video"): raise InvalidMetadataError("renderer/task incompatible; mock supports image-to-video or synthetic-video")
    plans=index.entities.get("render_plan",{}); pid=_next(root,shot_id,"rp-",plans)
    base=root/"project/shots"/shot_id/"render-plans"/pid; base.mkdir(parents=True,exist_ok=False)
    contract_path=index.files["shot_contract"][shot_id]; contract_hash=_hash(contract_path)
    prompt="\n".join(["Dramatic intention: "+str(shot["dramatic_intention"]),"Subject: "+", ".join(shot["characters"]),"Action: "+shot["primary_action"],"Camera: "+shot["camera"],"Lighting: "+shot["lighting"],"Duration: "+str(duration),"Acceptance: "+", ".join(shot["acceptance_criteria"])])+"\n"
    (base/"prompt.txt").write_text(prompt); (base/"negative-prompt.txt").write_text("No excessive motion.\n")
    data={"entity_type":"render_plan","schema_version":"0.1","render_plan_id":pid,"shot_id":shot_id,"shot_contract_revision":shot["revision"],"shot_contract_checksum":contract_hash,"renderer":"mock","renderer_version":"0.1","model":"mock-video-generator","model_version":"0.1","task":task,"compiler_version":"0.1","prompt_artifact":str((base/"prompt.txt").relative_to(root)),"negative_prompt_artifact":str((base/"negative-prompt.txt").relative_to(root)),"references":[],"audio_conditioning":None,"duration":duration,"resolution":resolution,"fps":fps,"seed_policy":"deterministic","selected_seed":int(pid[-3:]),"candidate_budget":1,"handles":0,"model_specific":{"mock":{"media_type":"application/x-ai-drama-factory-mock"}},"estimated_cost":None,"created_at":_now(),"created_by":"cli"}
    _write(base/"render-plan.json",data); return pid,base/"render-plan.json"

def run_plan(project_path, plan_id, failure=None):
    index=load_project(project_path); root=index.root; plan=index.entities.get("render_plan",{}).get(plan_id)
    if not plan: raise InvalidMetadataError("%s: Render Plan not found"%plan_id)
    shot=plan["shot_id"]; lock=_lock(root,shot)
    try:
      jobs=index.entities.get("render_job",{}); candidates=index.entities.get("candidate",{}); jid=_next(root,shot,"job-",jobs); cid=_next(root,shot,"cand-",candidates); jobpath=root/"project/shots"/shot/"jobs"/(jid+".json"); queued=_now()
      job={"entity_type":"render_job","schema_version":"0.1","render_job_id":jid,"render_plan_id":plan_id,"candidate_id":cid,"status":"QUEUED","worker":"local","provider":"mock","queued_at":queued,"started_at":None,"completed_at":None,"exit_code":None,"runtime_seconds":None,"estimated_cost":None,"actual_cost":None,"log_path":None,"error":None,"retry_of":None,"history":[{"status":"QUEUED","at":queued}]}; _write(jobpath,job)
      job["status"]="RUNNING"; job["started_at"]=_now(); job["history"].append({"status":"RUNNING","at":job["started_at"]}); _write(jobpath,job); stage=root/".drama-factory/temp"/jid; stage.mkdir(parents=True,exist_ok=False)
      if failure: raise RuntimeError("injected %s"%failure)
      artifact=stage/"candidate.mock"; artifact.write_text("MOCK\nshot_id=%s\nplan=%s\nseed=%s\n"%(shot,plan_id,plan["selected_seed"])); checksum=_hash(artifact)
      final=root/"project/shots"/shot/"candidates"/cid
      if final.exists(): raise RuntimeError("candidate destination already exists")
      rel=lambda p:str(p.relative_to(root)); finished=_now(); provenance={"project_id":index.manifest["project_id"],"shot_id":shot,"shot_contract_revision":plan["shot_contract_revision"],"shot_contract_checksum":plan["shot_contract_checksum"],"render_plan_id":plan_id,"render_plan_checksum":_hash(index.files["render_plan"][plan_id]),"render_job_id":jid,"renderer":"mock","renderer_version":"0.1","model":"mock-video-generator","model_version":"0.1","task":plan["task"],"seed":plan["selected_seed"],"input_references":[],"prompt_artifact_checksum":_hash(root/plan["prompt_artifact"]),"output_checksum":checksum,"runtime_environment":{"python":sys.version.split()[0],"system":platform.system(),"architecture":platform.machine(),"hostname":socket.gethostname()},"started_at":job["started_at"],"completed_at":finished,"runtime_seconds":0}
      candidate={"entity_type":"candidate","schema_version":"0.1","candidate_id":cid,"shot_id":shot,"render_plan_id":plan_id,"render_job_id":jid,"version":int(cid[-3:]),"status":"REVIEW_REQUIRED","video_path":None,"artifact_path":rel(final/"candidate.mock"),"media_type":"application/x-ai-drama-factory-mock","proxy_path":None,"thumbnail_path":None,"metadata_path":rel(final/"candidate.json"),"checksum":checksum,"duration":plan["duration"],"fps":plan["fps"],"resolution":plan["resolution"],"created_at":finished,"provenance":rel(final/"provenance.json"),"qc_summary":rel(final/"qc-summary.json")}
      _write(stage/"candidate.json",candidate); _write(stage/"provenance.json",provenance); _write(stage/"qc-summary.json",{"artifact_exists":"PASS","artifact_non_empty":"PASS","checksum_verified":"PASS","media_type":"PASS","real_video_validation":"NOT_APPLICABLE"}); (stage/"renderer.log").write_text("mock renderer succeeded\n"); os.replace(stage,final)
      job.update({"status":"SUCCEEDED","completed_at":finished,"runtime_seconds":0,"exit_code":0,"log_path":rel(final/"renderer.log")}); job["history"].append({"status":"SUCCEEDED","at":finished}); _write(jobpath,job); return jid,cid
    except Exception as exc:
      if 'job' in locals():
       job.update({"status":"FAILED","completed_at":_now(),"exit_code":1,"error":{"code":"RENDER_FAILED","message":str(exc),"phase":"execute","recoverable":True}}); job["history"].append({"status":"FAILED","at":job["completed_at"]}); _write(jobpath,job)
      raise
    finally: lock.unlink(missing_ok=True)
