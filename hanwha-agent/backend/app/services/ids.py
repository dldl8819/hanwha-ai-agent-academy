# 실행 번호 run_id 를 만들어 주는 모듈
# - run_id 를 DB 의 자동 증가 PK 로 두지 않는 이유는, 값을 "먼저" 알아야 하기 때문이다
#   LangFuse 트레이스 id, runs 테이블 PK, usage_logs 의 FK, GET /chat/runs/{run_id} 경로,
#   감사 로그까지 다섯 군데에서 같은 값을 써야 해서 호출을 시작하기 전에 정해둔다
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Run

# 수업용 시작 번호. RUN-0001 부터 쓰지 않는 이유는 눈으로 구분하기 쉽게 하기 위해서다
RUN_START = 8821


# 다음 run_id 를 만들어 주는 함수 : "RUN-8821" 형태로 리턴
def next_run_id(session: Session) -> str:
    # DB 에서 이미 쓰인 번호를 전부 읽는다
    # - 행이 늘어나면 전부 읽는 방식은 느려진다. 운영이라면 시퀀스나 max() 쿼리로 바꿀 자리다
    used = session.scalars(select(Run.id)).all()

    # 아무 행도 없을 때 max() 가 빈 목록으로 죽지 않도록 하는 바닥값
    numbers = [RUN_START - 1]
    for run_id in used:
        tail = run_id.removeprefix("RUN-")
        # 숫자가 아닌 꼬리("RUN-테스트" 같은 값)는 건너뛴다. int() 로 바로 넘기면 예외가 난다
        if tail.isdigit():
            numbers.append(int(tail))

    # :04d 는 8821 을 "8821" 로, 21 을 "0021" 로 채운다 → 문자열로 정렬해도 순서가 맞는다
    return f"RUN-{max(numbers) + 1:04d}"
