# Creative Journey MVP

The Creative Journey makes the portal a structured production workspace rather
than a technical metadata viewer. It supports manual material from friends,
meetings, research, and external AI tools; there is no internal AI integration
or credential storage.

The stages are Idea, Creative Brief, Story, Screenplay, Scene Breakdown, Shot
Planning, Storyboard, Production, Post-production, and Delivery. Development
documents are file-backed under `project/development` and pre-production
documents under `project/preproduction`. Each document records revision, source,
approval state, timestamps, and human-authored content.

An approved Shot Plan can explicitly hand off to engine-compatible Shot
Contracts. The handoff records the source plan revision and approver, validates
the result, and refuses to overwrite an existing contract without explicit
confirmation; the old contract is retained in project history.

The Cut Manifest remains the system record for editorial instructions. The
portal presents it as a visual timeline, with raw JSON contained in Technical
Details. Text mock assemblies are clearly labelled workflow validation
artifacts, not video.

Creative Journey MVP is **IMPLEMENTED PENDING APPROVAL**. Deferred: internal
AI assistant, automatic writing or breakdown, collaboration, authentication,
database, realtime sync, image/video generation, nonlinear editing, and cloud
deployment.
