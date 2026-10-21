# 카카오 첫 로그인 state 실패 조사

## 요약

첫 카카오 로그인의 최종 화면에 `로그인 요청이 만료됐어요. 다시 시도해 주세요.`가 표시된다면, 현재 Vue 코드 기준으로는 `oauth_error=invalid_state` 응답을 받은 것이다. 이 경우 백엔드가 카카오 토큰 교환을 시도하기 전에 OAuth state 검증을 거절했다.

가장 유력한 원인은 **처음 연 웹 페이지의 호스트명과 카카오 콜백 URI의 호스트명이 다른 것**이다. 현재 콜백 URI는 `.env`의 `http://localhost:8000/api/user/kakao/callback`이다. 처음 페이지를 `127.0.0.1`로 열었다면 state 쿠키는 `127.0.0.1`에 저장되지만, 카카오 콜백은 `localhost`로 온다. 브라우저는 두 호스트를 별개로 취급하므로 콜백 요청에 state 쿠키를 보내지 않고, 백엔드는 로그인 요청이 만료됐다고 처리한다.

다만 첫 실패 당시 브라우저의 요청 헤더와 실제 진입 주소를 확보하지 못했으므로 호스트 불일치는 **코드와 증상에 잘 맞는 가설이지, 실측으로 확정된 원인은 아니다.**

## 코드에서 확인한 흐름

1. `frontend/src/pages/LoginPage.vue:25-38`은 `/api/user/kakao/state` 응답의 `state`, `redirect_uri`를 그대로 Kakao SDK의 `Auth.authorize()`에 전달한다.
2. `frontend/src/api.js:1-9, 32`는 상대 경로 `/api/...`로 요청하고 `credentials: 'same-origin'`을 지정한다. 브라우저가 보는 요청 호스트는 페이지를 연 호스트다.
3. 개발 모드의 `frontend/vite.config.js:10`은 `/api`를 `127.0.0.1:8000`으로 프록시한다. 프록시가 전달하더라도 브라우저 관점에서 응답 쿠키는 프런트 페이지의 호스트에 속한다.
4. `app/api/routers/user.py:44-58`은 임의 state를 응답하고 `kakao_oauth_state` 쿠키로 설정한다. 쿠키는 `HttpOnly`, `SameSite=Lax`, 수명 300초, 경로 `/api/user/kakao/callback`이며 `Domain`은 지정하지 않아 요청 호스트에 묶인다.
5. `app/api/routers/user.py:63-72`는 callback 쿼리의 `state`와 쿠키 값이 모두 존재하고 동일한지 비교한다. 누락·불일치 때 `302 /login?oauth_error=invalid_state`를 반환한다.
6. `frontend/src/pages/LoginPage.vue:16-22`는 `invalid_state`를 사용자가 본 만료 메시지로 표시한다. REST 키/Client Secret 문제는 검증 통과 뒤 토큰 교환 단계에서 발생하므로 이 메시지의 직접 원인이 아니다.

## 네트워크 실패가 없어도 발생하는 이유

state 요청은 `200`, callback의 실패 처리는 정상적인 `302` 리다이렉트다. 요청이 네트워크 오류로 실패한 것이 아니라, callback 요청이 서버에 도달한 뒤 애플리케이션이 state를 거부한 것이다. 따라서 Network 탭에 실패 아이콘이 없어도 화면에는 로그인 오류가 표시될 수 있다.

## 원인 확정에 필요한 브라우저 증거

첫 로그인 시도 한 번에 대해 DevTools Network에서 아래 항목을 비교한다. state 값 원문은 공유하거나 로그에 남기지 않는다.

| 요청/정보 | 확인할 항목 |
| --- | --- |
| 처음 연 페이지 | 주소의 호스트가 `localhost`인지 `127.0.0.1`인지 |
| `/api/user/kakao/state` | Request URL 호스트, 응답의 `Set-Cookie` 존재 여부 및 Path/SameSite/Domain 속성 |
| Kakao callback | Request URL 호스트, 요청에 `kakao_oauth_state` 쿠키가 포함됐는지, 응답의 `Location`이 `oauth_error=invalid_state`인지 |

진입 주소가 `127.0.0.1`이고 callback이 `localhost`이며 callback 요청에 쿠키가 없다면 호스트 불일치가 확인된다. 호스트가 같다면 쿠키 누락 여부와 중복된 동일 이름 쿠키를 추가 확인한다.

## 수정 권고와 위치

### 1. 로컬 개발의 기본 조치

브라우저 주소, state 요청 호스트, `KAKAO_REDIRECT_URI`, Kakao Developers에 등록된 callback URI를 모두 동일한 호스트로 맞춘다. 현재 설정을 유지한다면 웹 페이지도 `localhost`로 접속하고 `127.0.0.1` 주소와 혼용하지 않는다. 포트는 쿠키 호스트 범위에 포함되지 않으므로 `localhost:5173`과 `localhost:8000`은 같은 쿠키 호스트를 사용한다.

### 2. 두 호스트를 모두 지원해야 하는 경우

백엔드에서 무조건 요청의 `Host` 헤더를 신뢰해 callback 주소를 만들면 Host 헤더 주입 문제가 생길 수 있다. 두 주소를 지원하려면 허용 호스트 목록을 설정하고, state 쿠키 발급 시 선택한 callback URI를 검증 가능한 OAuth 트랜잭션 정보와 함께 저장해야 한다. 토큰 교환에도 인가 요청과 똑같은 `redirect_uri`를 사용해야 한다. 이 확장은 현재 증거만으로 바로 적용할 필요는 없다.

### 3. 안전한 진단 로그

원인 확인을 위해 임시 또는 구조화 로그에 `query_state_present`, `cookie_state_present`, `state_matches`, 요청 호스트만 기록할 수 있다. 실제 state 문자열, 쿠키 값, 인가 코드, 토큰은 기록하지 않는다.

## 다른 가능성

- state 쿠키의 수명은 300초다. 동의 화면에서 오래 머물러 쿠키가 만료되면 동일한 오류가 날 수 있다.
- 예전 배포에서 같은 이름의 쿠키가 다른 Path로 남았으면 callback 요청에 중복 쿠키가 포함될 수 있다. 현재 코드는 callback Path 쿠키만 설정·삭제하므로 실제 요청 헤더에서 확인해야 한다.
- 기존 `tests/test_kakao_auth.py`의 state 테스트는 단일 TestClient 호스트와 쿠키 저장소에서 수행한다. `localhost`와 `127.0.0.1` 간 쿠키 범위나 실제 브라우저 리다이렉트는 검증하지 않는다.

## 부수 설정 관찰

현재 루트 `.env.example`에서 `KAKAO_CLIENT_SECRET`과 `KAKAO_REDIRECT_URI`가 한 줄로 붙어 있어, 예시 파일을 그대로 복사하면 redirect URI 변수가 별도 항목으로 로드되지 않는다. 이 문제는 이미 만들어진 런타임 `.env`의 값과는 별개지만, 템플릿은 별도 줄로 수정해야 한다.

## 이번 검토 범위

프런트엔드와 백엔드 에이전트가 각각 읽기 전용으로 검토했다. 애플리케이션 코드는 변경하지 않았고, 이 파일에 조사 결과와 권고만 기록했다. 실제 브라우저의 첫 실패 요청 헤더가 제공되면 호스트 불일치 여부를 확정할 수 있다.
