"""Append-only reviews and selections for immutable candidates."""
import json, os
from datetime import datetime, timezone
from pathlib import Path
from .errors import InvalidMetadataError
from .project import load_project
from .validator import validate

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
def write(path,data):
    tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(data,indent=2)+'\n'); os.replace(tmp,path)
def next_id(existing,prefix):
    nums=[int(x.rsplit('-',1)[1]) for x in existing if x.startswith(prefix) and x.rsplit('-',1)[1].isdigit()]
    return prefix+('%03d'%(max(nums,default=0)+1))
def effective(index,cid):
    reviews=[r for r in index.entities.get('review',{}).values() if r['candidate_id']==cid]
    reviews.sort(key=lambda r:r['created_at'])
    for r in reversed(reviews):
      if r['decision']=='APPROVE_PICTURE': return 'PICTURE_APPROVED'
      if r['decision']=='REJECT': return 'REJECTED'
    return 'REVIEW_REQUIRED'
def add_review(project,cid,decision,summary,reviewer,reviewer_type='human',findings=None,waive=False,waiver_reason=None,waive_ids=None):
    index=load_project(project); candidate=index.entities.get('candidate',{}).get(cid)
    if not candidate: raise InvalidMetadataError('Candidate not found: '+cid)
    if decision=='APPROVE_PICTURE' and reviewer_type!='human': raise InvalidMetadataError('Only a human reviewer can approve picture')
    if decision=='APPROVE_PICTURE':
      failures=[f for f in validate(index,'files') if f.file==str(index.files['candidate'][cid])]
      if failures: raise InvalidMetadataError('Cannot approve candidate because its package validation failed; it may be modified or corrupted')
    findings=findings or []
    blockers=[f for r in index.entities.get('review',{}).values() if r['candidate_id']==cid for f in r.get('findings',[]) if f.get('severity')=='blocker' and not f.get('waived')]
    ids={f.get('finding_id') for f in blockers}; waive_ids=waive_ids or []
    if decision=='APPROVE_PICTURE' and blockers and set(waive_ids)!=ids: raise InvalidMetadataError('Cannot approve: explicitly waive every unresolved blocker finding ID')
    if waive and not waiver_reason: raise InvalidMetadataError('Waiver requires --waiver-reason')
    shot=candidate['shot_id']; rid=next_id(index.entities.get('review',{}),'rev-cand-'+shot+'-'+cid[-3:]+'-')
    for f in findings:
      f.update({'status':f.get('status','OPEN'),'waived':waive or f.get('waived',False),'waiver_reason':waiver_reason if waive else f.get('waiver_reason'),'waived_by':reviewer if waive else f.get('waived_by'),'waived_at':now() if waive else f.get('waived_at')})
    waived=[{'finding_id':x,'waiver_reason':waiver_reason,'waived_by':reviewer,'waived_at':now()} for x in waive_ids]
    data={'entity_type':'review','schema_version':'0.1','review_id':rid,'candidate_id':cid,'reviewer':reviewer,'reviewer_type':reviewer_type,'created_at':now(),'decision':decision,'summary':summary,'findings':findings,'waived_findings':waived,'supersedes_review_id':None,'source':'cli','tool_version':'0.1.0'}
    path=index.root/'project/shots'/shot/'reviews'/(rid+'.json'); write(path,data); return rid
def select(project,cid,purpose,who,notes):
    index=load_project(project); c=index.entities.get('candidate',{}).get(cid)
    if not c: raise InvalidMetadataError('Candidate not found: '+cid)
    status=effective(index,cid)
    if purpose in ('ROUGH_CUT','FINAL_CUT') and status!='PICTURE_APPROVED': raise InvalidMetadataError('Cannot select %s for %s because its effective status is %s'%(cid,purpose,status))
    if purpose in ('ROUGH_CUT','FINAL_CUT') and any(f.file==str(index.files['candidate'][cid]) for f in validate(index,'files')): raise InvalidMetadataError('Cannot select candidate because its package validation failed; it may be modified or corrupted')
    shot=c['shot_id']; old=[s for s in index.entities.get('selection',{}).values() if s['shot_id']==shot and s['purpose']==purpose]; old.sort(key=lambda s:s['selected_at']); sid=next_id(index.entities.get('selection',{}),'sel-'+shot+'-')
    data={'entity_type':'selection','schema_version':'0.1','selection_id':sid,'shot_id':shot,'candidate_id':cid,'selected_by':who,'selected_at':now(),'purpose':purpose,'notes':notes,'supersedes_selection_id':old[-1]['selection_id'] if old else None,'active':True,'created_by_tool_version':'0.1.0'}
    path=index.root/'project/shots'/shot/'selections'/(sid+'.json'); write(path,data); return sid
