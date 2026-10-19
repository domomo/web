from fastapi import APIRouter, Depends, Query
from app.models.board import Board
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.board import BoardWriteReq, BoardWriteRes, BoardReadRes


router = APIRouter(prefix="/api/board", tags=["board"])

@router.post("/write", response_model = BoardWriteRes)
def write(req: BoardWriteReq, db: Session = Depends(get_db)):

    writing = Board(
        title=req.title, contents=req.contents
    )

    db.add(writing)
    db.commit()
    db.refresh(writing)

    return writing

@router.get("/read/{idx}", response_model = BoardReadRes)
def read(idx: int, db: Session = Depends(get_db)):

    reading = db.get(Board, idx)

    return reading

@router.get("/list", response_model=list[BoardReadRes])
def read_list(
    offset: int = Query(default=0, ge=0, description="건너뛸 게시글 수"),
    limit: int = Query(default=20, ge=1, le=100, description="한 번에 조회할 게시글 수"),
    db: Session = Depends(get_db),
):
    """게시글 목록을 최신 게시글 순으로 페이지네이션해 조회한다."""
    statement = select(Board).order_by(Board.idx.desc()).offset(offset).limit(limit)
    return db.scalars(statement).all()
