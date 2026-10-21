from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base

# DB표와 1:1로 매핑되는 파일

class User(Base):
    __tablename__ = "user"

    idx: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(nullable=True)
    password: Mapped[str | None] = mapped_column(nullable=True)
    name: Mapped[str] = mapped_column()
    kakao_user_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)

