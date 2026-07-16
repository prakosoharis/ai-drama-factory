# AI Drama Factory

AI Drama Factory is an AI Production Operating System for planning, producing,
reviewing, editing, and reproducibly publishing audiovisual work.

It is a product and engine repository. The completed `project-film` V1
repository remains the historical creative-project baseline and must not be
refactored into V2.

## Current capability

V2.1-A provides a local, file-based Python metadata inspector and validator.
It loads project manifests, Shot Contracts, Render Plans, Render Jobs,
Candidates, Reviews, Selections, Cut Manifests, and Shot Packages. It does not
render, process media, migrate V1 assets, or assemble a film.

Python 3.9+ and the standard library are sufficient. No GPU, network access,
sudo, or third-party runtime dependency is required.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --editable .
drama inspect --project examples/v2.1-minimal-project
drama validate --project examples/v2.1-minimal-project --level structure
drama shot show shot-001 --project examples/v2.1-minimal-project
```

`--level files` also verifies referenced media existence and supplied SHA-256
checksums. The synthetic example deliberately fails that level because it has
no production media. See [V2.1-A core metadata](docs/implementation/V2.1-A-CORE-METADATA.md).

Create a native creative project with `drama project create <path> --project-id
<id> --name <name> --template minimal-drama`.

V2.1-D is complete for MVP: reviews, findings, human picture approval,
rejection, comparison, ROUGH_CUT selection, immutable candidate packages, and
file/checksum validation work. V2.2 Review and Selection Hardening is backlog
for concurrent allocation, full waiver edge cases, complex selection chains,
cycle detection, and expanded exhaustive tests. V2.1-E is next.

V2.1-E is COMPLETE — MVP: Cut Manifests explicitly place selected Candidates
on a timeline and deterministic mock assembly follows that manifest. V2.1-F is
next: Native V2 Pilot Production.

## Portal MVP

The Portal MVP adds a local FastAPI control plane and a Next.js web interface
for configured creative projects. It is intentionally a thin layer over the
file-based engine: human review, selection, validation, and mock assembly
continue to use the engine services. Run it with `docker compose --env-file
.env up --build` after setting `DRAMA_FACTORY_PILOT_PATH`; the pilot remains a
bind-mounted project and is never copied into an image. See
[Portal MVP](docs/implementation/PORTAL-MVP.md).

Creative Journey MVP is implemented pending approval. It gives non-technical
users a manual, documented path from Idea through Delivery; notes from friends,
research, and external AI tools can be pasted into the project without storing
any external credentials. Internal AI assistance remains deferred. See
[Creative Journey MVP](docs/implementation/CREATIVE-JOURNEY-MVP.md).

Start with the [master vision](docs/vision/MASTER-VISION.md),
[roadmap](docs/roadmap/ROADMAP.md), and [project context](PROJECT-CONTEXT.md).
