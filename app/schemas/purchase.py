from datetime import datetime

from pydantic import BaseModel


class PurchaseReq(BaseModel):
    board_idx: int


class PurchasePrepareRes(BaseModel):
    payment_id: str
    board_idx: int
    order_name: str
    amount: int
    currency: str = "KRW"


class PurchaseConfirmReq(BaseModel):
    payment_id: str


class PaymentConfigRes(BaseModel):
    configured: bool
    store_id: str | None
    channel_key: str | None


class PurchaseRes(BaseModel):
    id: int
    board_idx: int
    price: int
    created_at: datetime
