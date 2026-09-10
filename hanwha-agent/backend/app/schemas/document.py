# 문서 정보 응답해줄 때 사용할 스키마
from pydantic import BaseModel
from typing import Literal

class DocumentOut(BaseModel):
    doc_id: str
    title: str 
    dept: str 
    version: str 
    security_level: Literal["일반", "3급", "대외비"]
    file_format: Literal["docx", "pdf"]
    status: str 
    # secret_note는 외부에 전달할 데이터가 아니라 제외