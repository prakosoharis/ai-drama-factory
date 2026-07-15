"""Read-only command-line interface for V2.1-A."""

import argparse
import json
import traceback
from typing import Optional, Sequence

from .errors import DramaFactoryError
from .bootstrap import create_project
from .rendering import create_plan, run_plan
from .reviewing import add_review, select, effective
from .cuts import create as create_cut, add_shot, assemble as assemble_cut, clone as clone_cut
from .project import load_project
from .validator import findings_as_dict, validate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="drama")
    parser.add_argument("--debug", action="store_true", help="show traceback for unexpected failures")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "validate"):
        item = sub.add_parser(name)
        item.add_argument("--project", help="project directory or drama-factory.project.json")
    validate_parser = sub.choices["validate"]
    validate_parser.add_argument("--level", choices=("structure", "files"), default="structure")
    validate_parser.add_argument("--format", choices=("text", "json"), default="text")
    shot = sub.add_parser("shot")
    shot_sub = shot.add_subparsers(dest="shot_command", required=True)
    show = shot_sub.add_parser("show")
    show.add_argument("shot_id")
    show.add_argument("--project", help="project directory or drama-factory.project.json")
    project = sub.add_parser("project")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    create = project_sub.add_parser("create")
    create.add_argument("project_path")
    create.add_argument("--project-id", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--template", choices=("minimal-drama",), default="minimal-drama")
    create.add_argument("--description", default="First native V2 production project for AI Drama Factory.")
    create.add_argument("--force-empty-directory", action="store_true")
    create.add_argument("--format", choices=("text", "json"), default="text")
    render=sub.add_parser("render"); render_sub=render.add_subparsers(dest="render_command",required=True)
    plan=render_sub.add_parser("plan"); plan_sub=plan.add_subparsers(dest="plan_command",required=True); pc=plan_sub.add_parser("create")
    pc.add_argument("shot_id");
    for arg,typ in (("--renderer",str),("--task",str),("--duration",int),("--resolution",str),("--fps",int)): pc.add_argument(arg,required=True,type=typ)
    pc.add_argument("--project",required=True)
    run=render_sub.add_parser("run"); run.add_argument("plan_id"); run.add_argument("--project",required=True); run.add_argument("--fail", choices=("before-output","partial-output"))
    candidates=sub.add_parser("candidates"); candidates.add_argument("shot_id"); candidates.add_argument("--project",required=True); candidates.add_argument("--format",choices=("text","json"),default="text")
    candidate=sub.add_parser("candidate"); cs=candidate.add_subparsers(dest="candidate_command",required=True); showc=cs.add_parser("show"); showc.add_argument("candidate_id"); showc.add_argument("--project",required=True)
    approve=cs.add_parser('approve'); approve.add_argument('candidate_id'); approve.add_argument('--project',required=True); approve.add_argument('--reviewer',required=True); approve.add_argument('--summary',required=True); approve.add_argument('--waive-findings',action='store_true'); approve.add_argument('--waive-finding',action='append',default=[]); approve.add_argument('--waiver-reason')
    reject=cs.add_parser('reject'); reject.add_argument('candidate_id'); reject.add_argument('--project',required=True); reject.add_argument('--reviewer',required=True); reject.add_argument('--summary',required=True)
    compare=cs.add_parser('compare'); compare.add_argument('candidate_a'); compare.add_argument('candidate_b'); compare.add_argument('--project',required=True); compare.add_argument('--format',choices=('text','json'),default='text')
    review=sub.add_parser('review'); rs=review.add_subparsers(dest='review_command',required=True); ra=rs.add_parser('add'); ra.add_argument('candidate_id'); ra.add_argument('--project',required=True); ra.add_argument('--decision',required=True,choices=('APPROVE_PICTURE','REQUEST_REVISION','REJECT','COMMENT_ONLY')); ra.add_argument('--summary',required=True); ra.add_argument('--reviewer',required=True); ra.add_argument('--reviewer-type',default='human')
    rl=rs.add_parser('list'); rl.add_argument('candidate_id'); rl.add_argument('--project',required=True); rl.add_argument('--format',default='text',choices=('text','json'))
    finding=rs.add_parser('finding'); fs=finding.add_subparsers(dest='finding_command',required=True); fa=fs.add_parser('add'); fa.add_argument('candidate_id'); fa.add_argument('--project',required=True); fa.add_argument('--category',required=True); fa.add_argument('--severity',required=True); fa.add_argument('--start-timecode',required=True); fa.add_argument('--end-timecode',required=True); fa.add_argument('--evidence',required=True); fa.add_argument('--confidence',type=float,required=True); fa.add_argument('--suggested-action',required=True); fa.add_argument('--reviewer',default='human')
    sel=sub.add_parser('select'); sel.add_argument('candidate_id'); sel.add_argument('--project',required=True); sel.add_argument('--purpose',required=True,choices=('ROUGH_CUT','FINAL_CUT','BENCHMARK','PREVIEW')); sel.add_argument('--selected-by',required=True); sel.add_argument('--notes',default='')
    sels=sub.add_parser('selections'); sels.add_argument('shot_id'); sels.add_argument('--project',required=True); sels.add_argument('--format',default='text',choices=('text','json'))
    cut=sub.add_parser('cut'); cuts=cut.add_subparsers(dest='cut_command',required=True); cc=cuts.add_parser('create'); cc.add_argument('--project',required=True); cc.add_argument('--name',required=True); cc.add_argument('--purpose',default='ROUGH_CUT'); ca=cuts.add_parser('add-shot'); ca.add_argument('cut_id'); ca.add_argument('shot_id'); ca.add_argument('--project',required=True); ca.add_argument('--source-in',type=float,required=True); ca.add_argument('--source-out',type=float,required=True); ca.add_argument('--notes',default='')
    cl=cuts.add_parser('clone'); cl.add_argument('cut_id'); cl.add_argument('--project',required=True); cl.add_argument('--name',required=True)
    csw=cuts.add_parser('show'); csw.add_argument('cut_id'); csw.add_argument('--project',required=True)
    csl=cuts.add_parser('list'); csl.add_argument('--project',required=True)
    asm=sub.add_parser('assemble'); asm.add_argument('cut_id'); asm.add_argument('--project',required=True); asm.add_argument('--assembler',default='mock')
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the CLI and return documented process exit codes."""
    parser = _parser()
    try:
        args = parser.parse_args(argv)
        if args.command == "project":
            created = create_project(args.project_path, args.project_id, args.name, args.description, args.force_empty_directory)
            result = {"project_path": str(args.project_path), "project_id": args.project_id, "template": args.template, "files_created": [str(item) for item in created]}
            print(json.dumps(result, indent=2) if args.format == "json" else "Created:\n" + "\n".join(result["files_created"]))
            return 0
        if args.command == "render":
            if args.render_command=="plan":
                pid,path=create_plan(args.project,args.shot_id,args.renderer,args.task,args.duration,args.resolution,args.fps); print("Render Plan: %s\nPath: %s"%(pid,path)); return 0
            jid,cid=run_plan(args.project,args.plan_id,args.fail); print("Render Job: %s\nCandidate: %s"%(jid,cid)); return 0
        project = load_project(getattr(args, "project", None))
        if args.command == "candidates":
            rows=[x for x in project.entities.get("candidate",{}).values() if x.get("shot_id")==args.shot_id]
            print(json.dumps(rows,indent=2) if args.format=="json" else "\n".join("%s v%s %s %s"%(x["candidate_id"],x["version"],x["status"],x.get("artifact_path")) for x in rows)); return 0
        if args.command=='review':
            if args.review_command=='finding':
                f={'finding_id':'finding-'+args.candidate_id[-3:]+'-001','category':args.category,'severity':args.severity,'start_timecode':args.start_timecode,'end_timecode':args.end_timecode,'frame':None,'evidence':args.evidence,'confidence':args.confidence,'suggested_action':args.suggested_action}; print('Review: '+add_review(args.project,args.candidate_id,'COMMENT_ONLY','Finding added',args.reviewer,'human',[f])); return 0
            if args.review_command=='add': print('Review: '+add_review(args.project,args.candidate_id,args.decision,args.summary,args.reviewer,args.reviewer_type)); return 0
            rows=[r for r in project.entities.get('review',{}).values() if r['candidate_id']==args.candidate_id]; print(json.dumps(rows,indent=2) if args.format=='json' else '\n'.join('%s %s %s'%(r['review_id'],r['decision'],r['summary']) for r in rows)); return 0
        if args.command=='select': print('Selection: '+select(args.project,args.candidate_id,args.purpose,args.selected_by,args.notes)); return 0
        if args.command=='selections':
            rows=[s for s in project.entities.get('selection',{}).values() if s['shot_id']==args.shot_id]; superseded={s.get('supersedes_selection_id') for s in rows};
            for s in rows: s['_derived_status']='SUPERSEDED' if s['selection_id'] in superseded else 'ACTIVE'
            print(json.dumps(rows,indent=2) if args.format=='json' else '\n'.join('%s %s %s %s'%(s['selection_id'],s['purpose'],s['candidate_id'],s['_derived_status']) for s in rows)); return 0
        if args.command=='cut':
            if args.cut_command=='create': print('Cut: '+create_cut(args.project,args.name,args.purpose)); return 0
            if args.cut_command=='add-shot': add_shot(args.project,args.cut_id,args.shot_id,args.source_in,args.source_out,args.notes); print('Added shot'); return 0
            if args.cut_command=='clone': print('Cut: '+clone_cut(args.project,args.cut_id,args.name)); return 0
            p=load_project(args.project); cuts=p.entities.get('cut_manifest',{})
            if args.cut_command=='show': print(json.dumps(cuts.get(args.cut_id),indent=2)); return 0
            print('\n'.join('%s %s %s'%(x['cut_id'],x['status'],len(x['timeline'])) for x in cuts.values())); return 0
        if args.command=='assemble': print('Assembly: '+str(assemble_cut(args.project,args.cut_id))); return 0
        if args.command == "candidate":
            if args.candidate_command=='approve': print('Review: '+add_review(args.project,args.candidate_id,'APPROVE_PICTURE',args.summary,args.reviewer,waive=args.waive_findings or bool(args.waive_finding),waiver_reason=args.waiver_reason,waive_ids=args.waive_finding)); return 0
            if args.candidate_command=='reject': print('Review: '+add_review(args.project,args.candidate_id,'REJECT',args.summary,args.reviewer)); return 0
            if args.candidate_command=='compare':
                rows=[]
                for cid in (args.candidate_a,args.candidate_b):
                    item=project.entities.get('candidate',{}).get(cid)
                    if not item: raise DramaFactoryError('Candidate not found: '+cid)
                    plan=project.entities.get('render_plan',{}).get(item['render_plan_id'],{})
                    reviews=[r for r in project.entities.get('review',{}).values() if r['candidate_id']==cid]
                    rows.append({'candidate_id':cid,'renderer':plan.get('renderer'),'model':plan.get('model'),'seed':plan.get('selected_seed'),'render_plan_id':item['render_plan_id'],'duration':item['duration'],'resolution':item['resolution'],'checksum':item['checksum'],'effective_status':effective(project,cid),'review_decisions':[r['decision'] for r in reviews],'finding_count':sum(len(r.get('findings',[])) for r in reviews)})
                print(json.dumps(rows,indent=2) if args.format=='json' else '\n'.join('%s %s %s %s'%(r['candidate_id'],r['effective_status'],r['checksum'],r['render_plan_id']) for r in rows)); return 0
            item=project.entities.get("candidate",{}).get(args.candidate_id)
            if not item: print("Candidate not found"); return 2
            reviews=[r for r in project.entities.get('review',{}).values() if r['candidate_id']==args.candidate_id]
            selections=[s for s in project.entities.get('selection',{}).values() if s['candidate_id']==args.candidate_id]
            plan=project.entities.get('render_plan',{}).get(item['render_plan_id'],{})
            print('Candidate: %s\nShot: %s\nRendered status: %s\nEffective review status: %s\nRender Plan: %s\nRender Job: %s\nRenderer: %s\nModel: %s\nArtifact: %s\nChecksum: %s\nReviews: %d\nLatest review: %s\nSelected for: %s' % (item['candidate_id'],item['shot_id'],item['status'],effective(project,args.candidate_id),item['render_plan_id'],item['render_job_id'],plan.get('renderer'),plan.get('model'),item.get('artifact_path'),item['checksum'],len(reviews),reviews[-1]['decision'] if reviews else 'none',', '.join(s['purpose'] for s in selections) or 'none')); return 0
        if args.command == "inspect":
            findings = validate(project)
            print("Project: %s (%s)" % (project.manifest.get("project_name"), project.manifest.get("project_id")))
            print("Project file: %s" % project.manifest_path)
            print("Schema version: %s" % project.manifest.get("schema_version"))
            print("Engine version: %s" % project.manifest.get("engine_version"))
            print("Configured paths: %s" % json.dumps(project.manifest.get("paths", {}), sort_keys=True))
            print("Entity counts: %s" % json.dumps({k: project.count(k) for k in sorted(project.entities)}, sort_keys=True))
            print("Validation: %d error(s), %d warning(s)" % (len([f for f in findings if f.severity == "error"]), len([f for f in findings if f.severity == "warning"])))
            return 1 if findings else 0
        if args.command == "validate":
            findings = validate(project, args.level)
            if args.format == "json":
                print(json.dumps({"project_file": str(project.manifest_path), "level": args.level, "findings": findings_as_dict(findings)}, indent=2, default=str))
            else:
                for finding in findings:
                    print("%s: %s: %s=%r; expected %s; correction: %s" % (finding.file, finding.severity, finding.field, finding.invalid_value, finding.expected, finding.suggestion))
                if not findings:
                    print("Valid (%s): %s" % (args.level, project.manifest_path))
            return 1 if findings else 0
        shot_id = args.shot_id
        contract = project.entities.get("shot_contract", {}).get(shot_id)
        if contract is None:
            print("Shot %s not found" % shot_id)
            return 2
        plans = [x for x in project.entities.get("render_plan", {}).values() if x.get("shot_id") == shot_id]
        candidates = [x for x in project.entities.get("candidate", {}).values() if x.get("shot_id") == shot_id]
        candidate_ids = {x.get("candidate_id") for x in candidates}
        jobs = [x for x in project.entities.get("render_job", {}).values() if x.get("candidate_id") in candidate_ids]
        reviews = [x for x in project.entities.get("review", {}).values() if x.get("candidate_id") in candidate_ids]
        selections = [x for x in project.entities.get("selection", {}).values() if x.get("shot_id") == shot_id]
        cuts = [x.get("cut_id") for x in project.entities.get("cut_manifest", {}).values() if any(i.get("shot_id") == shot_id for i in x.get("timeline", []))]
        print("Shot: %s — %s" % (shot_id, contract.get("title")))
        print("Render plans: %d; jobs: %d; candidates: %d; reviews: %d" % (len(plans), len(jobs), len(candidates), len(reviews)))
        print("Candidate statuses: %s" % json.dumps({x["candidate_id"]: x.get("status") for x in candidates}, sort_keys=True))
        print("Active selections: %s" % json.dumps([x.get("selection_id") for x in selections]))
        print("Cuts using shot: %s" % json.dumps(cuts))
        related = [f for f in validate(project) if shot_id in str(f.invalid_value) or shot_id in f.file]
        print("Unresolved validation findings: %d" % len(related))
        return 1 if related else 0
    except DramaFactoryError as exc:
        print("Configuration error: %s" % exc)
        return 2
    except Exception as exc:  # deliberate CLI boundary
        if "args" in locals() and args.debug:
            traceback.print_exc()
        else:
            print("Internal failure: %s (use --debug for traceback)" % exc)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
