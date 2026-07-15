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

Current milestone: **V2.1 — Flexible Shot Revision**.

Target: Shot 11 can be rendered again as a new candidate, compared, selected,
and inserted into the film without rendering any other shot again.

V2.1-A now provides file-based project discovery, metadata loading, structural
and file-level validation, and read-only inspection for synthetic projects.
Rendering, review mutation, selection mutation, assembly, and V1 migration
remain deferred.

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
