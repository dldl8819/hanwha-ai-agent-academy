# 채팅 요청과 응답 스키마
# - description 은 /docs(OpenAPI) 화면에 그대로 보이는 설명이다
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

# 인용할 수 있는 문서 번호 (임시)
# - 지금은 answer_system.md 에 적어둔 세 건으로 고정한다
# - Literal 이라 목록에 없는 번호를 모델이 지어내면 검증에서 걸린다
# - 한 글자만 틀려도(예: 하이픈 대신 밑줄) 정상 인용까지 검증 실패가 난다
# - 문서가 DB 에서 오게 되면 이 목록 대신 실제 등록 문서로 확인하게 바꾼다
DOC_ID = Literal["DOC-HR-014", "DOC-PU-007", "DOC-SE-003"]

# 사용자가 보내오는 질문 하나를 담는 모델 (들어오는 것)
class ChatRequest(BaseModel):
    # max_length 2000 은 .env 의 MAX_INPUT_CHARS 와 따로 관리되는 값이라, 바꿀 때 둘 다 맞춘다
    question: str = Field(
        min_length=2,
        max_length=2000,
        description="사용자 질문. 두 글자 이상 2000자 이하"
    )

# 답변이 인용한 근거 1개를 담는 모델 (나가는 데이터의 부품)
class AnswerSource(BaseModel):
    doc_id: DOC_ID = Field(description="인용한 문서 번호. 등록된 세 건 중 하나")
    title: str = Field(description="문서 제목")
    version: str = Field(description="문서 버전. 예: v2.0")
    locator: str = Field(description="문서 안 위치. 예: 제12조 · p.6")

# 모델이 돌려줘야 하는 답변의 모양 (나가는 것)
# - 모델 응답을 _extract_json 으로 꺼낸 뒤 이 모델로 검증한다
class AnswerOut(BaseModel):
    answer: str = Field(description="한국어 답변 본문")
    sources: list[AnswerSource] = Field(description="답변이 인용한 근거 목록")
    enough_evidence: bool = Field(description="근거가 충분했는가. 부족하면 False")

# 재시도/폴백 관련 정보 추가 : 라우터가 사용자에게 돌려주는 최종 응답 객체 
class AskOut(AnswerOut):
    run_id: str = Field(description="이 질문 한 건의 실행 번호.예: RUN-1234")
    attempts: int = Field(default=1, description="스키마 검증에 성공하기까지 부른 횟수")
    fallback_used: bool = Field(
        default=False, 
        description="세 번 모두 실패해 폴백 답변으로 대처한 여부"
    )