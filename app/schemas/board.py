from pydantic import BaseModel

# 작성용 요청, 제목, 내용
class BoardWriteReq(BaseModel):
    title: str
    contents: str

# 작성용 응답, 번호, 제목, 내용
class BoardWriteRes(BaseModel):
    idx: int
    title: str
    contents: str

# 조회용 요청 : 필요x

# 조회용 응답 : 번호, 제목, 내용
class BoardReadRes(BaseModel):
    idx: int
    title: str
    contents: str