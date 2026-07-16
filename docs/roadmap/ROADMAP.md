# Roadmap

The master vision is stable direction; versions are capability increments;
milestones are scoped outcomes within a version. No dates are implied. A
version activates only when its production or technology trigger is met.

| Version | Status / milestone | Focus | Technology dependency | Exit criteria |
| --- | --- | --- | --- | --- |
| V1 | Archived — End-to-End Proof | Historical proof of end-to-end production | Wan2.2, Vast.ai, audio and FFmpeg workflows | Archived baseline tag exists |
| V2 | Shot-Centric Production System | Shot Contract, Render Plan, selective rendering, immutable candidates, review ledger, candidate selection, Cut Manifest, reproducible assembly, shot-synchronous audio | Structured metadata and reproducible local execution | A single shot can be revised and cut in without rerendering unrelated shots |
| V3 | Character and Continuity | Character Registry, Scene Contract, intended/observed state, Continuity Graph, warnings | Reliable structured character and scene data | Continuity conflicts are detected before publish |
| V4 | Renderer Architecture | Model-specific compiler, renderer adapter, standard candidate output, escape hatch, capability registry | At least two renderer capabilities worth normalizing | A renderer can be replaced without changing production workflow |
| V5 | Benchmark and Champion-Challenger | Golden benchmark, raw and finished-sequence comparison, cost per approved second | Comparable runs, cost capture, stable benchmark assets | Model promotion is evidence-based |
| V6 | AI-Assisted Planning and Review | Planning Assistant, Review Critic, timecoded findings, human waiver, revision suggestions | Sufficient evaluation quality and review data | Assistants improve review without displacing human authority |
| V7 | Knowledge System | Observations, hypotheses, experiments, results, validated playbooks | Repeated production and research evidence | Validated learning is reusable across productions |
| V8 | Production Control Plane | Dashboard, review UI, A/B comparison, approval workflow, cost visibility | Proven manual workflow and stable data contracts | Teams can manage production state safely |
| V9 | Scalable Rendering | Job queue, multi-worker, persistent cache, recovery, budget guardrails | Proven throughput bottleneck and safe orchestration | Scaling improves throughput with controlled cost and recovery |
| V10 | Semi-Autonomous Creative Studio | Brief-to-plan, screenplay, storyboard, animatic, render planning, review queue, editorial, delivery assets | Mature validated capabilities from earlier versions | End-to-end plans remain reviewable, reproducible, and human-approved |

## V2.1 delivery sequence

1. **V2.1-A — Core Metadata and Validation** (complete)
2. **V2.1-B — New Project Bootstrap** (complete)
3. **V2.1-C — Single-Shot Candidate Workflow** (complete)
4. **V2.1-D — Review and Candidate Selection** (COMPLETE — MVP)
5. **V2.1-E — Cut Manifest and Reproducible Assembly** (COMPLETE — MVP)
6. **V2.1-F — New Native V2 Pilot Production** (next)
7. **V2.1-G — Optional V1 Baseline Import**

## V2.2 backlog: Review and Selection Hardening

- Concurrent Review and Selection allocation.
- Full waiver edge-case coverage.
- Complex Selection supersession validation and cycle detection.
- Expanded exhaustive test coverage.
- Picture-lock lifecycle, concurrent Cut allocation, complex timeline editing,
  transition handling, recovery hardening, and real-media conform edge cases.

The native V2 pilot uses a new clean creative project. `project-film` remains
an archived baseline and optional migration test, not a required test fixture.

## Activation triggers

**Production trigger:** a real production bottleneck has occurred and the
proposed capability removes it safely.

**Technology trigger:** the necessary capability has become sufficiently
mature, reliable, and affordable to justify adoption.
# Portal MVP — Implemented pending runtime approval

The local Portal MVP provides a Docker Compose runtime, FastAPI control plane,
and Next.js interface for configured projects. It is a product-surface slice,
not a replacement for the file-based engine. Authentication, multi-user
authorization, queues, media playback, real render orchestration, and hosted
deployment remain backlog items.

# Creative Journey MVP — Implemented pending approval

The Journey adds human-friendly, file-backed development and pre-production
stages, discussion notes, and explicit Shot Plan-to-Production handoff. It does
not add an internal AI assistant, database, real-time collaboration, or media
generation; internal AI assistance is deferred.
