# Portal MVP

## Scope

Portal MVP is a local Docker Compose runtime containing a FastAPI control plane
and a Next.js App Router portal. It lists configured projects, exposes project
metadata and validation, shows shots, Candidates, and Cuts, and permits
explicit human approval, rejection, ROUGH_CUT selection, and mock assembly.
All write operations call the existing engine services; the portal does not
reimplement validation or lifecycle rules.

## Configuration and safety

Copy `.env.example` to `.env` and set `DRAMA_FACTORY_PILOT_PATH` to the local
creative project. Compose bind-mounts that path to `/projects/ai-drama-pilot`.
The API accepts only server-configured project IDs from
`DRAMA_FACTORY_PROJECTS`, and rejects configured paths outside
`DRAMA_FACTORY_PROJECT_ROOT`. Browser clients never provide filesystem paths.
CORS defaults to the local portal origin and does not use a wildcard.

The mount is writable because approved/rejected reviews, selections, and mock
assemblies are append-only project records. Use a copy of a creative project
when testing writes. No project data, V1 media, models, cache, credentials, or
generated assets are included in an image.

## Deferred

This MVP has no authentication or role management, database, queue, worker,
GPU execution, media proxy/streaming, image generation, production deployment,
or concurrency hardening. It is a local operator interface, not an internet
facing service.

## Run

```sh
cp .env.example .env
# edit DRAMA_FACTORY_PILOT_PATH
docker compose --env-file .env up --build
```

Open `http://localhost:3000`; health is available at
`http://localhost:8000/health`.
