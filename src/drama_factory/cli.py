"""Read-only command-line interface for V2.1-A."""

import argparse
import json
import traceback
from typing import Optional, Sequence

from .errors import DramaFactoryError
from .bootstrap import create_project
from .rendering import create_plan, run_plan
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
        if args.command == "candidate":
            item=project.entities.get("candidate",{}).get(args.candidate_id)
            if not item: print("Candidate not found"); return 2
            print(json.dumps(item,indent=2)); return 0
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
