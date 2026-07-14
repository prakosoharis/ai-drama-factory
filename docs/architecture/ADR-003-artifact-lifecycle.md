# ADR-003: Artifact Lifecycle

## Decision

Render execution, candidate review, and publishing are separate lifecycles.

| Artifact | States |
| --- | --- |
| Render Job | `QUEUED` → `RUNNING` → `SUCCEEDED` or `FAILED` |
| Candidate | `REVIEW_REQUIRED` → `PICTURE_APPROVED`, `REJECTED`, or `SUPERSEDED` |
| Publish | `SELECTED_FOR_CUT` → `SHOT_PACKAGE_APPROVED` → `PICTURE_LOCKED` → `DELIVERY_APPROVED` |

Candidates and published artifacts are immutable. A revision creates a new
candidate and preserves the provenance and review history of the old one.

## Consequences

Successful rendering does not imply creative approval, and picture approval
does not imply editorial selection or delivery approval.
