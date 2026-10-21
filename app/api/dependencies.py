from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.database import get_db
from app.models.user import User


def _resolve_user(db: Session, token: str | None) -> User | None:
    if not token:
        return None
    try:
        payload = decode_token(token)
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject:
            return None
        if subject.startswith("kakao:"):
            return db.scalar(select(User).where(User.kakao_user_id == subject.removeprefix("kakao:")))
        return db.scalar(select(User).where(User.email == subject))
    except Exception:
        return None


def get_current_user(
    db: Session = Depends(get_db),
    token: str | None = Cookie(default=None, alias="EN_AT"),
) -> User:
    user = _resolve_user(db, token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증이 필요합니다.")
    return user


def get_optional_current_user(
    db: Session = Depends(get_db),
    token: str | None = Cookie(default=None, alias="EN_AT"),
) -> User | None:
    return _resolve_user(db, token)
