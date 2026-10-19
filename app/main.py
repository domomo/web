# 전체 서버 진입점, FastAPI 객체 생성, 라우터 등록, 테이블 생성

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.routers import board, user
from app.db.database import Base, engine
from app.models.user import User
from app.models.board import Board

app = FastAPI(title="노트 api", version="0.1.0")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(user.router)
app.include_router(board.router)

Base.metadata.create_all(bind=engine)
@app.get("/")
def main():
    return FileResponse(static_dir / "index.html")


@app.get("/{full_path:path}", include_in_schema=False)
def frontend_route(full_path: str):
    """Serve the Vue entry point for client-side page routes."""
    if full_path.startswith(("api/", "static/")):
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(static_dir / "index.html")
