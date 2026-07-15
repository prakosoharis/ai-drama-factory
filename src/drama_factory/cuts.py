"""File-based DRAFT cuts and deterministic mock assembly."""
import json, os, hashlib
from datetime import datetime, timezone
from pathlib import Path
from .project import load_project
from .errors import InvalidMetadataError

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
def write(p,d):
 t=p.with_suffix('.tmp'); t.write_text(json.dumps(d,indent=2)+'\n'); os.replace(t,p)
def next_id(cuts): return 'cut-rough-%03d'%(max([int(x[-3:]) for x in cuts if x[-3:].isdigit()] or [0])+1)
def create(project,name,purpose='ROUGH_CUT',parent=None):
 i=load_project(project); cid=next_id(i.entities.get('cut_manifest',{})); d={'entity_type':'cut_manifest','schema_version':'0.1','cut_id':cid,'project_id':i.manifest['project_id'],'cut_name':name,'cut_version':int(cid[-3:]),'purpose':purpose,'status':'DRAFT','timeline':[],'audio':{},'created_at':now(),'created_by':'cli','parent_cut_id':parent,'notes':None,'provenance':{}}; p=i.root/'project/cuts'/(cid+'.json'); write(p,d); return cid
def add_shot(project,cid,shot,source_in,source_out,notes):
 i=load_project(project); c=i.entities.get('cut_manifest',{}).get(cid)
 if not c or c['status']!='DRAFT': raise InvalidMetadataError('Cut must exist and be DRAFT')
 sels=[s for s in i.entities.get('selection',{}).values() if s['shot_id']==shot and s['purpose']==c['purpose']];
 if not sels: raise InvalidMetadataError('No active selection for shot and purpose')
 s=sorted(sels,key=lambda x:x['selected_at'])[-1]; cand=i.entities['candidate'][s['candidate_id']]
 if source_out>cand['duration']: raise InvalidMetadataError('source_out exceeds candidate duration')
 start=sum(x['timeline_out']-x['timeline_in'] for x in c['timeline']); c['timeline'].append({'timeline_item_id':'item-%03d'%(len(c['timeline'])+1),'sequence_index':len(c['timeline'])+1,'shot_id':shot,'candidate_id':cand['candidate_id'],'selection_id':s['selection_id'],'source_in':source_in,'source_out':source_out,'timeline_in':start,'timeline_out':start+source_out-source_in,'transition':'cut','audio_package_id':None,'notes':notes}); write(i.files['cut_manifest'][cid],c)
def assemble(project,cid):
 i=load_project(project); c=i.entities.get('cut_manifest',{}).get(cid)
 if not c or not c['timeline']: raise InvalidMetadataError('Cut requires timeline items')
 lines=[]
 for x in c['timeline']:
  cand=i.entities['candidate'].get(x['candidate_id']);
  if not cand or cand['status']=='REJECTED': raise InvalidMetadataError('Cut references invalid candidate')
  lines.append('%s %s %s'%(x['shot_id'],x['candidate_id'],cand['checksum']))
 text='Cut ID: %s\nCut version: %s\n'% (cid,c['cut_version'])+'\n'.join(lines)+'\nTotal duration: %s\n'%sum(x['timeline_out']-x['timeline_in'] for x in c['timeline'])
 existing=list((i.root/'project/delivery').glob(cid+'-mock-*.txt')); out=i.root/'project/delivery'/(cid+'-mock-%03d.txt'%(len(existing)+1)); out.write_text(text); return out
def clone(project,cid,name):
 i=load_project(project); parent=i.entities.get('cut_manifest',{}).get(cid)
 if not parent: raise InvalidMetadataError('Cut not found')
 new=create(project,name,parent['purpose'],cid); data=i.entities['cut_manifest'].get(new)
 if data is None: data=json.loads((i.root/'project/cuts'/(new+'.json')).read_text())
 data['timeline']=parent['timeline']; write(i.root/'project/cuts'/(new+'.json'),data); return new
