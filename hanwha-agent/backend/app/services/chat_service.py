from __future__ import annotations

import time

import app.integrations.factory as factory

from pydantic import ValidationError

from app.core.config import get_settings
from app.core.exceptions import NotFound
from app.core.guards import check_question
from app.core.logging import get_logger
from app.db.session import session_scope
from app.models import Run, UsageLog
from app.schemas.chat import AnswerOut, AskOut
from app.services.ids import next_run_id

log = get_logger(__name__)

# 첫 호출 1회 + 재시도 2회 = 3회
MAX_ATTEMPTS = 3

# 폴백 답변 본문
FALLBACK_ANSWER = "요청을 처리했지만 근거를 확인하지 못했습니다. 담당 부서에 문의해 주세요."

# 질문자 (임시)
DEFAULT_USER = {"name": "김민준", "dept": "인프라사업부 2팀"}

# 근거 문서 목록.
NO_CONTEXTS: list[dict] = []

# pydantic 의 오류 목록을 모델에게 다시 보낼 한 줄의 문장으로 변경해서 리턴 : 재시도 힌트
def _hint_from(errors: list[dict]) -> str:
    # errors : ValidationError 가 돌려주는 목록
    parts = []
    for err in errors:
        where = ".".join(str(x) for x in err.get("loc", ())) or "(최상위)"
        parts.append(f"{where}: {err.get('msg', '')}")
    return "/".join(parts)

# fallback : 재시도 다 사용뒤 사용자에게 보낼 답 리턴해주는 함수
def _fallback(run_id: str, attempts: int) -> AskOut:
    # 사용자에게 응답해줄 최종 응답 결과
    return AskOut(
        answer=FALLBACK_ANSWER,
        sources=[],
        enough_evidence=False,
        run_id=run_id,
        attempts=attempts,
        fallback_used=True
    )

# 호출 한 번의 사용량과 원가를 usage_logs 에 남기는 함수
# - run_id : 실행 고유번호. runs.id 를 가리키는 FK 라 Run 행이 먼저 들어가 있어야 한다
# - result : 어댑터가 돌려준 LLMResult
# - runs 가 "질문 한 건"이라면 usage_logs 는 "호출 한 번"이다
#   재시도가 돌면 한 run_id 에 행이 여러 개 붙는다 (재시도 한 번이 곧 과금 한 번이라서)
def _record_usage(run_id: str, result) -> None:
    # 관측(langfuse_client)과 같은 판단이다 : 기록에 실패해도 답변은 나가야 한다
    # - 사용량을 남기려다 사용자 요청을 깨뜨리면 집계를 붙인 것이 손해가 된다
    # - 다만 조용히 넘어가므로, 테이블이 없거나 FK 가 어긋나도 경고만 찍히고 행은 안 쌓인다
    try:
        with session_scope() as session:
            session.add(
                UsageLog(
                    run_id=run_id,
                    model=result.model,
                    input_tok=result.input_tok,
                    cache_tok=result.cache_tok,
                    output_tok=result.output_tok,
                    cost_krw=result.cost_krw,
                )
            )
    except Exception as e:
        log.warning("사용 기록 실패(무시하고 계속): %s", e)


# 본체 : 질문 하나에 대답하기
# - run_id 기본값이 "RUN-0000" 에서 None 으로 바뀌었다
#   안 주면 DB 를 보고 다음 번호를 직접 만든다 (services/ids.py)
def ask(*, question: str, run_id: str | None = None, user_id: int = 1) -> AskOut:
    #1. 가드 호출 -> 여기서 던져진 예외는 이 함수를 통과해 전역 핸들러까지 올라간다.
    q = check_question(question)

    # 2. 어댑터 한 개.
    llm = factory.get_llm()

    # 함수 안에서 import 하는 이유
    # - langfuse_client 는 factory 를 거치지 않는 어댑터라, 최상단에서 import 하면
    #   test_layers.py 의 "services 는 app.integrations.factory 만 본다" 규칙에 걸린다
    #   (그 검사는 ast 로 파일 최상단만 읽으므로 함수 안 import 는 통과한다)
    # - 규칙을 우회한 것이 아니라, 관측은 계층을 타고 흐르는 의존이 아니라
    #   어디서든 껐다 켤 수 있는 부수 기능이라는 판단이다
    from app.integrations.langfuse_client import score, trace
    from app.integrations.llm_claude import _extract_json

    started = time.perf_counter() # 시작시간

    # 3. 호출 전에 먼저 기록을 만든다
    # - 답을 받은 다음에 남기면, 호출 중에 서버가 죽은 요청은 흔적이 남지 않는다
    #   "진행중" 으로 먼저 넣어두면 끝나지 않은 요청도 DB 에 보인다
    # - with 블록을 빠져나올 때 커밋된다. 트레이스보다 이 블록을 먼저 닫아
    #   행이 확실히 들어간 뒤에 관측을 시작한다
    with session_scope() as session:
        if run_id is None:
            run_id = next_run_id(session) # run_id 없으면 생성
        session.add(
            Run(
                id=run_id,
                user_id=user_id,
                question=q,
                status="진행중",
                mode=get_settings().app_mode
            )
        )

    # 4. 여기서부터가 한 건의 트레이스
    # - 관측이 꺼져 있으면 trace() 는 아무것도 안 하고 with 블록만 그대로 지나간다
    with trace(
        "ask",
        run_id=run_id,
        user_id=str(user_id),
        metadata={"question_len" : len(q)},
    ):
        # 재시도 구조가 바뀌었다
        # - 전에는 성공하면 바로 return 했지만, 지금은 트레이스 안에서
        #   DB 마무리까지 해야 해서 out 에 담고 break 로 빠져나온다
        out = None
        hint = ""
        for attempt in range(1, MAX_ATTEMPTS + 1):
            # 5. llm 호출
            #   프롬프트 준비
            prompt = q if not hint else f"{q}\n\n[직전 응답의 문제] {hint}\n출력 형식을 지켜 다시 답해 주세요."
            #   llm에 질문 던지기
            result = llm.answer(question=prompt, contexts=NO_CONTEXTS, user=DEFAULT_USER)

            # 검증 "전에" 사용량을 남긴다
            # - 여기가 핵심이다. 응답이 규칙을 어겨 버려지더라도 그 호출의 토큰은 이미 과금됐다
            #   통과한 호출만 기록하면 재시도로 나간 비용이 장부에서 통째로 빠진다
            # - 그래서 attempts 가 2면 usage_logs 에도 행이 2건 쌓인다
            _record_usage(run_id, result)

            try:
                data = _extract_json(result.text)
                AnswerOut.model_validate(data)   # 규격에 맞는지 검사하는 부분
            except ValidationError as e:
                hint = _hint_from(e.errors(include_url=False))
                # log.warning(f"스키마 위반 {attempt}/{MAX_ATTEMPTS}회 : {hint}")
                log.warning("스키마 위반 %d/%d회 : %s", attempt, MAX_ATTEMPTS, hint)
                continue

            # 통과 시 out 변수에 담기
            out = AskOut(**data, run_id=run_id, attempts=attempt, fallback_used=False)
            break
        # end of for

        if out is None:
            # 3번 다 시도했다. 로그 남기고, 폴백 실행
            log.warning("스키마 검증에 %d회 모두 실패하여 폴백으로 응답합니다.(run_id=%s)", MAX_ATTEMPTS, run_id)
            out = _fallback(run_id, MAX_ATTEMPTS)
            # 폴백으로 빠진 것을 점수로 남긴다
            # - 로그는 사람이 찾아 읽어야 하지만, 점수는 "폴백 비율"로 집계된다
            score(run_id, "schema_ok", 0.0)

        # 6. 기록 마무리
        # - 처음 만든 행을 찾아 답과 시간을 채운다 (status "진행중" → "완료")
        with session_scope() as session:
            run = session.get(Run, run_id)  # run_id에 해당하는 레코드 한개 조회
            run.answer = out.answer
            run.status = "완료"
            run.latency_ms = int((time.perf_counter() - started) * 1000)
            # AnswerSource 객체 목록을 JSON 에 넣을 수 있게 dict 목록으로 바꾼다
            run.sources = [s.model_dump() for s in out.sources]

        return out


# 실행 기록 한 건 조회
# - 라우터가 그대로 내보낼 dict 를 만든다
#   모델 객체를 그냥 돌려주면 세션이 닫힌 뒤에 속성을 읽다가 터지고(DetachedInstance),
#   테이블 컬럼이 늘어날 때 응답이 조용히 같이 늘어난다
def get_run(*, run_id: str) -> dict:
    with session_scope() as session:
        run = session.get(Run, run_id) # PK로 레코드 한건 조회
        # 없는 번호는 404 로 끊는다. None 을 그대로 돌려주면 라우터가 200 에 빈 값을 내보낸다
        if run is None:
            raise NotFound(f"실행 기록을 찾을 수 없습니다: {run_id}")
        return {
            "run_id": run_id,
            "user_id": run.user_id,
            "question": run.question,
            "answer": run.answer,
            "status": run.status,
            "latency_ms":  run.latency_ms,
            "mode": run.mode,
            # 아직 안 채워졌으면 None 이 아니라 빈 목록으로 내보낸다 (화면에서 분기를 줄인다)
            "sources": run.sources or [],
            # datetime 은 JSON 으로 그대로 못 나가서 문자열로 바꾼다
            "created_at": run.created_at.isoformat(),
        }
