# Project Context

## Origin

`project-film` V1 proved an end-to-end AI-film workflow: 22 shots, a final
film of approximately 1 minute 40 seconds, Wan2.2 self-hosted rendering on
Vast.ai, audio work, and final assembly. It is archived at tag
`v1.0-baseline` as a creative project and historical baseline.

V1 also exposed important limits. Its batch flow was too linear, individual
shot revisions were difficult, a shot had only one candidate, prompts became
an implicit source of truth, and approval, selection, editorial, continuity,
and publishing were insufficiently separated. Its visual quality remained
below the SeaDance quality benchmark.

## Why repositories are separated

`project-film` preserves the creative project, production outputs, and V1
history. `ai-drama-factory` is the reusable production system that will serve
that project and future productions. V1 must not be evolved in place into V2.

## Role of AI Drama Factory

AI Drama Factory orchestrates approved planning, assets, generative workers,
review, editorial, audio, quality control, and reproducible publishing. It is
not an attempt to build the best generative model.

## Current status

Current milestone: **V2.1-D — Review and Candidate Selection** is COMPLETE — MVP. V2.1-E is next and has not started.

V2.2 — Review and Selection Hardening is backlog for concurrent allocation,
full waiver edge cases, complex supersession chains/cycle detection, and
expanded exhaustive tests.

The first native V2 workflow will use a new, clean creative project. V1 is an
archived reference and optional future import test, not a V2 runtime dependency.

## V2.1 delivery sequence

1. **V2.1-A — Core Metadata and Validation** (complete)
2. **V2.1-B — New Project Bootstrap** (implemented; pending approval)
3. **V2.1-C — Single-Shot Candidate Workflow**
4. **V2.1-D — Review and Candidate Selection**
5. **V2.1-E — Cut Manifest and Reproducible Assembly**
6. **V2.1-F — New Native V2 Pilot Production**
7. **V2.1-G — Optional V1 Baseline Import**

V2.1-A now provides file-based project discovery, metadata loading, structural
and file-level validation, and read-only inspection for synthetic projects.
Rendering, review mutation, selection mutation, assembly, new-project
bootstrap, native pilot production, and optional V1 import remain deferred.

## Current non-goals

- Implementing a production pipeline, database, web UI, CLI, distributed
  queue, or AI Director.
- Running GPU workloads or installing dependencies.
- Copying V1 video, audio, model weights, caches, or other production assets.
- Defining final schemas before production requirements validate them.

## Key terms

- **Shot Contract:** approved, structured intent and constraints for a shot.
- **Candidate:** an immutable render output awaiting or carrying a review
  decision.
- **Cut Manifest:** the versioned timeline selection used for assembly.
- **Published artifact:** an immutable approved production output.
- **SeaDance benchmark:** a quality reference, not a technology blueprint.
