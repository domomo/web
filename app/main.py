# 전체 서버 진입점, FastAPI 객체 생성, 라우터 등록, 테이블 생성

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.routers import board, purchase, user
from app.db.database import Base, engine, ensure_board_category_column, ensure_board_sale_columns, ensure_purchase_payment_column, ensure_user_kakao_schema
from app.models.user import User
from app.models.board import Board
from app.models.purchase import PaymentOrder, Purchase
from app.core.config import settings

app = FastAPI(title="노트 api", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(user.router)
app.include_router(board.router)
app.include_router(purchase.router)

Base.metadata.create_all(bind=engine)
ensure_board_category_column(engine)
ensure_board_sale_columns(engine)
ensure_purchase_payment_column(engine)
ensure_user_kakao_schema(engine)
@app.get("/")
def main():
    return FileResponse(static_dir / "index.html")

@app.get("/{full_path:path}", include_in_schema=False)
def frontend_route(full_path: str):
    """Serve the Vue entry point for client-side page routes."""
    if full_path.startswith(("api/", "static/")):
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(static_dir / "index.html")
