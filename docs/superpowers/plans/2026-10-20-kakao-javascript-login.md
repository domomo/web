# 카카오 JavaScript SDK 로그인 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vue의 카카오 로그인 버튼으로 닉네임 기반 로컬 계정을 만들거나 로그인하고, 기존 EN_AT 쿠키를 발급한다.

**Architecture:** Vue는 Kakao JavaScript SDK v2 `Kakao.Auth.authorize()`를 `profile_nickname` 범위로 호출한다. FastAPI는 state 쿠키 검증, 코드/토큰 교환, 사용자 확인과 로컬 계정 처리를 맡는다. SQLAlchemy User 스키마는 기존 로컬 계정을 보존하며 카카오 식별자를 추가한다.

**Tech Stack:** Vue 3, Vite, Jest, FastAPI, SQLAlchemy, SQLite, pytest, HTTPX, Kakao JavaScript SDK v2.

**Spec:** [docs/superpowers/specs/2026-10-20-kakao-javascript-login-design.md](../specs/2026-10-20-kakao-javascript-login-design.md)

## Global Constraints

- 프런트엔드는 `frontend`의 Vue 프로젝트, 백엔드는 `app`의 FastAPI 프로젝트, DB는 SQLite를 사용한다.
- 카카오 로그인은 JavaScript SDK v2의 `Kakao.Auth.authorize()`와 `profile_nickname` 범위를 사용한다.
- 카카오에서 저장하는 프로필 정보는 회원번호와 닉네임뿐이다. 이메일은 요청·저장·비교하지 않는다.
- 이메일을 근거로 기존 로컬 계정에 자동 연결하지 않고, 추가 소셜 제공자나 연결 해제 기능을 넣지 않는다.
- 기존 이메일·비밀번호 가입/로그인은 계속 동작하고, 로그인 쿠키 이름은 `EN_AT`이다.
- 카카오 사용자는 `email=None`, `password=None`, 닉네임을 `name`으로 저장한다.
- 개발 콜백 URI는 `http://localhost:8000/api/user/kakao/callback`이다.
- 전체 백엔드 검증은 `pytest`, 전체 프런트엔드 검증은 `npm test -- --runInBand`이며 프런트엔드 빌드는 `npm run build`다.
- HTTPX는 이미 설치되어 있으므로 OAuth HTTP 요청을 위해 새 런타임 의존성을 추가하지 않는다.
- `app/main.py`와 `app/db/database.py`에는 게시글 카테고리 지원을 위한 기존 미커밋 변경이 있다. 이를 보존하면서 필요한 초기화 코드를 병합하고, 해당 변경을 이 기능 커밋에 포함하지 않는다.

## Review Focus

- 구형 SQLite `user` 테이블에서 재작성 도중 오류가 나도 기존 계정 행과 스키마가 보존되는지 — Task 1의 `test_user_schema_migration_rolls_back_without_losing_existing_users`.
- state 쿠키와 콜백 state가 누락·불일치·재사용되는 요청이 거절되는지 — Task 2의 `test_kakao_callback_rejects_missing_or_mismatched_state` 및 `test_kakao_state_is_single_use`.
- 토큰 교환·사용자 조회의 시간 초과, 비정상 HTTP 응답, 닉네임 미제공이 로그인 실패로 처리되는지 — Task 2의 `test_kakao_provider_errors_are_normalized` 및 `test_kakao_callback_rejects_missing_nickname`.
- 같은 카카오 회원번호의 동시 최초 로그인이 unique 위반 뒤에도 하나의 계정으로 수렴하는지 — Task 2의 `test_concurrent_first_kakao_login_reuses_unique_account`.
- 키 누락, SDK 로드 실패, 사용자 취소가 화면 오류로 전달되고 로컬 로그인은 유지되는지 — Task 3의 `test_kakao_login_reports_sdk_and_configuration_errors`, `test_kakao_login_cancel_shows_message`, 기존 로컬 로그인 회귀 테스트.

---

## File Structure

- Modify `app/models/user.py`: 로컬 자격 증명을 nullable로 바꾸고 `kakao_user_id` unique 열을 선언한다.
- Modify `app/db/database.py`: 기존 SQLite User 테이블을 안전하게 새 스키마로 재작성한다.
- Modify `app/main.py`: 기존 게시글 카테고리 마이그레이션을 보존하고 User 마이그레이션을 시작 시 호출한다.
- Modify `app/core/config.py`: Kakao REST API 키, 클라이언트 시크릿, 콜백 URI 설정을 선언한다.
- Create `app/services/kakao.py`: Kakao 코드 교환과 닉네임 조회를 한 서비스로 격리한다.
- Modify `app/schemas/user.py` and `app/api/routers/user.py`: state 응답 및 카카오 OAuth 시작/콜백 계약을 구현한다.
- Create `tests/test_user_schema_migration.py`: 새/기존 SQLite 스키마와 데이터 보존을 검증한다.
- Create `tests/test_kakao_auth.py`: OAuth 서비스, state, callback, 쿠키, 리다이렉트를 검증한다.
- Create `postman/mocks/kakao/` and `postman/simulations/kakao-dev.sim.yaml`: 실제 Kakao REST 호출 형태로 로컬 HTTP 시뮬레이션을 제공한다.
- Modify `frontend/index.html`: SDK v2를 고정 버전 및 공식 SRI와 함께 로드하고 Vite 공개 JavaScript 키를 HTML 메타데이터로 제공한다.
- Create `frontend/src/kakao.js` and `frontend/src/kakao.test.js`: SDK 초기화와 authorize 호출을 격리·검증한다.
- Modify `frontend/src/api.js`, `frontend/src/api.test.js`, `frontend/src/pages/LoginPage.vue`, `frontend/src/App.test.js`: state API, 카카오 버튼/오류, 기존 로컬 로그인 회귀를 반영한다.
- Modify `frontend/src/style.css` only if existing button styles do not meet the login layout.
- Create `.env.example`, `frontend/.env.example`, and `docs/kakao-login-setup.md`: 필요한 변수와 개발자 콘솔 설정을 기록한다. 실제 시크릿은 커밋하지 않는다.

## Task 1: User 모델과 SQLite 마이그레이션

**Files:**
- Modify: `app/models/user.py`
- Modify: `app/db/database.py`
- Modify: `app/main.py`
- Create: `tests/test_user_schema_migration.py`

**Interfaces:**
- Produces `ensure_user_kakao_schema(bind: Engine = engine) -> None`.
- `User.email: Mapped[str | None]`, `User.password: Mapped[str | None]`, and `User.kakao_user_id: Mapped[str | None]` with a unique constraint.
- Existing `idx`, email, password, and name values survive migration unchanged.

- [x] **Step 1: Write the failing legacy migration test**

`test_user_schema_migration_preserves_existing_local_account` creates the original four-column SQLite table, inserts an account, runs the migration, then asserts its values are unchanged and that email/password are nullable while `kakao_user_id` exists and is nullable.

- [x] **Step 2: Run the migration test and verify it fails**

Run: `pytest tests/test_user_schema_migration.py::test_user_schema_migration_preserves_existing_local_account -v`
Expected: FAIL because `ensure_user_kakao_schema` and `kakao_user_id` do not exist.

- [x] **Step 3: Implement the nullable User schema and migration**

Rebuild only the `user` table inside a transaction when its columns/nullability differ from the target schema. Copy the four legacy columns, create the unique nullable Kakao ID column, and leave an already-current table untouched. Call the migration from `app/main.py` after `Base.metadata.create_all` without removing `ensure_board_category_column(engine)`.

- [x] **Step 4: Add fresh-schema, uniqueness, and rollback tests**

Add `test_new_user_schema_accepts_kakao_user_without_credentials` asserting a row with null email/password persists; `test_user_schema_enforces_unique_kakao_user_id` asserting a duplicate provider ID fails; and `test_user_schema_migration_rolls_back_without_losing_existing_users`, which injects a SQLite `before_cursor_execute` error on the new-table creation after the legacy table rename and asserts rollback restores the original table and row.

- [x] **Step 5: Run the targeted migration tests**

Run: `pytest tests/test_user_schema_migration.py -v`
Expected: all four migration/schema tests PASS.

- [ ] **Step 6: Commit the isolated database change**

Commit only `app/models/user.py`, `app/db/database.py`, `app/main.py`, and `tests/test_user_schema_migration.py` with message `feat: support Kakao identities in users`.

## Task 2: FastAPI Kakao OAuth contract and callback

**Files:**
- Modify: `app/core/config.py`
- Create: `app/services/kakao.py`
- Modify: `app/schemas/user.py`
- Modify: `app/api/routers/user.py`
- Create: `tests/test_kakao_auth.py`

**Interfaces:**
- `KakaoProfile(user_id: str, nickname: str)` contains no email field.
- `KakaoOAuthClient.user_from_code(code: str) -> KakaoProfile` exchanges the code at `https://kauth.kakao.com/oauth/token`, then requests `/v2/user/me` using `property_keys=["kakao_account.profile"]`.
- `GET /api/user/kakao/state` returns `{state, redirect_uri}` and sets `kakao_oauth_state` (HttpOnly, SameSite=Lax, 300-second lifetime, callback-only path).
- `GET /api/user/kakao/callback` validates state, creates or reuses a local user, sets `EN_AT`, and redirects to `/posts`; errors redirect to `/login` with a fixed `oauth_error` value.
- `KAKAO_REST_API_KEY`, `KAKAO_CLIENT_SECRET`, and `KAKAO_REDIRECT_URI` are backend settings. Provider HTTP calls use an injectable `httpx.Client` with a 10-second timeout.

- [x] **Step 1: Write the failing Kakao service tests**

Add `test_kakao_oauth_client_exchanges_code_and_reads_only_nickname` asserting the token request form and Kakao user request scope, and `test_kakao_provider_errors_are_normalized` covering timeout, non-2xx, malformed JSON, and missing user ID/nickname.

- [x] **Step 2: Run the service tests and verify they fail**

Run: `pytest tests/test_kakao_auth.py -k 'oauth_client or provider_errors' -v`
Expected: FAIL because the client and profile schema do not exist.

- [x] **Step 3: Implement settings and the Kakao OAuth client**

Add optional Kakao settings and a `KakaoOAuthClient` that posts form data with the REST API key and configured client secret, reads the access token, and performs the authenticated user lookup. Return only Kakao member ID and nickname; convert provider/network/parse errors to one typed service error.

- [x] **Step 4: Write the failing route tests**

Add `test_kakao_state_sets_short_lived_http_only_cookie`, `test_kakao_callback_creates_nickname_only_user_and_sets_en_at`, `test_kakao_callback_reuses_existing_kakao_user`, `test_kakao_callback_rejects_missing_or_mismatched_state`, `test_kakao_state_is_single_use`, `test_kakao_callback_rejects_missing_nickname`, `test_kakao_callback_handles_provider_cancel_and_failure`, `test_kakao_callback_handles_database_error_safely`, and `test_concurrent_first_kakao_login_reuses_unique_account`.

Assertions cover the response state/redirect URI, cookie flags and clearing, persisted `email is None` and `password is None`, no email-based local-account lookup/link, `EN_AT`, redirect destination, safe fixed errors, and idempotent unique-ID handling.

- [x] **Step 5: Run route tests and verify they fail**

Run: `pytest tests/test_kakao_auth.py -k 'state or callback or concurrent' -v`
Expected: FAIL because the state and callback routes are absent.

- [x] **Step 6: Implement state and callback routes**

Generate state with `secrets.token_urlsafe(32)` and compare with `secrets.compare_digest`. Clear the state cookie on every callback outcome. Use one transaction to create a Kakao-only user; on `IntegrityError`, roll back, reload by Kakao ID, and continue with that row. Use `createToken(f"kakao:{profile.user_id}")` for the existing `EN_AT` cookie without changing local-login token subjects.

- [x] **Step 7: Run backend auth tests and inspect generated OpenAPI**

Run: `pytest tests/test_kakao_auth.py tests/test_user_schema_migration.py -v`
Expected: all targeted tests PASS. Confirm `/openapi.json` describes the state endpoint and the callback query/error behavior.

- [ ] **Step 8: Commit the backend OAuth change**

Commit only the backend settings/service/schema/router and the two auth test files with message `feat: add Kakao OAuth callback`.

## Task 3: Vue Kakao SDK login button

**Files:**
- Modify: `frontend/index.html`
- Create: `frontend/src/kakao.js`
- Create: `frontend/src/kakao.test.js`
- Modify: `frontend/src/api.js`
- Modify: `frontend/src/api.test.js`
- Modify: `frontend/src/pages/LoginPage.vue`
- Modify: `frontend/src/App.test.js`
- Modify: `frontend/src/style.css` only if required by the existing auth layout.

**Interfaces:**
- `getKakaoSdk() -> KakaoSdk` reads the injected JavaScript key and initializes the global SDK once.
- `api.getKakaoLoginState() -> Promise<{state: string, redirect_uri: string}>` calls `GET /api/user/kakao/state` with same-origin credentials.
- The login button calls `Kakao.Auth.authorize({redirectUri, scope: "profile_nickname", state})` after the state request succeeds.

- [x] **Step 1: Write the failing SDK and API client tests**

Add `test_kakao_sdk_initializes_once_with_public_key`, `test_kakao_sdk_reports_missing_key_or_script`, and an API contract test asserting the exact GET path, same-origin credentials, and returned state object.

- [x] **Step 2: Run frontend tests and verify the new tests fail**

Run: `npm test -- --runInBand --runTestsByPath src/kakao.test.js src/api.test.js` (`frontend` directory)
Expected: FAIL because the Kakao SDK wrapper and state API method do not exist.

- [x] **Step 3: Load and wrap the official Kakao JavaScript SDK**

Add the latest stable v2 URL and matching SRI copied from Kakao's official SDK download page to `frontend/index.html`; inject only `VITE_KAKAO_JS_KEY` as public HTML metadata. Implement `getKakaoSdk()` to reject absent SDK/key and initialize only once.

- [x] **Step 4: Add the state API method and contract test**

Implement `api.getKakaoLoginState()` in `frontend/src/api.js` and assert exact request behavior in `frontend/src/api.test.js`.

- [x] **Step 5: Write the failing login component tests**

Add component tests for Kakao button authorizing with `profile_nickname` and server state, SDK/state failures shown with `role="alert"`, Kakao cancellation query messaging, and the existing email/password login flow still navigating to posts.

- [x] **Step 6: Run the login tests and verify they fail**

Run: `npm test -- --runInBand --runTestsByPath src/App.test.js` (`frontend` directory)
Expected: FAIL because the login page has no Kakao button or OAuth error handling.

- [x] **Step 7: Implement the login button and accessible error states**

Add a Kakao login button to `LoginPage.vue`. On click, disable while pending, fetch state, initialize the SDK, and call `authorize`. Render fixed Korean messages for cancellation and failures without exposing provider detail. Preserve the existing local form and navigation notice.

- [ ] **Step 8: Run all frontend tests and commit**

Run: `npm test -- --runInBand` (`frontend` directory)
Expected: all Jest tests PASS. Commit only frontend source/tests with message `feat: add Kakao login to Vue`.

## Task 4: Kakao app and local configuration

**Files:**
- Create: `.env.example`
- Create: `frontend/.env.example`
- Create: `docs/kakao-login-setup.md`
- External configuration: Kakao Developers app `mlops` (app ID 1614699), explicitly selected by the user.

**Interfaces:**
- Root environment example documents REST API key, client secret, and callback URI.
- Frontend environment example documents the public JavaScript key only.
- Setup instructions name the exact local origins and callback URI.

- [x] **Step 1: Document the configuration variables and local run order**

Create examples with empty credential values and `KAKAO_REDIRECT_URI=http://localhost:8000/api/user/kakao/callback`; create frontend example with `VITE_KAKAO_JS_KEY=`. State that actual `.env` files are ignored and secret values must not be committed.

- [x] **Step 2: Configure Kakao Developers with Chrome DevTools**

In app `mlops`, enable Kakao Login; set `profile_nickname` as the only required consent item; register JavaScript SDK domains `http://localhost:5173` and `http://localhost:8000`; register exact callback `http://localhost:8000/api/user/kakao/callback`. Confirm each saved value in the console after saving. Do not add email consent or an inferred production domain.

- [x] **Step 3: Add only the public JavaScript key to the local frontend environment**

Read the app's JavaScript key from the console and write it to ignored `frontend/.env.local` as `VITE_KAKAO_JS_KEY`; do not print it in the terminal or add it to Git. Keep REST API key/client secret server-side in ignored root `.env`.

- [x] **Step 4: Document console paths, values, and email limitation**

Create `docs/kakao-login-setup.md` with the Kakao console navigation, local domains/callback, env variable names, start commands, verification steps, and an explicit note that email duplicate rejection is unavailable because email is not requested.

- [ ] **Step 5: Review local configuration without exposing secrets**

Confirm both required server variables are present by checking variable names only, confirm frontend key is present without echoing its value, and confirm the saved Kakao console settings. If the client secret is not available in the app, stop the live-credential check and report the missing variable without weakening Kakao's client-secret setting.

- [ ] **Step 6: Commit only examples and setup documentation**

Commit `.env.example`, `frontend/.env.example`, and `docs/kakao-login-setup.md` with message `docs: explain Kakao login setup`. Never stage `.env` or `frontend/.env.local`.

## Task 5: Final integration verification

**Files:**
- No product files unless a failure requires a focused fix in its owning task.

- [x] **Step 1: Run all backend tests**

Run: `pytest`
Expected: all tests PASS, including existing board category and frontend route tests.

- [x] **Step 2: Run all frontend Jest tests**

Run: `npm test -- --runInBand` (`frontend` directory)
Expected: all tests PASS.

- [x] **Step 3: Build the Vue frontend**

Run: `npm run build` (`frontend` directory)
Expected: Vite builds to `app/static` and the generated entry point loads the Kakao SDK and public key metadata. Review generated asset diffs and preserve existing user edits.

- [x] **Step 4: Review the complete diff**

Confirm no Kakao secret, access token, `.env`, or `.env.local` is staged; confirm unrelated workspace changes are unchanged; confirm the Kakao-only account has null email/password and existing local login remains functional.

- [x] **Step 5: Report live versus mocked evidence**

Report pytest/Jest/build results, saved Kakao console settings, whether real provider login was completed, and any missing credential that prevented a live OAuth run.
