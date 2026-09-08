# [한화 내일 아카데미 ICT부문] 5일차 후기 — 레이어드 아키텍처, 예외 처리와 로깅, pytest, 네트워크·HTTP 기초

어제는 프로젝트 개발환경을 세팅하고 타입 힌트·Pydantic·환경변수의 기본기를 다뤘는데, 오늘은 그 위에 실제 서버 프로젝트에 필요한 구조와 도구들을 쌓아 올렸습니다. 한화 내일 아카데미 ICT부문 과정 2주차 두 번째 날로, 프로젝트 아키텍처부터 예외 처리, 로깅, 테스트, 그리고 오후에는 네트워크·HTTP 기초까지 다뤄서 하루 안에 다룬 범위가 꽤 넓었습니다.

오늘 학습한 내용을 순서대로 정리해봅니다.

1. 레이어드 아키텍처
2. 예외 계층 설계
3. 로깅
4. pytest
5. 네트워크와 HTTP 기초

## 1. 레이어드 아키텍처

로그인 확인, 권한 확인, 업무 규칙 처리, DB 조회, 외부 API(LLM) 호출, 로그 기록, 응답 생성까지 한 요청 안에서 처리할 일이 많은데, 이걸 `main.py` 한 파일에 순서대로 다 적으면 코드가 길어질수록 관리가 어려워집니다. 그래서 MVC 패턴을 더 세분화한 계층형(Layered) 구조로 나눕니다.

```text
frontend        Streamlit 화면
    | HTTP 요청
API             FastAPI Router — 요청을 받고 분배
    |
Schema          Pydantic — 요청/응답 데이터 형태 검증
    |
Service         비즈니스 로직 처리 (AI 기능도 여기)
    |
Repository      DB 접근
    |
Model           DB 테이블 정의
    |
PostgreSQL
```

각 계층은 자기 바로 아래 계층만 호출합니다. 예를 들어 DB를 SQLite에서 PostgreSQL로 바꿀 때 Repository 계층만 손보면 되고, 나머지 계층은 그대로 둘 수 있는 구조입니다.

## 2. 예외 계층 설계

API 에러를 사용자에게 그대로 노출하지 않고 상태 코드 + 코드 문자열 + 메시지로 응답하려면, 예외를 프로젝트 전용 클래스 계층으로 미리 설계해둬야 합니다.

```python
class AgentError(Exception):
    status_code = 400
    code = "agent_error"

    def __init__(self, message: str, *, detail: str | None = None):
        super().__init__(message)
        self.message = message
        self.detail = detail

class NotFound(AgentError):          # 요청한 자원이 없다
    status_code = 404
    code = "not_found"

class ExternalServiceError(AgentError):  # 외부 서비스 호출 실패
    status_code = 502
    code = "external_service_error"
```

모든 예외가 `AgentError`를 상속받기 때문에, `isinstance(exc, AgentError)` 한 번으로 "우리가 의도한 상황"인지 아닌지 구분할 수 있습니다. 여기에 속하지 않는 예외는 자동으로 500 처리로 빠지게 만들어서, 예상 못 한 에러가 내부 정보를 그대로 노출하지 않도록 막았습니다.

다른 예외를 잡아서 우리 예외로 다시 던질 때는 `raise ... from ...`으로 원인을 연결합니다.

```python
import json

def parse_bad(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValidationError(
            "데이터 형식이 올바르지 않습니다.",  # 사용자에게 보여줄 메시지
            detail=str(e),                    # 개발자용 원본 에러
        ) from e  # 원인 연결

try:
    parse_bad("{json 형식이 아닌 input}")
except ValidationError as e:
    print("원인 :", type(e.__cause__).__name__, e.__cause__)
```

`from e`로 연결해두면 `e.__cause__`로 원래 예외에 그대로 접근할 수 있어서, 사용자에게는 다듬어진 메시지를 보여주고 로그에는 원인을 그대로 남길 수 있습니다.

## 3. 로깅

로그 레벨은 DEBUG, INFO, WARNING, ERROR, CRITICAL 순으로 심각도가 올라갑니다. 노트북에서는 `logging.basicConfig()`로 실험했지만, 실제 프로젝트에서는 로깅 설정을 앱 전체에서 딱 한 번만 해야 합니다. 여러 모듈이 각자 `basicConfig()`를 부르면 핸들러가 중복으로 쌓여서 로그 한 줄이 여러 번 찍히기 때문입니다.

```python
_CONFIGURED = False
_NOISY = ("httpx", "httpcore", "urllib3", "asyncio")  # 너무 시끄러운 라이브러리는 레벨을 낮춤

def setup_logging(level: int = logging.INFO, stream=None) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]
    for name in _NOISY:
        logging.getLogger(name).setLevel(logging.WARNING)
    _CONFIGURED = True

def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
```

`config.py`의 `get_settings()`처럼 한 파일에서만 설정하고, 나머지 모듈은 `get_logger(__name__)`으로 가져다 쓰는 구조입니다. 예외 처리와 결합하면 내부적으로는 원인을 자세히 기록하고 사용자에게는 다듬어진 예외로 알려주는 흐름을 만들 수 있습니다.

```python
def ingest(doc_id):
    logger.info("적재 시작: %s", doc_id)
    try:
        text = fake_parsing(doc_id)
    except ConnectionError as e:
        logger.exception("문서 파싱 실패 : %s", doc_id)  # 스택 트레이스까지 로그에 남김
        raise ExternalServiceError("문서 변환 서비스에 연결하지 못했습니다.", detail=str(e)) from e
    logger.info("적재 완료: %s", doc_id)
    return text
```

로그에 API 키, 비밀번호, 토큰, 주민번호, 문서 원문 전체는 남기면 안 된다는 것도 함께 배웠습니다. `SecretStr` 타입으로 애초에 값이 `print`나 로그에 안 찍히게 막아두는 것도 같은 맥락입니다.

## 4. pytest

pytest는 내가 만든 코드가 예상대로 동작하는지 자동으로 검사해주는 테스트 프레임워크입니다. 별도로 "이 테스트를 실행하라"고 등록하는 곳이 없고, 이름 규칙이 곧 등록입니다 — 파일명은 `test_*.py`, 함수명은 `test`로 시작해야 pytest가 찾아서 실행합니다.

```python
from calculator import add, substract

def test_add():
    result = add(10, 20)
    assert result == 30

def test_substract():
    result = substract(10, 3)
    assert result == 7
```

`assert 조건`이 참이면 통과, 거짓이면 실패로 표시됩니다. 실행은 `pytest 파일경로 -v`로 합니다.

이 실습 중에 흥미로운 이슈를 하나 만났는데, 테스트 폴더 안에 빈 `__init__.py`를 넣어뒀더니 바로 옆의 `calculator.py`를 못 찾고 `ModuleNotFoundError`가 났습니다. pytest는 테스트 파일이 있는 폴더에 `__init__.py`가 있으면 그 폴더를 패키지로 보고, `__init__.py`가 없는 첫 상위 폴더를 `sys.path`에 넣기 때문입니다. 스크립트와 테스트를 나란히 두고 그 파일만 바로 돌리는 구조에서는 `__init__.py`를 넣지 않는 게 맞다는 걸 직접 에러를 겪으며 확인했습니다.

## 5. 네트워크와 HTTP 기초

오후에는 코드에서 한발 물러나 네트워크 기본 개념을 정리했습니다. 네트워크에 연결된 장치는 노드(Node), 그중 서비스를 제공하는 노드는 호스트(Host)라고 부릅니다. 인터넷은 컴퓨터들이 TCP/IP로 연결된 전 세계 네트워크이고, 웹은 그 인터넷 서비스 중 하나입니다.

웹은 클라이언트(브라우저)가 요청(request)을 보내면 서버(uvicorn 등)가 응답(response)을 돌려주는 클라이언트-서버 방식으로 동작합니다. 정확한 서버에 요청을 보내려면 그 서버의 IP 주소가 필요하고, IP는 32비트(IPv4) 또는 128비트(IPv6)로 구성됩니다. IP 프로토콜 자체는 비연결성(받을 대상이 없어도 일단 전송)과 비신뢰성(순서 보장 없음)이라는 한계를 가져서, 이를 보완하기 위해 연결 지향에 순서를 보장하는 TCP가 쓰입니다. 반대로 UDP는 순서 보장을 포기하는 대신 속도가 빨라서 스트리밍 같은 곳에 쓰입니다.

같은 IP 안에서 여러 서비스가 충돌 없이 동작하도록 구분해주는 게 포트(Port)입니다. HTTP는 80, HTTPS는 443처럼 잘 알려진 포트는 임의로 지정할 때 피합니다. 그리고 IP 주소를 외우기 쉬운 이름으로 바꿔주는 DNS, 그 자원의 위치를 식별하는 URI까지 이어서 배웠습니다.

```text
https://www.google.com/search?q=hello&oq=hello

* 프로토콜   : https
* IP        : www.google.com (도메인이 IP를 대신함)
* Port      : 443 (https 기본 포트라 생략됨)
* 경로       : /search
* 쿼리스트링  : ?q=hello&oq=hello
```

URI 뒤에 `#`으로 붙는 fragment는 같은 페이지 안의 특정 위치를 저장해두는 용도입니다. 서버로는 전송되지 않고 브라우저가 그 페이지를 받은 뒤 해당 위치로 스크롤해주는 역할만 합니다.

## 오늘의 소감

어제까지는 개별 라이브러리(Pydantic, dotenv) 사용법 위주였다면, 오늘은 그 도구들을 실제로 어떻게 조합해서 하나의 서버 프로젝트 구조를 만드는지에 가까운 하루였습니다. 특히 pytest 실습에서 `__init__.py` 하나 때문에 import 경로가 완전히 달라지는 걸 직접 에러로 겪어보니, 왜 폴더 구조를 이렇게 나누는지 이유가 더 분명해졌습니다. 오후의 네트워크·HTTP 기초는 그동안 당연하게 써왔던 URL 구조를 프로토콜·IP·포트·경로·쿼리로 뜯어서 다시 보는 시간이었습니다.

다음 포스팅에서는 이어서 배울 내용을 정리해보겠습니다.

---

\#한화내일아카데미 #한화시스템 #AI개발자 #AI에이전트 #레이어드아키텍처 #예외처리 #로깅 #pytest #네트워크 #HTTP #K뉴딜아카데미 #국비지원교육 #개발자이직 #부트캠프후기

참고 링크 : https://blog.naver.com/dldl8819/224405026520
