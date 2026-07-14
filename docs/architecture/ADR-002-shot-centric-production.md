# ADR-002: Shot-Centric Production

## Decision

A shot is the primary production unit. A film is a dependency graph, not a
conveyor belt.

Storyboard, previs, and animatic precede expensive GPU inference. A revision
to one shot must not require rendering the entire film again. An approved
candidate is not automatically selected for the cut. Picture lock is a
timeline-level decision, recorded through the Cut Manifest.

## Consequences

The system must keep shot contracts, candidates, review decisions, and cut
selection distinct. It optimizes for selective revision and sequence quality,
not only for batch completion.
