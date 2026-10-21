# 유료 글 판매와 구매 기록 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to execute this plan task-by-task.

**Goal:** 기존 공개 글 목록과 상세 읽기를 유지하며 작성자가 새 글을 유료로 등록하고 로그인한 독자가 구매 기록으로 전체 본문을 열람하게 한다.

**Architecture:** FastAPI가 작성자/구매자 권한을 JWT 쿠키와 SQLite 구매 기록으로 판정하며, 유료 글의 전체 본문을 서버 응답에서 제한한다. Vue는 기존 글 흐름에 판매 가격·미리보기·구매 화면을 더한다. 백엔드와 프런트엔드는 승인된 API 계약을 기준으로 별도 worktree에서 작업한다.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite, Pydantic, Vue 3, Jest, pytest.

**Spec:** `docs/superpowers/specs/2026-10-20-article-commerce-design.md`

## Global Constraints

- DB는 SQLite `app.db`를 사용한다.
- 기존 글 목록, 분야 필터, pagination, 상세 조회를 유지한다.
- 이번 구매는 결제 승인이나 실제 금전 이동 없이 구매 내역과 열람 권한만 기록한다.
- 기존 데이터에는 작성자 정보가 없으므로 기존 글은 무료로 유지한다.
- 백엔드는 전체 pytest, 프런트엔드는 전체 Jest와 production build를 확인한다.
- 각 에이전트는 별도 Git worktree를 사용한다. 현재 작업 트리의 기존 변경을 덮어쓰거나 stash하지 않는다.
- 기존 사용자 변경은 커밋하지 않는다. 각 worktree 내부에서 현재 상태를 기준 스냅샷으로 staging한 뒤, 구현 에이전트 변경만 소유 파일 기준으로 추출한다.

## Review Focus

- 만료·변조·잘못된 subject의 EN_AT 쿠키가 구매 권한을 얻지 못한다 — backend identity 테스트에서 잘못된 쿠키의 구매 요청이 401인지 고정한다.
- 기존 SQLite board 테이블을 마이그레이션해도 예전 게시글 본문과 분야가 보존되고 글은 무료로 읽힌다 — migration 테스트에서 확인한다.
- 가격이 0/음수이거나 미리보기가 공백인 유료 글 등록이 거부된다 — 작성 endpoint 테스트에서 422를 확인한다.
- 다른 사용자나 익명 독자는 유료 본문을 얻을 수 없고, 작성자와 구매자만 얻는다 — 상세 조회 테스트에서 세 역할을 구분한다.
- 중복 구매 요청으로 구매 기록이 중복되지 않는다 — purchase endpoint 테스트에서 재요청 결과와 행 수를 확인한다.

---

## Files and Ownership

- `app/api/dependencies.py`: 이메일/Kakao JWT를 검증해 현재 사용자 또는 익명 사용자를 제공한다.
- `app/core/security.py`: 기존 토큰 생성과 함께 검증 가능한 토큰 해독 함수를 제공한다.
- `app/models/board.py`: 작성자, 공개 미리보기, 가격을 저장한다.
- `app/models/purchase.py`: 구매자, 글, 구매 가격, 생성 시각과 unique 제약을 저장한다.
- `app/db/database.py`, `app/main.py`: 기존 board 열을 안전하게 보정하고 구매 모델을 생성한다.
- `app/schemas/board.py`, `app/schemas/purchase.py`: 글/구매 요청 및 응답 계약을 정의한다.
- `app/api/routers/board.py`, `app/api/routers/purchase.py`: 권한별 글 응답과 구매 기록 endpoint를 구현한다.
- `tests/test_article_sales.py`, `tests/test_article_migrations.py`: 권한, API, 기존 DB 호환성을 검증한다.
- `frontend/src/api.js`: 판매 등록 및 구매 API 호출 함수를 추가한다.
- `frontend/src/pages/PostCreatePage.vue`: 무료/유료 등록, 가격, 미리보기 입력을 제공한다.
- `frontend/src/pages/PostListPage.vue`, `frontend/src/pages/PostDetailPage.vue`: 판매 표시, 미리보기, 구매 및 권한별 본문 표시를 제공한다.
- `frontend/src/App.test.js`, `frontend/src/api.test.js`: 기존 목록/조회 회귀와 판매 흐름을 검증한다.
- `app/static/`: 최종 Vue 빌드에서 다시 생성한다. 프런트엔드 에이전트는 이 생성 산출물을 기능 변경으로 통합하지 않는다.

## Interfaces

- `get_current_user(db: Session = Depends(get_db), token: str | None = Cookie(alias="EN_AT")) -> User`: 토큰이 없거나 잘못되면 401.
- `get_optional_current_user(db: Session = Depends(get_db), token: str | None = Cookie(alias="EN_AT")) -> User | None`: 익명 요청은 `None`; 유효하지 않은 쿠키도 공개 읽기에서는 `None`으로 취급한다.
- 글 응답 필드: `idx`, `title`, `contents: str | None`, `category`, `author_name: str | None`, `preview: str | None`, `sale_price: int | None`, `is_for_sale`, `is_author`, `has_purchased`.
- `POST /api/purchases` 요청 `{ "board_idx": int }`; 응답 `{ "id": int, "board_idx": int, "price": int, "created_at": datetime }`.
- 프런트 호출: `api.createNote(note)`, `api.listNotes(offset, limit, category)`, `api.getNote(idx)`, `api.purchaseNote(boardIdx)`.
- 목록과 상세 조회는 기존 경로를 유지한다. 상세 유료 본문은 공개 미리보기만으로 응답되며, 작성자/구매자에게만 `contents` 전체를 반환한다.

## Task 1: Create isolated worktrees from the current workspace snapshot

**Owner:** Orchestrator. **Files:** no product files; worktrees under `%TEMP%/backend_2-paid-article-worktrees/backend` and `%TEMP%/backend_2-paid-article-worktrees/frontend`.

- [ ] **Step 1: Capture the current baseline without changing the main index**

Record `git status --short`, `git diff HEAD --binary`, and all relevant untracked project files. Do not copy `.env` or other local secrets; do not stash, reset, clean, commit, or move files in the main workspace.

- [ ] **Step 2: Add two worktrees on separate branches**

Create branches `feature/backend-article-sales` and `feature/frontend-article-sales` from the current `main` HEAD in the two paths above. The temporary path avoids modifying the user's already-dirty `.gitignore`.

- [ ] **Step 3: Apply the same current workspace snapshot to each worktree**

Apply the captured tracked diff and copy relevant untracked project files (including current root `AGENTS.md`, tests, `postman/`, and the approved spec) while excluding `.env`, caches, `.venv`, `node_modules`, and build caches. Verify both worktrees begin with matching owned source and tests.

- [ ] **Step 4: Stage only each worktree's baseline snapshot**

In each worktree, stage the copied baseline locally so subsequent unstaged and untracked changes represent only that agent's implementation. Do not commit the baseline or implementation.

- [ ] **Step 5: Reuse installed local tool dependencies**

Create a `.venv` directory junction in each worktree to the verified main workspace `.venv`, and a `frontend/node_modules` junction to the verified main workspace `frontend/node_modules`. Do not install or download dependencies. The backend test DB and frontend build output must stay inside their own worktrees.

- [ ] **Step 6: Verify isolation**

Run `git worktree list` and `git status --short` from the main workspace and both worktrees. Confirm the original workspace status and files are unchanged.

- [ ] **Step 7: Run the clean baseline suites**

Run `pytest` from the backend worktree and `npm test -- --runInBand` from `frontend/` in the frontend worktree. Record any pre-existing failures before implementation; do not proceed past a failure without identifying its test and output.

## Task 2: Add identity resolution and sale schema migration

**Owner:** `backend_dev`, in `%TEMP%/backend_2-paid-article-worktrees/backend`.

**Files:** Modify `app/core/security.py`, `app/db/database.py`, `app/main.py`, `app/models/board.py`; Create `app/api/dependencies.py`, `app/models/purchase.py`, `tests/test_article_migrations.py`.

**Interfaces:** Produces `get_current_user`, `get_optional_current_user`, `Board.author_idx`, `Board.preview`, `Board.sale_price`, and `Purchase` for Task 3.

- [ ] **Step 1: Write failing identity and migration tests**

Add `test_current_user_resolves_email_and_kakao_subjects`, `test_current_user_rejects_invalid_or_expired_token`, `test_optional_current_user_returns_none_for_anonymous_request`, and `test_legacy_board_migration_preserves_posts_as_free`. Assert email and Kakao cookie subjects resolve to their existing `User`, invalid/expired credentials return 401 on required auth, and old rows retain title/content/category with null author/preview/price.

- [ ] **Step 2: Run those tests and confirm expected failures**

Run `pytest tests/test_article_migrations.py -q`. Expected: failures because identity dependencies and sale columns do not exist yet.

- [ ] **Step 3: Implement token decoding and current-user dependencies**

Decode `EN_AT` with `settings.SECRET_KEY` and `settings.ALGORITHM`; resolve normal subjects by email and `kakao:<id>` subjects by `User.kakao_user_id`. Do not expose token values in errors.

- [ ] **Step 4: Implement additive Board and Purchase models/migration**

Add nullable `author_idx`, `preview`, `sale_price` columns and an idempotent SQLite migration; add a Purchase model with `buyer_idx`, `board_idx`, `price`, `created_at`, foreign keys, and unique `(buyer_idx, board_idx)`. Ensure `app.main` imports the model and runs migration before serving.

Migration interface: `ensure_board_sale_columns(bind=engine) -> None`.

- [ ] **Step 5: Run migration and identity tests**

Run `pytest tests/test_article_migrations.py -q`. Expected: all tests pass, including preserving old rows.

## Task 3: Implement paid article and purchase API contract

**Owner:** `backend_dev`, same backend worktree.

**Files:** Modify `app/api/routers/board.py`, `app/schemas/board.py`, `app/main.py`; Create `app/api/routers/purchase.py`, `app/schemas/purchase.py`, `tests/test_article_sales.py`.

**Interfaces:** Consumes Task 2 identity/model interfaces. Produces the exact board response fields and `POST /api/purchases` response specified above.

- [ ] **Step 1: Write failing contract tests**

Add `test_free_article_list_and_detail_remain_public`, `test_paid_article_requires_positive_price_and_nonblank_preview`, `test_paid_article_requires_login_and_sets_author_from_cookie`, `test_unpurchased_reader_gets_preview_but_not_contents`, `test_author_and_buyer_get_full_contents`, `test_purchase_is_idempotent_and_unlocks_contents`, `test_author_cannot_purchase_own_article`, and `test_free_or_missing_article_cannot_be_purchased`. Assert legacy list/category/pagination behavior, 422 validation, 401 auth, 409 self/free purchase, 404 missing post, and exact field values.

- [ ] **Step 2: Run the contract tests and confirm expected failures**

Run `pytest tests/test_article_sales.py -q`. Expected: new request fields, response fields, and purchase route are missing.

- [ ] **Step 3: Extend Board request/response schemas and existing routes**

Keep anonymous free writing and existing list parameters. Accept optional `sale_price` and `preview`; require both valid values and current user when a positive price is supplied. Compute identity and purchase entitlement server-side and never return a locked full body.

- [ ] **Step 4: Implement purchase route and OpenAPI descriptions**

Implement `POST /api/purchases` with authentication, missing/free/self-purchase errors, stored `price`, and duplicate-safe unique constraint handling. Document auth, response, error codes, and that the operation does not charge money in FastAPI route/schema descriptions.

- [ ] **Step 5: Run focused backend tests**

Run `pytest tests/test_article_sales.py tests/test_article_migrations.py -q`. Expected: all new contract cases pass.

- [ ] **Step 6: Run the full backend suite in the backend worktree**

Run `pytest`. Expected: all existing and new backend tests pass.

## Task 4: Implement Vue article sales and purchase flow

**Owner:** `frontend_dev`, in `%TEMP%/backend_2-paid-article-worktrees/frontend`. This may run in parallel with Task 2/3 because the spec fixes the API contract.

**Files:** Modify `frontend/src/api.js`, `frontend/src/api.test.js`, `frontend/src/pages/PostCreatePage.vue`, `frontend/src/pages/PostListPage.vue`, `frontend/src/pages/PostDetailPage.vue`, `frontend/src/App.test.js`.

**Interfaces:** Consume the exact API fields and status behavior in this plan. Do not change backend response names. Do not include generated `app/static/` assets in implementation changes.

- [ ] **Step 1: Write failing API helper tests**

Add tests that `api.createNote` sends `sale_price` and `preview` unchanged and `api.purchaseNote(boardIdx)` POSTs `{ board_idx: boardIdx }` to `/api/purchases` with same-origin credentials.

- [ ] **Step 2: Run the focused Jest API tests and confirm expected failures**

Run `npm test -- --runInBand src/api.test.js` from `frontend/`. Expected: `purchaseNote` is not defined and paid fields are not yet exercised by the form.

- [ ] **Step 3: Add the API purchase helper and paid authoring form**

Add `purchaseNote`; add a free/paid control, positive price input and required preview for paid posts. Submit paid fields only when paid mode is selected; retain the existing free post payload and navigation.

- [ ] **Step 4: Write failing page-flow tests**

Add Jest cases for paid list rows showing preview and price; locked detail showing preview and purchase CTA without contents; successful purchase reloading detail and showing the full contents; author/buyer hiding the purchase CTA; and 401/409 errors displayed accessibly. Keep existing free list/category/pagination/detail tests.

- [ ] **Step 5: Run focused page tests and confirm expected failures**

Run `npm test -- --runInBand src/App.test.js`. Expected: paid list/detail and purchase interactions are absent.

- [ ] **Step 6: Implement paid list/detail display and purchase interaction**

Render the server-returned role flags and never infer access from local state. After a successful `purchaseNote`, call `api.getNote(idx)` again. For 401, provide a login path; preserve errors and retry affordances.

- [ ] **Step 7: Run full frontend Jest and build in the frontend worktree**

Run `npm test -- --runInBand` and `npm run build` from `frontend/`. Expected: all tests pass and production build succeeds. Keep build artifacts local to the frontend worktree.

## Task 5: Integrate owned changes and verify both suites

**Owner:** Orchestrator in the original workspace after both agents report completion.

**Files:** Only integrate backend-owned changes from `%TEMP%/backend_2-paid-article-worktrees/backend` and frontend source/test changes from `%TEMP%/backend_2-paid-article-worktrees/frontend`; regenerate `app/static/` from the integrated frontend source.

- [ ] **Step 1: Review each agent's worktree diff against its staged baseline**

Check the changed file list and diff. Reject unrelated changes, ensure the frontend uses the backend contract, and ensure no copied baseline changes are treated as new implementation.

- [ ] **Step 2: Apply only feature diffs to the original workspace**

Apply backend `app/` and `tests/` changes and frontend `frontend/src/` changes separately. Do not overwrite other pre-existing workspace changes.

- [ ] **Step 3: Run the full integrated backend suite**

Run `pytest` from the original workspace. Expected: all backend tests pass.

- [ ] **Step 4: Run the full integrated frontend suite and production build**

Run `npm test -- --runInBand` and `npm run build` from `frontend/`. Expected: all frontend tests pass and build succeeds.

- [ ] **Step 5: Verify API docs and shipped frontend assets**

Run the app's OpenAPI generation/read check and verify `app/static/index.html` references the newly built frontend assets. Confirm `git status --short` still includes pre-existing user changes and no worktree baseline was copied over them.
