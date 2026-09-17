import sys
from pathlib import Path

# backend 폴더를 모듈 검색 경로로 잡기
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))

import anthropic

from app.core.config import get_settings

settings = get_settings()
# 환경변수에 세팅되어 있는 API키의 값 가져오기
key = settings.anthropic_api_key 

# 키값이 없으면
if key is None:
    print(".env의 anthropic_api_key가 비어있습니다. 확인해주세요.")
    # 프로그램 종료
    sys.exit(1)

# API 요청하는 클라이언트 생성
# - API key 인자로 전달
# - pydantic SecretStr 타입이 주는 메서드 활용
client = anthropic.Anthropic(api_key=key.get_secret_value())

# 메세지 생성하여 요청
# - 인자 값들을 환경변수에 지정된 값을 가져와 사용
# - AI-Native 아키텍처 설계 방침
response = client.messages.create(
    model=settings.llm_model,
    max_tokens=settings.max_tokens,
    system="너는 사내 규정 질의 응답 도우미야. 근거가 없으면 없다고 말해.",
    messages=[
        {
            "role": "user",
            "content": "제주도 출장 숙박비 한도는 얼마인가요?"
        }
    ]
)

# print(response)


print("".join(b.text for b in response.content if b.type == "text"))
print("입력 토큰: ", response.usage.input_tokens)
print("출력 토큰: ", response.usage.output_tokens)
# end_turn은 정상
print("멈춘 이유: ", response.stop_reason)
