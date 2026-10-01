from __future__ import annotations
import re
from dataclasses import dataclass
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.integrations.ports import ParsedDoc

# 제1조, 제12조(숙박비),
# - 괄호 제목을 필수로 둔다. 선택으로 두면 "제32조 에 따라 반환한다" 처럼
#   문장 안에서 다른 조를 가리키는 말까지 조 제목으로 잡힌다(실문서에서 27건).
# - ^[ \t]* 와 re.M 으로 줄머리만 본다. 앞 공백은 들여쓰기라 허용한다.
_ARTICLE = re.compile('^[ \\t]*(제\\s*\\d+\\s*조(?:의\\s*\\d+)?\\s*\\([^)\\n]{1,30}\\))', re.M)
# 별표1 ..
# - 본문 어디에 있어도 찾는다. locator 뒤에 " · 별표1" 로 붙여 어느 별표를 가리키는지 남긴다.
_ANNEX = re.compile('(별표\\s*\\d+)')
# 장,절,부칙 제목 줄
# - 줄 전체가 제목인 줄만 잡는다($ 로 끝을 막는다). 그래서
#   "제4장의 특례를 적용한다" 같은 문장은 걸리지 않는다.
_HEADING = re.compile('^[ \\t]*(?:(제\\s*\\d+\\s*장)|(제\\s*\\d+\\s*절)|(부\\s*칙))(?:[ \\t]+[^\\n]{1,30})?[ \\t]*$')
# 별표,서식 제목 줄
# - [별표2], [별지 제1호 서식] 처럼 대괄호로 시작하는 줄. 장·절 밖에 있는 부록이라
#   여기서부터는 장 정보를 버리고 별표 이름만 locator 로 쓴다.
_ANNEX_HEAD = re.compile('^[ \\t]*\\[(별표\\s*\\d+|별지[^\\]]{0,20})\\]')

MAX_CHARS = 1200   # 청크 하나의 최대 길이. 넘으면 _hard_wrap 으로 다시 자른다
MIN_CHARS = 30     # 첫 조 앞 머리말이 이보다 짧으면 청크로 만들지 않는다
TOC_BODY_MIN = 10  # 조 제목 뒤 본문이 이보다 짧으면 목차 줄로 본다

# 청킹 결과 한 건. 임베딩·적재 직전 단계의 초안
@dataclass
class ChunkDraft:
    kind: str     # 조항 | 표
    locator: str  # 원본 어디서 나왔는지 : 제3장 제2절 제14조(숙박비), 표2
    text: str     # 임베딩할 본문

# 조 단위로 자르기
# 반환값: (조 제목, 제목을 포함한 본문) 쌍의 목록. 제목이 없는 덩어리는 제목 자리가 ''
def _split_articles(text: str) -> list[tuple[str, str]]:
    # 패턴을 괄호 하나로 감쌌으므로 split 결과가 [머리말, 제목1, 본문1, 제목2, 본문2, ...] 로 나온다.
    # 괄호를 안 씌우면 제목이 사라져 출처를 못 적고, 안쪽까지 씌우면 홀짝 규칙이 깨진다.
    parts = _ARTICLE.split(text)
    if len(parts) <= 1:
        # 조가 하나도 없으면 전체를 한 덩어리로 넘긴다
        return [('', text.strip())] if text.strip() else []
    out: list[tuple[str, str]] = []
    # 첫 조 앞의 머리말은 충분히 길 때만 남긴다
    head = parts[0].strip()
    if len(head) >= MIN_CHARS:
        out.append(('', head))
    # 1번부터 두 칸씩 건너뛰며 (제목, 본문) 쌍으로 묶는다
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ''
        # 검색 결과만 봐도 어느 조인지 알 수 있게 본문 앞에 제목을 붙인다
        out.append((title, f'{title} {body}'.strip()))
    return out

# 장,절 제목 줄에서 끊고, 그 줄은 본문에서 제외
# where 는 호출 사이에 유지되는 상태다. 표를 만나 flush 가 여러 번 돌아도
# "지금 몇 장 몇 절인지" 가 이어지게 chunk() 가 하나를 만들어 돌려 쓴다.
def _split_headings(text: str, where: dict) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    lines: list[str] = []
    for line in text.split('\n'):
        m = _HEADING.match(line)
        annex = _ANNEX_HEAD.match(line)
        if not m and (not annex):
            lines.append(line)
            continue
        # 제목 줄을 만났으니 여기까지 모인 본문을 "그 전까지의 위치" 로 끊어 낸다
        if lines:
            out.append((where['at'], '\n'.join(lines)))
            lines = []
        if annex:
            # 별표·서식은 장·절 밖이다. 장 정보를 버리고 별표 이름만 위치로 쓴다.
            where['chapter'], where['section'] = ('', '')
            where['at'] = re.sub('\\s+', ' ', annex.group(1)).strip()
            # 제목 줄을 본문에 남긴다 — 이 줄 자체가 별표의 시작이라 내용의 일부다
            lines.append(line)
            continue
        chapter, section, _ = m.groups()
        if chapter:
            # 장이 바뀌면 절은 초기화한다. 안 그러면 앞 장의 절이 따라붙는다.
            where['chapter'], where['section'] = (re.sub('\\s+', '', chapter), '')
        elif section:
            where['section'] = re.sub('\\s+', '', section)
        else:
            # 부칙은 장 자리에 넣는다. 본문 장 번호와 섞이지 않게.
            where['chapter'], where['section'] = ('부칙', '')
        where['at'] = ' '.join((x for x in (where['chapter'], where['section']) if x))
        # 장·절 제목 줄은 본문에 남기지 않는다 — locator 로 올라갔으므로 중복이다
    if lines:
        out.append((where['at'], '\n'.join(lines)))
    return out

# 길이가 아주 긴 조를 limit 이하로 나누기 (폴백)
def _hard_wrap(text: str, limit: int=MAX_CHARS) -> list[str]:
    if len(text) <= limit:
        return [text]
    # 문단 → 줄 → 문장 끝("다. ") → 공백 → 글자 순으로 자를 곳을 찾는다.
    # "다. " 가 들어 있는 것이 한국어 규정에 맞춘 부분이다.
    # keep_separator="end" 로 구분자를 앞 조각 끝에 남겨 "~한다." 가 온전히 끝나게 한다.
    # chunk_overlap=0 인 이유는 한 조 안이라 앞뒤를 겹쳐 붙일 필요가 없어서다.
    splitter = RecursiveCharacterTextSplitter(chunk_size=limit, chunk_overlap=0, separators=['\n\n', '\n', '다. ', '. ', ' ', ''], keep_separator='end')
    return splitter.split_text(text)

# ParsedDoc -> 청크 목록으로 변환해서 리턴
# 표는 블록 하나를 그대로 청크로 만들고, 나머지 본문 블록은 buffer 에 모았다가 조 단위로 다시 자른다
def chunk(doc: ParsedDoc) -> list[ChunkDraft]:
    out: list[ChunkDraft] = []
    buffer: list[str] = []  # 아직 청크로 만들지 않은 본문. 조 하나가 블록 여럿에 걸칠 수 있어 모아 둔다
    buffer_locator = ''     # buffer 에 처음 들어온 블록의 위치. 장·조를 못 찾았을 때 쓰는 대체값
    where = {'chapter': '', 'section': '', 'at': ''}  # flush 사이에 유지되는 현재 장·절

    # buffer 에 모인 본문을 조 단위 청크로 바꿔 out 에 넣고 buffer 를 비운다
    def flush() -> None:
        nonlocal buffer, buffer_locator
        if not buffer:
            return
        out.extend(_articles_from('\n'.join(buffer), buffer_locator, where))
        buffer = []
        buffer_locator = ''
    for block in doc.blocks:
        if block.kind == '표':
            # 표가 나오면 앞에 쌓인 본문부터 청크로 만든 뒤 표를 넣는다.
            # 순서를 안 지키면 표가 앞서고 본문이 뒤로 밀린다.
            flush()
            out.append(ChunkDraft('표', block.locator, block.text))
            continue
        if not buffer_locator:
            buffer_locator = block.locator
        buffer.append(block.text)
    # 문서 끝에 남은 본문 처리
    flush()
    return out

# 본문 덩어리를 조 단위로 자르는 함수
def _articles_from(text: str, fallback_locator: str, where: dict) -> list[ChunkDraft]:
    drafts: list[ChunkDraft] = []
    # 두 단계다. 먼저 장·절로 끊어 각 덩어리의 위치(at)를 알아내고, 그 안에서 조로 다시 끊는다.
    items = [(at, title, body) for at, part in _split_headings(text, where) for title, body in _split_articles(part)]
    for at, title, body in items:
        if not body.strip():
            continue
        # 제목을 뺀 실제 내용. 이게 짧으면 목차 줄이다.
        remainder = body[len(title):].strip() if title else body
        # [별표2] 한 줄만 있는 덩어리도 목차처럼 다룬다 — 제목만 있고 내용이 아직 안 나온 상태다
        if not title and '\n' not in body.strip() and _ANNEX_HEAD.match(body):
            remainder = ''
        if len(remainder) < TOC_BODY_MIN:
            # 목차 줄은 따로 청크로 만들지 않는다. 뜻이 없는 조각이 검색 결과를 채우기 때문이다.
            # 앞 청크에 붙여 두면 "제1장에 이런 조들이 있다" 는 정보는 남는다.
            if drafts:
                drafts[-1].text += '\n' + body
            else:
                drafts.append(ChunkDraft('조항', at or fallback_locator, body))
            continue
        if not title:
            locator = at or fallback_locator
        else:
            annex = _ANNEX.search(body)
            # "제3장 제2절 제14조(숙박비)" 처럼 장·절을 조 앞에 붙인다.
            # 검색 결과만 보고도 규정 어디인지 알 수 있어야 ⑪ Citation 에 쓸 수 있다.
            locator = f'{at} {title}'.strip()
            locator = locator if not annex else f'{locator} · {annex.group(1)}'
        pieces = _hard_wrap(body)
        for i, piece in enumerate(pieces):
            # 한 조가 쪼개졌으면 (1/2) 를 달아 어느 조의 몇 번째 조각인지 남긴다
            suffix = f' ({i + 1}/{len(pieces)})' if len(pieces) > 1 else ''
            drafts.append(ChunkDraft('조항', f'{locator}{suffix}', piece))
    return drafts

# 요약 문구 생성
def summarize(chunks: list[ChunkDraft]) -> str:
    articles = sum((1 for c in chunks if c.kind == '조항'))
    tables = sum((1 for c in chunks if c.kind == '표'))
    return f'조항 단위 {articles} + 표 단위 {tables} = {len(chunks)} 청크'
