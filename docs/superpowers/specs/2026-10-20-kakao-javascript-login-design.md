# 카카오 JavaScript SDK 로그인 설계

## 목적

Vue 로그인 화면에 카카오 로그인을 추가하고, 기존 FastAPI 세션 쿠키 방식과 함께 사용할 수 있게 한다. 첫 카카오 로그인은 카카오 회원번호로 새 로컬 사용자를 만들며, 이후 로그인은 같은 회원번호에 연결된 사용자로 처리한다.

## 합의된 범위

- 프런트엔드는 Kakao JavaScript SDK v2를 사용한다.
- Kakao `Auth.authorize()` 인가 코드 흐름을 사용하고, 인가 코드 교환과 로컬 계정 생성은 FastAPI가 담당한다.
- 카카오에서 요청하고 저장하는 프로필 정보는 회원번호와 닉네임뿐이다. 이메일 동의항목은 요청하지 않고, 응답에 포함되더라도 사용하거나 저장하지 않는다.
- 기존 이메일·비밀번호 가입과 로그인은 계속 사용할 수 있다.
- 새 카카오 사용자는 닉네임을 로컬 표시 이름으로 저장하고 기존 `EN_AT` 쿠키로 로그인한다.
- 카카오 계정과 기존 로컬 계정은 이메일 기반으로 자동 연결하지 않는다.

## 이메일 중복 정책 제약

카카오 이메일을 요청하지 않고 닉네임만 받으면 카카오 계정의 이메일과 로컬 이메일이 같은지 알 수 없다. 그러므로 “카카오 이메일이 기존 로컬 계정과 같으면 로그인을 거절한다”는 조건은 현재 범위와 양립하지 않는다. 이 설계에서는 이메일 중복 검사를 수행하지 않는다. 계정은 카카오의 고유 회원번호로 분리해 식별하며, 카카오에서 이메일을 요청하거나 사용자에게 이메일 입력을 받는 흐름은 포함하지 않는다.

## 현재 프로젝트 맥락

- FastAPI 라우터는 `app/api/routers/user.py`에 있고, Vue 로그인 화면은 `frontend/src/pages/LoginPage.vue`에 있다.
- `User` 모델은 `email`, `password`, `name`을 필수로 저장한다. 카카오 계정은 이메일과 비밀번호가 없으므로 두 열을 nullable로 바꾸고 nullable unique `kakao_user_id` 열을 추가한다.
- DB는 SQLAlchemy와 SQLite를 사용하며 현재 스키마 변경은 `app/db/database.py`의 시작 시 마이그레이션 함수와 `app/main.py`의 초기화 흐름을 따른다.
- Vue 개발 서버는 기본 포트 5173이며 `/api`를 FastAPI `127.0.0.1:8000`에 프록시한다. 빌드 산출물은 `app/static`에서 FastAPI가 제공한다.
- 프로젝트 지침의 완료 기준은 백엔드 pytest 전체 통과 및 프런트엔드 Jest 전체 통과다.

## 구성과 데이터 흐름

1. 로그인 화면은 설정된 `VITE_KAKAO_JS_KEY`로 Kakao JavaScript SDK v2를 초기화한다. SDK 로드는 단일 모듈에서 한 번만 수행하고 초기화 실패는 로그인 화면에 일반 오류로 표시한다.
2. 사용자가 카카오 버튼을 누르면 Vue가 `GET /api/user/kakao/state`를 호출한다. FastAPI는 짧은 수명의 난수 `state`를 생성하고, 해당 값을 담은 HttpOnly, SameSite=Lax 상태 쿠키를 설정한 뒤 브라우저에 `state`와 설정된 카카오 콜백 URI를 반환한다.
3. Vue는 반환받은 값으로 `Kakao.Auth.authorize({ redirectUri, scope: "profile_nickname", state })`를 호출한다. 카카오 개발자 설정은 프로필 닉네임 동의항목만 필수로 사용하도록 한다.
4. Kakao는 `code`와 `state`를 `GET /api/user/kakao/callback`에 전달한다. FastAPI는 요청의 `state`와 상태 쿠키를 상수 시간 비교로 확인하고 상태 쿠키를 폐기한다. 누락, 불일치, 만료된 상태는 로그인 실패로 처리한다.
5. FastAPI는 Kakao 토큰 API에서 코드를 교환하고 Kakao 사용자 정보 API를 `kakao_account.profile`만 요청해 조회한다. Kakao 회원번호와 프로필 닉네임만 읽는다. REST API 키와 클라이언트 시크릿은 백엔드 설정에 두며 프런트엔드로 전달하지 않는다.
6. `kakao_user_id`가 이미 존재하면 그 계정으로 로그인한다. 없으면 `email=None`, `password=None`, `name=<nickname>`으로 사용자를 만든다. 닉네임을 제공받지 못한 경우 임의의 프로필을 만들지 않고 실패 처리한다.
7. FastAPI는 기존 `EN_AT` HttpOnly 쿠키를 발급하고 `/posts`로 리다이렉트한다. Kakao 취소와 공급자 오류는 `/login`에 안전한 고정 오류 코드만 전달한다. 공급자의 원문 오류, 인가 코드, 토큰은 URL 또는 로그에 노출하지 않는다.

## API 계약

### `GET /api/user/kakao/state`

- 브라우저에서 로그인 버튼을 누른 뒤 호출한다.
- 응답: `{ "state": "<random-state>", "redirect_uri": "<configured-callback-uri>" }`
- `kakao_oauth_state` 쿠키: HttpOnly, SameSite=Lax, 5분 만료. HTTPS에서는 Secure이며 개발 HTTP에서는 Secure를 끈다. 경로는 카카오 콜백 경로로 제한한다.
- Kakao JavaScript 키 또는 토큰은 응답에 넣지 않는다.

### `GET /api/user/kakao/callback`

- Kakao가 `code`, `state` 또는 `error` 쿼리 매개변수로 호출한다.
- 성공은 `EN_AT` 설정과 `/posts`로의 302 리다이렉트다.
- 취소, 잘못된 state, 코드 교환 실패, 사용자 정보 실패, DB 실패는 각각 안전한 오류 코드와 함께 `/login`으로 리다이렉트한다.
- 이 콜백은 브라우저 네비게이션 계약이며 JSON 응답을 반환하지 않는다.

FastAPI의 자동 생성 OpenAPI를 이 API 계약의 로컬 기준으로 사용한다. OAuth 콜백에는 필요한 쿼리 매개변수와 리다이렉트 동작 설명을 적고, state 시작 엔드포인트에는 응답 스키마와 쿠키 동작을 기술한다. 별도 Postman 컬렉션이나 외부 워크스페이스는 현재 저장소에 없으므로 이번 설계에는 추가하지 않는다.

## 데이터와 마이그레이션

- `User.email`: nullable로 변경. 기존 행 값은 그대로 보존한다.
- `User.password`: nullable로 변경. 기존 행 값은 그대로 보존한다.
- `User.kakao_user_id`: nullable 문자열, 고유 제약 조건. 기존 행은 `NULL`로 유지한다.
- SQLite에는 기존 열의 NOT NULL 제약을 직접 제거할 수 없으므로 기존 `user` 테이블을 임시 테이블로 재작성하고 기존 `idx`, `email`, `password`, `name`을 복사한 뒤 새 제약으로 교체한다. 테이블 재작성은 트랜잭션 안에서 수행하고, 실패 시 시작을 중단해 기존 테이블을 보존한다.
- 회원가입은 계속 이메일, 비밀번호, 이름을 요구한다. 비밀번호 로그인은 이메일/비밀번호가 모두 있는 사용자만 성공한다.

## 설정과 Kakao 개발자 콘솔

서버 환경 변수:

- `KAKAO_REST_API_KEY`
- `KAKAO_CLIENT_SECRET`
- `KAKAO_REDIRECT_URI`

프런트엔드 공개 설정:

- `VITE_KAKAO_JS_KEY` — 공개 JavaScript 키만 포함한다. REST API 키와 클라이언트 시크릿은 여기에 두지 않는다.

개발 환경은 현재 Vite 원점 `http://localhost:5173`, FastAPI 원점 `http://localhost:8000`, 콜백 `http://localhost:8000/api/user/kakao/callback`을 사용한다. Kakao 개발자 콘솔의 현재 선택 앱 `mlops`에 Kakao Login을 켜고 닉네임 동의항목을 필수로 설정하며, JavaScript SDK 도메인 `http://localhost:5173` 및 `http://localhost:8000`과 정확히 일치하는 콜백 URI를 등록한다. 현재 앱에서 Kakao Login은 꺼져 있다. 운영 원점은 저장소에 없으므로 추정하거나 등록하지 않는다.

## 오류 및 보안

- state는 매 로그인 시 새로 생성하고, 브라우저 세션 쿠키와 콜백 값을 비교한다.
- Kakao 토큰은 서버에서만 사용하며 저장하지 않는다. 클라이언트 시크릿은 저장소에 기록하지 않는다.
- 프런트엔드는 SDK 토큰이나 Kakao API의 사용자 원문을 자체 로그인 신뢰 근거로 사용하지 않는다.
- Kakao 취소, 사용자 닉네임 미제공, 잘못된 state, 외부 API 네트워크/오류 응답, 이미 처리된/잘못된 코드, DB 쓰기 오류를 구분해 검증한다.
- 오류 안내는 사용자에게 이해 가능한 고정 메시지를 사용하고, 자격 증명이나 개인 정보를 로그에 남기지 않는다.
- Kakao 이메일은 수집하지 않으므로 이메일 일치 여부에 따른 거절은 동작하지 않는다.

## 검증 범위

### Backend pytest

- 신규/기존 SQLite 테이블 마이그레이션이 기존 로컬 계정을 보존하고 새 스키마 제약을 적용한다.
- state 쿠키 발급, 올바른 state 성공, 누락/불일치 state 실패를 검증한다.
- Kakao 코드 교환 및 사용자 정보 API는 모의하고, Kakao 회원번호와 닉네임만 저장되는지 검증한다.
- 기존 Kakao 계정 재로그인, 새 계정 생성, 닉네임 누락, Kakao 취소/오류, 중복 Kakao 회원번호, DB 오류를 검증한다.
- 성공 시 `EN_AT` 쿠키 및 `/posts` 리다이렉트, 실패 시 안전한 `/login` 오류 리다이렉트를 검증한다.
- 기존 이메일 가입/로그인과 비밀번호 없는 카카오 사용자의 비밀번호 로그인 거절을 검증한다.

### Frontend Jest

- SDK가 설정된 JavaScript 키로 한 번 초기화된다.
- 카카오 버튼이 state 엔드포인트를 호출하고 `profile_nickname` 범위 및 응답 콜백 URI로 authorize를 호출한다.
- 대기, SDK 로드/초기화 실패, state API 실패, OAuth 취소 오류 메시지와 접근 가능한 상태 표시를 검증한다.
- 기존 로그인 폼 제출 동작을 유지한다.

### 전체 검증

- 백엔드 전체: `pytest`
- 프런트엔드 전체: `npm test -- --runInBand` (`frontend`에서 실행)
- 빌드: `npm run build` (`frontend`에서 실행)

## 범위 밖

- Kakao 이메일 수집, 로컬 이메일과의 중복 비교, 이메일 기반 자동 계정 연결
- 여러 소셜 제공자, 계정 병합/연결 해제, Kakao 연결 해제 및 웹훅
- 운영 도메인 결정과 운영 배포 설정
- 기존 평문 비밀번호 저장 방식의 별도 보안 개선
