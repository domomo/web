# Kakao Login Setup

## Kakao Developers app

The `mlops` app (app ID `1614699`) is configured for local development:

- Kakao Login is enabled.
- `profile_nickname` is the only required consent item. Email is not requested.
- JavaScript SDK domains: `http://localhost:5173` and `http://localhost:8000`.
- Redirect URI: `http://localhost:8000/api/user/kakao/callback`.

These values are registered on the active JavaScript platform key. For production, set the backend `KAKAO_REDIRECT_URI` to `https://api.aiready.p-e.kr/api/user/kakao/callback` and register that exact URL in Kakao Developers → Kakao Login → Redirect URI. The frontend calls the backend API domain directly, and the browser returns to the frontend after the backend handles the callback. The backend setting and Kakao registration must match exactly. If the deployed server's `.env` already sets `KAKAO_REDIRECT_URI`, update it and restart Uvicorn.

## Local environment

Copy `.env.example` to `.env` and enter the server REST API key and client secret from **App settings → Platform keys → REST API key**. Keep both values server-side. Copy `frontend/.env.example` to `frontend/.env.local` and set only the public JavaScript key from **App settings → Platform keys → JavaScript key**.

The root `.env` and `frontend/.env.local` files are ignored by Git. Never commit them or put the REST API key/client secret in a `VITE_` variable.

Start the backend and frontend in separate terminals:

```powershell
python -m uvicorn app.main:app --reload --port 8000
cd frontend
npm run dev
```

Open `http://localhost:5173/login`, choose **카카오로 로그인**, and approve the nickname consent. A successful callback creates or reuses a Kakao-ID account, sets `EN_AT`, and returns to `/posts`.

## Account identity and email

This flow stores the Kakao member ID and nickname. Kakao email is not requested or stored, so the application cannot detect whether it matches a local account email. Kakao accounts are never linked to local accounts by email.

## Local provider simulation

The Postman simulation models only the Kakao token and nickname lookup requests used by this integration. Start it with `postman simulation run postman/simulations/kakao-dev.sim.yaml --port 4900 --output ndjson`; in a second terminal run the targeted auth tests with `$env:KAKAO_SIMULATION_URL='http://127.0.0.1:4900'` before pytest. This is simulated evidence, not a live Kakao login.
