from app.db.database import Base
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

class Board(Base):
    __tablename__ = "board"

    idx: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    contents: Mapped[str] = mapped_column()
    # Existing notes have no known category, so keep this nullable for migration compatibility.
    category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    author_idx: Mapped[int | None] = mapped_column(ForeignKey("user.idx"), nullable=True)
    preview: Mapped[str | None] = mapped_column(String, nullable=True)
    sale_price: Mapped[int | None] = mapped_column(nullable=True)
