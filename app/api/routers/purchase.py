from uuid import uuid4

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.models.board import Board
from app.models.purchase import PaymentOrder, Purchase
from app.models.user import User
from app.schemas.purchase import PaymentConfigRes, PurchaseConfirmReq, PurchasePrepareRes, PurchaseReq, PurchaseRes


router = APIRouter(prefix="/api/purchases", tags=["purchases"])


def _require_portone_config():
    if not (settings.PORTONE_STORE_ID and settings.PORTONE_CHANNEL_KEY and settings.PORTONE_API_SECRET):
        raise HTTPException(status_code=503, detail="포트원 결제 설정이 아직 준비되지 않았습니다.")


@router.get("/config", response_model=PaymentConfigRes)
def public_payment_config() -> PaymentConfigRes:
    """Expose only the browser SDK's public store and channel identifiers."""
    configured = bool(settings.PORTONE_STORE_ID and settings.PORTONE_CHANNEL_KEY and settings.PORTONE_API_SECRET)
    return PaymentConfigRes(
        configured=configured,
        store_id=settings.PORTONE_STORE_ID if configured else None,
        channel_key=settings.PORTONE_CHANNEL_KEY if configured else None,
    )


@router.post(
    "/prepare",
    response_model=PurchasePrepareRes,
    description="Creates a server-priced PortOne V2 payment order. This does not grant article access.",
    responses={401: {"description": "Authentication is required."}, 404: {"description": "Article not found."}, 409: {"description": "Article is free, owned, or already purchased."}, 503: {"description": "PortOne V2 credentials are not configured."}},
)
def prepare_purchase(req: PurchaseReq, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _require_portone_config()
    board = db.get(Board, req.board_idx)
    if board is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if board.sale_price is None or board.author_idx == user.idx:
        raise HTTPException(status_code=409, detail="구매할 수 없는 게시글입니다.")
    existing = db.scalar(select(Purchase).where(
        Purchase.board_idx == board.idx, Purchase.buyer_idx == user.idx, Purchase.payment_id.is_not(None)
    ))
    if existing:
        raise HTTPException(status_code=409, detail="이미 구매한 게시글입니다.")
    payment_id = f"article-{uuid4()}"
    order = PaymentOrder(payment_id=payment_id, buyer_idx=user.idx, board_idx=board.idx, amount=board.sale_price)
    db.add(order)
    db.commit()
    return PurchasePrepareRes(payment_id=payment_id, board_idx=board.idx, order_name=board.title[:80], amount=board.sale_price)


@router.post(
    "/confirm",
    response_model=PurchaseRes,
    description="Confirms a PortOne V2 payment by retrieving it server-side and matching paid status, amount, and currency before granting article access.",
    responses={401: {"description": "Authentication is required."}, 404: {"description": "Payment order not found."}, 409: {"description": "Payment is not paid or does not match the order."}, 502: {"description": "PortOne payment verification failed."}, 503: {"description": "PortOne V2 credentials are not configured."}},
)
def confirm_purchase(req: PurchaseConfirmReq, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _require_portone_config()
    payment_id = req.payment_id
    order = db.get(PaymentOrder, payment_id)
    if order is None or order.buyer_idx != user.idx:
        raise HTTPException(status_code=404, detail="결제 주문을 찾을 수 없습니다.")
    prior = db.scalar(select(Purchase).where(
        Purchase.board_idx == order.board_idx, Purchase.buyer_idx == user.idx, Purchase.payment_id.is_not(None)
    ))
    if prior:
        return prior
    try:
        response = requests.get(
            f"https://api.portone.io/payments/{payment_id}",
            headers={"Authorization": f"PortOne {settings.PORTONE_API_SECRET}"},
            timeout=10,
        )
        response.raise_for_status()
        payment = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise HTTPException(status_code=502, detail="포트원 결제 내역을 확인하지 못했습니다.") from exc
    amount = payment.get("amount") or {}
    if (
        payment.get("status") != "PAID"
        # PortOne V2's payment lookup response identifies the payment with `id`.
        # `paymentId` appears on transaction/event objects, not the Payment object.
        or payment.get("id") != payment_id
        or amount.get("total") != order.amount
        or payment.get("currency") not in ("KRW", "CURRENCY_KRW")
    ):
        raise HTTPException(status_code=409, detail="결제 완료 상태와 주문 금액을 확인하지 못했습니다.")

    order.status = "PAID"
    purchase = Purchase(buyer_idx=user.idx, board_idx=order.board_idx, price=order.amount, payment_id=payment_id)
    db.add(purchase)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(Purchase).where(
            Purchase.board_idx == order.board_idx,
            Purchase.buyer_idx == user.idx,
            Purchase.payment_id.is_not(None),
        ))
        if existing is None:
            raise
        return existing
    db.refresh(purchase)
    return purchase
