from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_optional_current_user
from app.db.database import get_db
from app.models.board import Board
from app.models.purchase import Purchase
from app.models.user import User
from app.schemas.board import BoardCategory, BoardReadRes, BoardWriteReq, BoardWriteRes


router = APIRouter(prefix="/api/board", tags=["board"])


def _board_response(board: Board, user: User | None, db: Session, *, reveal_contents: bool = False):
    is_for_sale = board.sale_price is not None
    is_author = user is not None and board.author_idx == user.idx
    has_purchased = False
    if user is not None and is_for_sale:
        has_purchased = db.scalar(select(Purchase.id).where(
            Purchase.board_idx == board.idx, Purchase.buyer_idx == user.idx,
            Purchase.payment_id.is_not(None),
        )) is not None
    return {
        "idx": board.idx,
        "title": board.title,
        "contents": board.contents if (not is_for_sale or is_author or has_purchased or reveal_contents) else None,
        "category": board.category,
        "author_name": db.scalar(select(User.name).where(User.idx == board.author_idx)) if board.author_idx else None,
        "preview": board.preview,
        "sale_price": board.sale_price,
        "is_for_sale": is_for_sale,
        "is_author": is_author,
        "has_purchased": has_purchased,
    }


@router.post(
    "/write",
    response_model=BoardWriteRes,
    description="Creates a free or paid article. Paid articles require authentication; no charge is processed.",
    responses={401: {"description": "Authentication is required for paid articles."}},
)
def write(req: BoardWriteReq, db: Session = Depends(get_db), user: User | None = Depends(get_optional_current_user)):
    if req.sale_price is not None and user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증이 필요합니다.")
    writing = Board(
        title=req.title, contents=req.contents, category=req.category,
        author_idx=user.idx if req.sale_price is not None and user else None,
        sale_price=req.sale_price, preview=req.preview,
    )
    db.add(writing)
    db.commit()
    db.refresh(writing)
    return _board_response(writing, user, db, reveal_contents=True)


@router.get("/read/{idx}", response_model=BoardReadRes)
def read(idx: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_current_user)):
    reading = db.get(Board, idx)
    if reading is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return _board_response(reading, user, db)


@router.get("/list", response_model=list[BoardReadRes])
def read_list(
    offset: int = Query(default=0, ge=0, description="건너뛸 게시글 수"),
    limit: int = Query(default=20, ge=1, le=100, description="한 번에 조회할 게시글 수"),
    category: BoardCategory | None = Query(default=None, description="분야별 필터. 생략하면 모든 글을 조회한다."),
    sale_type: str | None = Query(default=None, pattern="^(free|paid)$", description="무료 또는 유료 글 필터"),
    db: Session = Depends(get_db), user: User | None = Depends(get_optional_current_user),
):
    statement = select(Board)
    if category is not None:
        statement = statement.where(Board.category == category)
    if sale_type == "free":
        statement = statement.where(Board.sale_price.is_(None))
    elif sale_type == "paid":
        statement = statement.where(Board.sale_price.is_not(None))
    statement = statement.order_by(Board.idx.desc()).offset(offset).limit(limit)
    return [_board_response(board, user, db) for board in db.scalars(statement).all()]
