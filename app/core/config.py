# 환경 설정 파일 : DB 접속 주소, 토큰 시크릿 등 환경 변수로 설정된 값을 불러오는 파일

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SECRET_KEY: str = "my-secret-key-for-jwt-must-be-32-bytes-or-more"
    ALGORITHM: str = "HS256"
    DATABASE_URL: str = "sqlite:///db.sqlite3"
    FRONTEND_ORIGIN: str = "https://www.aiready.p-e.kr"
    COOKIE_DOMAIN: str = "aiready.p-e.kr"
    KAKAO_REST_API_KEY: str | None = None
    KAKAO_CLIENT_SECRET: str | None = None
    KAKAO_REDIRECT_URI: str = "https://api.aiready.p-e.kr/api/user/kakao/callback"
    PORTONE_STORE_ID: str | None = None
    PORTONE_CHANNEL_KEY: str | None = None
    PORTONE_API_SECRET: str | None = None

settings = Settings()
