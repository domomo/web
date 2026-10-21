import secrets

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from app.schemas.user import CurrentUserRes, KakaoStateRes, LoginReq, LoginRes, SignUpReq, SignUpRes
from app.core.security import createToken
from app.core.config import settings
from app.models.user import User
from app.services.kakao import KakaoOAuthClient, KakaoOAuthError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api/user", tags=["user"])
KAKAO_STATE_COOKIE = "kakao_oauth_state"
KAKAO_CALLBACK_PATH = "/api/user/kakao/callback"


@router.get("/me", response_model=CurrentUserRes)
def current_user(user: User = Depends(get_current_user)):
    return user


def get_kakao_client():
    client = KakaoOAuthClient(
        settings.KAKAO_REST_API_KEY,
        settings.KAKAO_CLIENT_SECRET,
        settings.KAKAO_REDIRECT_URI,
    )
    try:
        yield client
    finally:
        client.close()


def _kakao_failure(code: str):
    response = RedirectResponse(f"/login?oauth_error={code}", status_code=302)
    response.delete_cookie(KAKAO_STATE_COOKIE, path=KAKAO_CALLBACK_PATH)
    return response


@router.get(
    "/kakao/state",
    response_model=KakaoStateRes,
    description="Creates a short-lived, callback-scoped HttpOnly state cookie for Kakao OAuth.",
)
def kakao_state(res: Response):
    state = secrets.token_urlsafe(32)
    res.set_cookie(
        KAKAO_STATE_COOKIE,
        state,
        max_age=300,
        httponly=True,
        secure=settings.KAKAO_REDIRECT_URI.startswith("https://"),
        samesite="lax",
        path=KAKAO_CALLBACK_PATH,
    )
    return {"state": state, "redirect_uri": settings.KAKAO_REDIRECT_URI}


@router.get(
    "/kakao/callback",
    include_in_schema=True,
    description="OAuth browser callback. Success redirects to /posts; failures return to /login with a fixed oauth_error.",
)
def kakao_callback(
    code: str | None = Query(default=None, description="Kakao authorization code"),
    state: str | None = Query(default=None, description="One-time OAuth state"),
    error: str | None = Query(default=None, description="Provider cancellation/error code"),
    kakao_state: str | None = Cookie(default=None, alias=KAKAO_STATE_COOKIE),
    db: Session = Depends(get_db),
    kakao: KakaoOAuthClient = Depends(get_kakao_client),
):
    if not state or not kakao_state or not secrets.compare_digest(state, kakao_state):
        return _kakao_failure("invalid_state")
    if error:
        return _kakao_failure("cancelled")
    if not code:
        return _kakao_failure("provider_error")

    try:
        profile = kakao.user_from_code(code)
    except KakaoOAuthError as exc:
        failure = "profile_error" if str(exc) == "profile_incomplete" else "provider_error"
        return _kakao_failure(failure)

    try:
        user = db.scalar(select(User).where(User.kakao_user_id == profile.user_id))
        if user is None:
            user = User(email=None, password=None, name=profile.nickname, kakao_user_id=profile.user_id)
            db.add(user)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                user = db.scalar(select(User).where(User.kakao_user_id == profile.user_id))
                if user is None:
                    return _kakao_failure("server_error")
        response = RedirectResponse("/posts", status_code=302)
        response.set_cookie(
            "EN_AT",
            createToken(f"kakao:{profile.user_id}"),
            httponly=True,
            secure=settings.KAKAO_REDIRECT_URI.startswith("https://"),
            samesite="lax",
        )
        response.delete_cookie(KAKAO_STATE_COOKIE, path=KAKAO_CALLBACK_PATH)
        return response
    except Exception:
        db.rollback()
        return _kakao_failure("server_error")

# 제어의 역전 : IOC(Inversion Of Control)
# 객체 생성이나 프로그램 실행 흐름의 제어를 외부로 넘기는 프로그램 방식
# 의존성 주입 : DI(Dependancy Injection)
# 필요한 객체를 직접 생성하지 않고 외부에서 전달해주는 방식
@router.post("/signup", response_model = SignUpRes)
def signup(req: SignUpReq, db: Session = Depends(get_db)):
    # db 연결 객체 생성
    # db = SessionLocal()

    user = db.scalar(select(User).where(User.email == req.email))

    # 가입이 되어 있으면 None 반환
    # 그렇지 않으면 정상적으로 가입 진행
    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 가입된 이메일입니다. 다른 이메일을 입력해주세요."
        )

    newUser = User(
        email=req.email, password=req.password, name=req.name
    )

    db.add(newUser)
    db.commit()

    return req

@router.post("/login", response_model = LoginRes)
def login(req: LoginReq, res: Response, db: Session = Depends(get_db)):

    user = db.scalar(select(User).where(User.email == req.email))

    if user:
        if user.password == req.password:
            res.set_cookie(
                "EN_AT",
                createToken(req.email),
                httponly=True,
                secure=settings.KAKAO_REDIRECT_URI.startswith("https://"),
                samesite="lax"
            )
            print("정상 로그인")
            return user
    print("비정상 로그인")

    return user


@router.post("/logout")
def logout(res: Response):
    res.delete_cookie(
        "EN_AT",
        path="/",
        secure=settings.KAKAO_REDIRECT_URI.startswith("https://"),
        httponly=True,
        samesite="lax",
    )
    return {"message": "로그아웃되었습니다."}
