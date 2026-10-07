from __future__ import annotations

from pathlib import Path

from app.core.logging import get_logger
from app.integrations.ports import ParsedBlock, ParsedDoc
from app.rag.local_parsers import parse_local

log = get_logger(__name__)

# 파싱할 것이 없는 형식. 파일을 열면 글자가 이미 다 있다.
_PLAIN = {".txt", ".md"}

# 태그를 걷어내야 글자가 남는 형식.
_HTML = {".html", ".htm"}

# 상용 파서 API 에 보내지 않을 형식. 사내 규정이 대외비를 품고 있어서다.
_LOCAL_ONLY = {".hwp", ".hwpx"}


# 파일 하나를 읽어 형식과 무관한 한 가지 모양(ParsedDoc)으로 돌려준다.
# - 분기 순서가 설계다 
# - 뒤에 올수록 '그 앞에서 안 걸린 것'이 온다.
def parse(path: str | Path, *, use_upstage: bool = False) -> ParsedDoc:
    p = Path(path)
    ext = p.suffix.lower()

    if ext in _PLAIN:
        return _parse_plain(p)
    if ext in _HTML:
        return _parse_html(p)
    # _LOCAL_ONLY 검사가 이 자리에 있어야 한다. 스위치를 켜도 한글 문서는 안 나간다.
    # 기술 선택이 아니라 보안 결정이라 설정으로 뒤집히면 안 된다.
    if use_upstage and ext not in _LOCAL_ONLY:
        from app.integrations.upstage import UpstageParser

        return UpstageParser().parse(str(p))
    return parse_local(p)


# 글자만 든 파일. 빈 줄로 잘라 문단 단위 블록을 만든다.
def _parse_plain(p: Path) -> ParsedDoc:

    # 마크다운은 제목(#)이 있어서 따로 다룬다. 빈 줄로만 자르면 제목이 블록이 된다.
    if p.suffix.lower() == ".md":
        return _parse_markdown(p)
    text = _read_text(p)
    blocks = [
        ParsedBlock("조항", f"{p.name} · {i + 1}단락", part.strip())
        for i, part in enumerate(text.split("\n\n"))
        if part.strip()
    ]
    return ParsedDoc(blocks=blocks, page_count=1, table_count=0)


# 인코딩을 모르는 파일을 읽는다. 사내 문서에는 cp949 로 저장된 txt 가 섞여 있다.
def _read_text(p: Path) -> str:

    raw = p.read_bytes()
    # utf-8-sig 를 먼저 본다. BOM 이 있으면 떼고, 없으면 utf-8 과 같게 동작한다.
    for enc in ("utf-8-sig", "cp949"):
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError:
            continue                      # 이 인코딩이 아니면 다음 것으로
        if enc != "utf-8-sig":
            # cp949 로 읽혔다는 것은 기록해 둔다. 글자가 깨져 보일 때 여기를 먼저 본다.
            log.info("인코딩을 %s 로 읽었습니다: %s", enc, p.name)
        return text
    # 둘 다 아니면 읽히는 만큼 읽는다. 예외를 올려 적재 전체를 멈추지 않는다.
    log.warning("인코딩을 알 수 없어 글자를 바꿔 읽었습니다: %s", p.name)
    return raw.decode("utf-8", errors="replace")  # ◀ 추가 끝


# 마크다운. 제목을 블록으로 만들지 않고 locator 로 올린다.
# '## 1. 신청' 이 8자짜리 블록이 되면 뜻 없는 조각이 검색 결과를 채운다.
# 제목을 출처로 쓰면 '어느 절에서 나온 답인지'가 그대로 남는다.
def _parse_markdown(p: Path) -> ParsedDoc:
    import re

    text = _read_text(p)
    blocks: list[ParsedBlock] = []
    locator = p.name                       # 첫 제목이 나오기 전까지는 파일 이름이 출처다
    buffer: list[str] = []                 # 제목 아래로 모이는 본문

    # 모인 본문을 블록 하나로 만들고 비운다. 제목을 만날 때와 파일이 끝날 때 부른다.
    def flush() -> None:
        body = "\n".join(buffer).strip()
        if body:
            blocks.append(ParsedBlock("조항", locator, body))
        buffer.clear()

    for line in text.split("\n"):
        # #~###### 과 공백까지 봐야 한다. '#태그' 같은 줄을 제목으로 잡지 않기 위해서다.
        if re.match(r"#{1,6}\s", line):
            flush()                        # 앞 절을 먼저 닫고
            locator = line.lstrip("#").strip()   # 이 제목을 다음 절의 출처로 쓴다
        else:
            buffer.append(line)
    flush()                                # 마지막 절은 반복문이 끝난 뒤에 닫는다
    return ParsedDoc(blocks=blocks, page_count=1, table_count=0)


# HTML. 표를 먼저 떼어낸 뒤 본문의 태그를 지운다.
def _parse_html(p: Path) -> ParsedDoc:
    import re

    raw = _read_text(p)
    # <head> 를 통째로 지운다. <title> 의 글자가 본문에 섞여 들어오는 것을 막는다.
    raw = re.sub(r"<head.*?</head>", " ", raw, flags=re.S | re.I)
    # <script> <style> 안의 글자는 본문이 아니다. 코드가 규정 문장처럼 검색되면 안 된다.
    # \1 은 앞에서 잡은 태그 이름을 다시 쓴다 — <script> 를 </style> 로 닫지 못하게.
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)

    # 표를 모아 두고 본문에서는 뺀다. 순서가 반대면 표가 본문에 녹아
    # 어디가 열 이름이고 어디가 값인지 알 수 없게 된다.
    tables = re.findall(r"<table.*?</table>", raw, flags=re.S | re.I)
    body = re.sub(r"<table.*?</table>", " ", raw, flags=re.S | re.I)
    body = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()

    blocks = [ParsedBlock("조항", p.name, body)] if body else []
    for i, table in enumerate(tables, 1):
        cleaned = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", table)).strip()
        blocks.append(ParsedBlock("표", f"{p.name} · 표{i}", cleaned))
    return ParsedDoc(blocks=blocks, page_count=1, table_count=len(tables))

