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

Start with the [master vision](docs/vision/MASTER-VISION.md),
[roadmap](docs/roadmap/ROADMAP.md), and [project context](PROJECT-CONTEXT.md).
