# ADR-001: System Boundaries

## Decision

The system is separated into three planes.

### Control Plane

Owns projects, workflows, approval, policy, cost, and review.

### Production Data Plane

Owns assets, render jobs, candidates, editorial, audio, mastering, and
delivery.

### Knowledge Plane

Owns observations, experiments, playbooks, benchmarks, and technology watch.

## Shared foundations

All planes use an Asset Registry, Provenance Ledger, Dependency Graph,
Versioning, Review Ledger, and Cut Manifest. These foundations connect
decisions to artifacts without merging research exploration into production
state.

## Consequences

Production can remain stable while research evaluates technologies, and a
renderer can change without becoming the system boundary.
