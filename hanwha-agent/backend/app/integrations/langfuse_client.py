# LangFuse 어댑터
# - 이 파일의 원칙 하나 : 관측이 실패해도 답변은 나가야 한다
#   기록을 남기려다 사용자 요청을 깨뜨리면 관측 도구를 붙인 것이 손해가 된다
#   그래서 모든 함수가 예외를 삼키고, 못 하면 조용히 아무것도 안 한 것처럼 지나간다
from __future__ import annotations

from contextlib import contextmanager

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)

# 클라이언트를 한 번만 만들어 재사용한다
# - factory 처럼 @lru_cache 를 쓰지 않고 전역 변수를 쓴 이유는 "실패도 기억"해야 하기 때문이다
#   만들기에 실패했을 때 None 을 캐시해 두면 요청마다 다시 시도하며 로그를 쏟지 않는다
_client = None
_tried = False


# LangFuse 클라이언트 하나를 만들어 주는 함수. 못 만들면 None 을 돌려준다
# - 예외를 던지지 않는다. 부르는 쪽이 None 만 확인하면 되게 한다
def get_client():
    global _client, _tried
    if _tried:
        return _client
    _tried = True

    # 설정을 모듈 최상단이 아니라 함수 안에서 읽는다
    # - import 시점에 값을 굳혀두면 테스트가 .env 를 갈아끼워도 반영되지 않는다
    settings = get_settings()

    # 끄고 쓸 수 있어야 한다. 기본값이 false 라 아무 설정도 하지 않으면 관측은 그냥 꺼져 있다
    if not settings.langfuse_enabled:
        return None

    # 켜두고 키를 안 넣은 경우는 사람의 실수라 한 번 알려준다
    if not settings.langfuse_public_key or settings.langfuse_secret_key is None:
        log.warning("LANGFUSE_ENABLED=true 인데 키가 비어 있습니다. 관측을 건너뜁니다.")
        return None

    try:
        # SDK import 도 함수 안에서 한다
        # - 관측을 끄고 쓰는 사람은 langfuse 를 설치하지 않아도 앱이 돌아간다
        from langfuse import Langfuse

        _client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key.get_secret_value(),
            host=settings.langfuse_host,
        )
    except Exception as e:
        # 여기서 Exception 을 통째로 잡는 것은 의도한 것이다
        # - 패키지 미설치(ImportError), 주소 오타, 키 형식 오류가 전부 여기로 온다
        #   무엇이 왔든 "관측만 포기"가 정답이라 종류별로 나눌 이유가 없다
        log.warning("Langfuse 클라이언트를 만들지 못하였습니다 (무시하고 계속) : %s", e)
        _client = None

    return _client


# 첫 실패만 크게 알리고, 그 다음부터는 조용히 남기기 위한 표시
_warned = False


# 관측 실패를 남기는 함수 : 처음 한 번만 warning, 그 다음부터는 debug
# - 관측이 막혀 있으면 요청마다 같은 경고가 찍혀 로그가 정작 봐야 할 것을 덮는다
def _quiet(message: str, e: Exception) -> None:
    # message : 무엇을 하다 실패했는지 / e : 예외
    global _warned
    if not _warned:
        _warned = True
        log.warning("%s (무시하고 계속): %s", message, e)
    else:
        log.debug("%s: %s", message, e)


# 실행 하나를 트레이스 하나로 감싸는 함수
# - with 문으로 쓰도록 @contextmanager 로 만들었다
@contextmanager
def trace(name: str, *, run_id: str, user_id: str = "", metadata: dict | None = None):
    # name     : 트레이스 이름
    # run_id   : 이 실행의 고유 번호. LangFuse 트레이스 id 로 그대로 넘긴다
    #            우리가 정한 번호를 id 로 쓰기 때문에 화면과 DB 를 같은 값으로 찾아갈 수 있다
    # user_id  : 누가 물었나 (문자열)
    # metadata : 화면에서 함께 보고 싶은 값들
    client = get_client()
    handle = None
    if client is not None:
        try:
            handle = client.trace(
                id=run_id,
                name=name,
                user_id=user_id,
                metadata=metadata or {},
            )
        except Exception as e:
            _quiet("Langfuse 트레이스를 시작하지 못했습니다.", e)

    try:
        # 관측이 꺼져 있으면 handle 이 None 이다
        # - 부르는 쪽은 with 블록을 그대로 쓰고, 안에서 handle 을 쓸 때만 None 을 확인하면 된다
        yield handle
    finally:
        # 일부러 비워둔다
        # - v2 SDK 는 trace 를 닫는 호출이 따로 없고 flush 로 전송한다
        # - 그래도 try/finally 를 남겨둔 이유는, 나중에 닫는 처리가 생겼을 때
        #   with 블록 안에서 예외가 나도 실행될 자리를 미리 만들어 두는 것이다
        pass


# 트레이스 하나에 점수를 붙이는 함수
# - "잘 돌았나"가 아니라 "답이 쓸 만했나"를 숫자로 남기는 자리다 (골든셋 통과 여부 등)
def score(run_id: str, name: str, value: float) -> None:
    # run_id : 점수를 붙일 트레이스 id
    # name   : 점수 이름
    # value  : 점수 값. 0.0 = 폴백, 1.0 = 정상
    client = get_client()
    if client is None:
        return
    try:
        client.score(
            trace_id=run_id,
            name=name,
            value=value,
        )
    except Exception as e:
        _quiet("Langfuse 점수를 남기지 못했습니다.", e)
