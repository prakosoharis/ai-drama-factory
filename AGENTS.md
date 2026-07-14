# Agent Rules

- Inspect before modifying.
- Show a plan before structural changes.
- Never overwrite candidates.
- Never silently change published artifacts.
- Never delete production assets.
- Do not install dependencies without approval.
- Do not run GPU workloads without approval.
- Do not commit secrets, credentials, model weights, or caches.
- Preserve provenance for every asset, job, candidate, review, and publish decision.
- Keep model-specific logic inside `adapters/`.
- A prompt is never the canonical source of truth; approved structured production data is.
- Prefer simple implementation until a real bottleneck requires complexity.
- Update `PROJECT-CONTEXT.md` after major architecture decisions.
