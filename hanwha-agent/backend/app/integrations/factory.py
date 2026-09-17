# 유일한 mock / live 분기 지점
# - 서비스는 get_llm() 만 부르고, 받은 것이 어떤 어댑터인지 모른다 (반환 타입이 LLMPort)
from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.core.exceptions import ModeNotAvailable
from app.integrations.ports import LLMPort

# Claude 어댑터를 하나 만들어서 재사용
# - @lru_cache : 인자가 없는 함수라 첫 호출 결과(어댑터 객체)가 계속 재사용된다
# - 주의 : 만들어진 시점의 모델명·키를 계속 쥐고 있다
#          실행 중에 .env 를 바꾸면 _live_llm.cache_clear() 로 비워야 반영된다
@lru_cache
def _live_llm() -> LLMPort:
    # claude import
    # - 실제로 live 모드일 때만 import하도록 _live_llm() 함수 내에서만 ClaudeLLM 사용
    # - mock 모드에서는 llm_claude 와 anthropic SDK 가 아예 로드되지 않는다
    from app.integrations.llm_claude import ClaudeLLM
    return ClaudeLLM()

# 지금 설정에 맞는 LLM 어댑터를 돌려주는 함수
def get_llm() -> LLMPort:
    settings = get_settings()
    # mock 일 때 live 어댑터를 대신 돌려주지 않고 막는다
    # - 가짜 어댑터가 아직 없는 상태에서 조용히 live 로 넘기면, 개발·테스트 중에 실제 과금이 발생한다
    if not settings.is_live:
        raise ModeNotAvailable(
            # 문자열 두 개를 나란히 쓰면 공백 없이 붙으므로, 앞 문자열 끝에 공백을 둔다
            "테스트용 mock 어댑터는 만들지 않았습니다. "
            ".env의 APP_MODE의 값이 live인지 확인해주세요."
        )
    return _live_llm()
