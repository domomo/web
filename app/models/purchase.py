from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Purchase(Base):
    __tablename__ = "purchase"
    __table_args__ = (
        UniqueConstraint("buyer_idx", "board_idx", name="uq_purchase_buyer_board"),
        Index("uq_purchase_payment_id", "payment_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buyer_idx: Mapped[int] = mapped_column(ForeignKey("user.idx"), nullable=False)
    board_idx: Mapped[int] = mapped_column(ForeignKey("board.idx"), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PaymentOrder(Base):
    __tablename__ = "payment_order"

    payment_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    buyer_idx: Mapped[int] = mapped_column(ForeignKey("user.idx"), nullable=False)
    board_idx: Mapped[int] = mapped_column(ForeignKey("board.idx"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
