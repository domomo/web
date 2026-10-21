from pydantic import BaseModel, model_validator
from typing import Literal

BoardCategory = Literal["경제/경영", "과학/IT", "예술/취미", "인문/교양"]

# 작성용 요청, 제목, 내용, 분야
class BoardWriteReq(BaseModel):
    title: str
    contents: str
    category: BoardCategory
    sale_price: int | None = None
    preview: str | None = None

    @model_validator(mode="after")
    def validate_sale_fields(self):
        if self.sale_price is None:
            if self.preview is not None and not self.preview.strip():
                raise ValueError("preview must not be blank")
            return self
        if self.sale_price <= 0:
            raise ValueError("sale_price must be positive")
        if self.preview is None or not self.preview.strip():
            raise ValueError("preview is required for paid articles")
        return self

# 작성용 응답, 번호, 제목, 내용
class BoardWriteRes(BaseModel):
    idx: int
    title: str
    contents: str
    category: BoardCategory | None
    author_name: str | None = None
    preview: str | None = None
    sale_price: int | None = None
    is_for_sale: bool = False
    is_author: bool = False
    has_purchased: bool = False

# 조회용 요청 : 필요x

# 조회용 응답 : 번호, 제목, 내용
class BoardReadRes(BaseModel):
    idx: int
    title: str
    contents: str | None
    category: BoardCategory | None
    author_name: str | None = None
    preview: str | None = None
    sale_price: int | None = None
    is_for_sale: bool = False
    is_author: bool = False
    has_purchased: bool = False
