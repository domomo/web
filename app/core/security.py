# 보안상 중요한 값이나 기능들을 모아둔 파일, 토큰 생성, 비밀번호 암호화 등

from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings

SECRET_KEY = "aowepijvae54arv5a5ew3a5e1ca3ds21ca3sd21as3d2v1"
ALGORITHM = "HS256"

def createToken(userId:str):
    payload = {
        "sub": userId,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return token


def decode_token(token: str) -> dict:
    """Decode and validate an EN_AT JWT using the configured signing settings."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )


# Keep the existing camelCase naming convention available to callers.
decodeToken = decode_token

# security 파일
# 토큰 확인하는 함수
# 토큰에서 원하는 값을 가져오는 함수
# 비밀번호 암호화하는 함수
# 비밀번호 확인
