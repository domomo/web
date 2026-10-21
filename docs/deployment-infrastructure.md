# 배포 서버 정보

배포 대상은 Windows 서버 두 대입니다.

| 역할 | 서버 IP / 공개 주소 | 배포 경로 / 서비스 |
| --- | --- | --- |
| 프론트엔드 | `100.100.100.129` / `https://www.aiready.p-e.kr` | Nginx `C:\Users\test\nginx-1.30.5`; 빌드 결과를 `C:\Users\test\nginx-1.30.5\html`에 배치 |
| 백엔드 | `100.100.100.127` | `C:\Users\test\backend`; Uvicorn, 내부 포트 8000 |

두 서버 모두 SSH 접속 계정은 `test`입니다. SSH 포트는 배포용 GitHub Actions Variable로 관리합니다. 접속 비밀번호는 저장소에 기록하지 말고 GitHub Actions Secret으로 설정합니다.

프론트엔드 빌드는 `frontend` 폴더에서 `npm run build`를 실행하며, 결과는 `app/static`에 생성됩니다. 이 결과물을 Nginx 서버의 `html` 폴더에 배포해야 합니다.

브라우저는 `https://api.aiready.p-e.kr/api/...`로 백엔드에 직접 요청합니다. 백엔드 API 도메인은 Uvicorn 서버로 연결되어야 하며, 백엔드 `.env`의 `FRONTEND_ORIGIN`은 `https://www.aiready.p-e.kr`, `COOKIE_DOMAIN`은 `aiready.p-e.kr`로 유지하세요. 프론트엔드 빌드 시 기본 API 주소도 `https://api.aiready.p-e.kr`입니다. 다른 환경 주소가 필요하면 `VITE_API_BASE_URL`로 지정할 수 있습니다.

브라우저에서 프론트엔드와 API는 서로 다른 출처이므로 백엔드 CORS에서 `https://www.aiready.p-e.kr`을 허용하고 credentials를 활성화해야 합니다. API 도메인의 HTTPS 연결과 백엔드 8000 포트로의 네트워크 연결도 정상이어야 합니다.

카카오 로그인 운영 콜백은 `https://api.aiready.p-e.kr/api/user/kakao/callback`입니다. 백엔드 서버의 `.env`에 `KAKAO_REDIRECT_URI`가 이미 있으면 이 주소로 변경하고 Uvicorn을 재시작하세요. Kakao Developers의 Kakao Login Redirect URI에도 이 주소를 정확히 등록해야 합니다. 등록 주소와 백엔드 설정은 프로토콜, 호스트, 경로까지 일치해야 합니다. OAuth callback 성공 시 사용자는 `https://www.aiready.p-e.kr/posts`로 이동하고, 실패 시 프론트엔드의 로그인 페이지로 이동합니다.

## GitHub Actions 설정에 사용할 값

- 프론트엔드 SSH 호스트: `100.100.100.129`
- 백엔드 SSH 호스트: `100.100.100.127`
- SSH 사용자: `test`
- 백엔드 배포 디렉터리: `C:\Users\test\backend`
- 프론트엔드 웹 루트: `C:\Users\test\nginx-1.30.5\html`
- SSH 비밀번호: Actions Secret에만 저장
