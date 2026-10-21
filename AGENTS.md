# 기술 스택
frontend 폴더에 vue 프로젝트로 프론트엔드 개발
app 폴더에 fastapi 프로젝트로 백엔드 개발
DB는 SQLlite로 app.db 파일로 관리

# 검증
백엔드는 pytest로 테스트할 수 있는 테스트 코드 작성 후 전체 통과되면 완료
프론트엔드는 jest로 테스트할 수 있는 테스트 코드 작성 후 전체 통과되면 완료

# Persistent project agent notes

## Available specialist agents

- `backend_dev` is defined in `.codex/agents/backend-dev.toml`. Use it for work in `app/` and FastAPI backend changes. Follow the project stack: SQLite in `app.db`; backend changes should include pytest coverage and be considered done after the full backend test suite passes.
- `frontend_dev` is defined in `.codex/agents/frontend-dev.toml`. Use it for work in `frontend/` and Vue changes. Keep the Vue structure organized into `api`, `assets`, `components`, `router`, `stores`, and `views`; use axios to call the backend directly. Include Jest coverage and finish after the full frontend test suite passes.

## Session continuity

These TOML agent definitions are the durable configuration for future Codex sessions. Spawn or select the relevant named agent again in each session; a running subagent instance itself does not persist across sessions. Keep project-wide instructions in the root `AGENTS.md` and specialist behavior in the corresponding TOML file.




