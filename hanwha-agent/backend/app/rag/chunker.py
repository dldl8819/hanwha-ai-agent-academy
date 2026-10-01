from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.integrations.ports import ParsedDoc

# 정규표현식 추가
# - 제 1조, 제 12조(숙박비)
# - 별표1 ..
# 패턴 전체를 ( )로 감싸서 split 결과에 조 제목도 남게 한다
_ARTICLE = re.compile(r"(제\s*\d+\s*조(?:의\s*\d+)?\s*(?:\([^)]{1,30}\))?)")
_ANNEX = re.compile(r"(별표\s*\d+)")

MAX_CHARS = 1200   # 청크 하나의 최대 글자 수. 넘으면 _hard_wrap으로 다시 자른다
MIN_CHARS = 30     # 이보다 짧은 머리말은 청크로 만들지 않는다
TOC_BODY_MIN = 10  # 목차 줄을 거를 때 쓰는 본문 최소 글자 수

# 청킹 결과 한 건. 임베딩·저장 직전 단계의 초안
@dataclass
class ChunkDraft:
    kind: str     # 조항 | 표
    locator: str  # 원본 어디서 나왔는지 : 제3조(숙박비), p.6, 표2
    text: str     # 임베딩할 본문

# 조 단위로 자르기
# 반환값: (조 제목, 제목을 포함한 조 본문) 쌍의 목록. 제목이 없는 덩어리는 제목 자리가 ""
def _split_articles(text: str) -> list[tuple[str, str]]:
    # split 결과: [머리말, 제목1, 본문1, 제목2, 본문2, ...]
    parts = _ARTICLE.split(text)
    if len(parts) <= 1:
        # 조항이 하나도 없으면 전체를 한 덩어리로
        return [("", text.strip())] if text.strip() else []

    out: list[tuple[str, str]] = []
    # 첫 조 앞의 머리말은 충분히 길 때만 남긴다
    head = parts[0].strip()
    if len(head) >= MIN_CHARS:
        out.append(("", head))
    # 1번부터 두 칸씩 건너뛰며 (제목, 본문) 쌍으로 묶는다
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i+1].strip() if i + 1 < len(parts) else ""
        # 검색 결과만 봐도 어느 조인지 알 수 있게 본문 앞에 제목을 붙인다
        out.append((title, f"{title} {body}".strip()))

    return out

# 길이가 아주 긴 조를 limit 이하로 나누기 (폴백)
def _hard_wrap(text: str, limit: int = MAX_CHARS) -> list[str]:
    if len(text) <= limit:
        return [text]
    # 문단 → 줄 → 문장 끝("다. ") → 공백 → 글자 순으로 자를 곳을 찾는다
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=limit,
        chunk_overlap=0,
        separators=["\n\n", "\n", "다. ", ". ", " ", ""],
        keep_separator="end"  # 구분자를 앞 조각 끝에 붙여서 "~한다." 문장이 온전히 남게 한다
    )
    return splitter.split_text(text)

# ParsedDoc -> 청크 목록으로 변환해서 리턴
# 표는 블록 하나를 그대로 청크로 만들고, 나머지 본문 블록은 buffer에 모았다가 조 단위로 다시 자른다
def chunk(doc: ParsedDoc) -> list[ChunkDraft]:
    out: list[ChunkDraft] = []
    buffer: list[str] = []  # 아직 청크로 만들지 않은 본문 블록 텍스트. 조항 하나가 여러 블록(페이지)에 걸칠 수 있어서 모아 둔다
    buffer_locator = ""     # buffer에 처음 들어온 블록의 위치. 조 제목이 없는 청크의 locator로 쓴다

    # buffer에 모인 본문을 조 단위 청크로 바꿔 out에 넣고 buffer를 비운다
    def flush() -> None:
        nonlocal buffer, buffer_locator
        if not buffer:
            return
        # TODO: _articles_from 아직 정의 안 됨
        out.extend(_articles_from("\n".join(buffer), buffer_locator))
        buffer = []
        buffer_locator = ""

    for block in doc.blocks:
        if block.kind == "표":
            # 표가 나오면 앞에 쌓인 본문부터 청크로 만든 뒤 표를 따로 넣는다 (본문 순서 유지)
            flush()
            out.append(ChunkDraft("표", block.locator, block.text))
            continue
        if not buffer_locator:
            buffer_locator = block.locator
        buffer.append(block.text)
    # 문서 끝에 남은 본문 처리
    flush()
    return out

# 본문 덩어리를 조 단위로 자르는 함수
# TODO: 아직 작성 중이다. 목록을 만들다 말고 return 이 없어 None 을 돌려주므로
#       chunk() 가 extend 하다 TypeError 로 터진다. 목차 줄 분기에도 continue 가 없어
#       같은 본문이 두 번 들어간다.
def _articles_from(text: str, fallback_locator: str) -> list[ChunkDraft]:
    drafts: list[ChunkDraft] = []
    # title : 제 1조(...) 
    # body : 제 1조(...) 내용...
    for title, body in _split_articles(text):
        if not body.strip():
            continue

        remainder = body[len(title):].strip() if title else body
        if len(remainder) < TOC_BODY_MIN:
            if drafts:
                drafts[-1].text += "\n" + body
            else:
                drafts.append(ChunkDraft("조항", fallback_locator, body))

        if not title:
            locator = fallback_locator
        else:
            annex = _ANNEX.search(body)
            locator = title if not annex else f"{title} - {annex.group(1)}"

        # --- 이어서 하기#