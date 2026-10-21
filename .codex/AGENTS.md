# Persistent project agent notes

## Available specialist agents

- `backend_dev` is defined in `.codex/agents/backend-dev.toml`. Use it for work in `app/` and FastAPI backend changes. Follow the project stack: SQLite in `app.db`; backend changes should include pytest coverage and be considered done after the full backend test suite passes.
- `frontend_dev` is defined in `.codex/agents/frontend-dev.toml`. Use it for work in `frontend/` and Vue changes. Keep the Vue structure organized into `api`, `assets`, `components`, `router`, `stores`, and `views`; use axios to call the backend directly. Include Jest coverage and finish after the full frontend test suite passes.

## Session continuity

These TOML agent definitions are the durable configuration for future Codex sessions. Spawn or select the relevant named agent again in each session; a running subagent instance itself does not persist across sessions. Keep project-wide instructions in the root `AGENTS.md` and specialist behavior in the corresponding TOML file.
