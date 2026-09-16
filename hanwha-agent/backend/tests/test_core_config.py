# 설정(Settings) 동작 검증
from app.core.config import get_settings

# get_settings 에 @lru_cache 가 걸려 있는지를 고정해두는 테스트
# - == 이 아니라 is 로 비교한다 : 값이 같은지가 아니라 "같은 객체인지"를 본다
# - 캐시가 빠지면 .env 를 매번 다시 읽게 되고, 이 테스트가 먼저 깨져서 알려준다
def test_get_settings_returns_same_instance() -> None:
    assert get_settings() is get_settings()

# 기본값 검증
# - app_mode 기본값이 mock 이어야 실수로 실제 LLM 호출이 나가지 않는다
def test_settings_has_defaults() -> None:
    settings = get_settings()
    assert settings.app_mode == "mock"
    assert settings.debug is False
