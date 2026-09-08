import logging
import sys

# 이미 설정했는지 기억해 두는 표식
_CONFIGURED = False

# 출력 모양 
_FORMAT = "%(asctime)s %(levelname)-8s %(name)s %(message)s"
_DATEFMT = "%H:%M:%S"

# 내 로그가 파묻히지 않도록 로그 줄여줄 라이브러리들 
_NOISY = ("httpx", "httpcore", "urllib3", "asyncio")

def setup_logging(level: int = logging.INFO, stream=None) -> None:

    # global : 함수 안에서 모듈의 전역 변수 수정 가능하게 해주는 명령어
    global _CONFIGURED
    if _CONFIGURED: # 설정을 이미 했으면 메서드 강제 종료
        return

    # 핸들러 : 로그를 어디로 내보낼지 설정
    handler = logging.StreamHandler(stream or sys.stdout)

    # formatter : 로그 1줄의 모양 설정
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))

    # 이름 없는 최상위 로거 설정
    root = logging.getLogger() 
    root.setLevel(level)
    root.handlers = [handler] # 기존 핸들러를 밀어내고 하나만 놓기 

    for name in _NOISY:
        logging.getLogger(name).setLevel(logging.WARNING)

    _CONFIGURED = True

# 로그 가져다 사용할 수 있도록 getter 만들기
def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)

    # name에는 __name__을 넣는다.
    # -> 로그에 모듈 경로가 찍혀 어느 파일에서 발생한 에러인지 바로 알 수 있다.