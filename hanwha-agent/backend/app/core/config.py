from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from functools import lru_cache

from app.models.base import EMBED_DIM

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False # APP_MODE 든 app_mode든 같은 것으로 보게 설정 
    )
    
    # --- 실행 모드 ---
    # 기본값 mock으로 설정
    # - mock이 아니면 live로 설정
    app_mode: str = Field(default="mock", pattern=r"^(mock|live)$")
    # --- LLM --------------------------------------------------------
    anthropic_api_key: SecretStr | None = None
    llm_model: str = "claude-haiku-4-5"
    max_tokens: int = Field(default=400, ge=1, le=8192)
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    daily_call_limit: int = Field(default=200, ge=1)
    max_input_chars: int = Field(default=200, ge=1)
    # --- DB ------------------------------
    database_url: str = "sqlite:///./app.db"
    debug: bool = False
    allow_external_send: bool = False
    # 실습 - 환경변수 값 추가 upstage_api_key
    upstage_api_key: SecretStr | None = None
    upstage_base_url: str = "https://api.upstage.ai/v1"
    upstage_parse_model: str = "document-parse"
    upstage_parse_ocr: str = "auto"  
    # --- embedding ---------------------------------------------
    embed_provider: str = Field(default="local", pattern=r"^(local|upstage)")
    # 가중치는 저장소 바깥(프로젝트 루트의 ../models)에 둔다 — git 에 올리지 않는다
    embed_model_dir: str = "../models/bge-m3"
    embed_dim: int = EMBED_DIM
    upstage_embed_model: str | None = None

    # --- 검색 ---------------------------------------
    # 임계값: 가장 가까운 근거가 이 점수에 못 미치면 '근거 부족'
    #   벡터 검색은 맞는 답이 없어도 가장 가까운 것을 돌려준다.
    #   그 사실을 숫자 하나로 가리는 자리라 값의 근거가 약하다는 점을 알고 쓴다.
    retrieval_threshold: float = Field(default=0.60, ge=0.0, le=1.0)
    # 벡터 검색이 받아올 후보 갯수
    retrieval_top_k: int = Field(default=12, ge=1, le=100)
    # 질문을 몇 갈래까지 늘리는가
    multi_query_n: int = Field(default=3, ge=1, le=10)
    # 다시 줄 세운 뒤 몇 건을 남길 것인가
    rerank_top_n: int = Field(default=3, ge=1, le=20)

    # --- 리랭커 ---
    # simple : 간이 리랭커, cross_encoder : 모델이 질문과 조각을 한 번에 읽어 점수를 매김
    reranker: str = Field(default="simple", pattern=r"^(simple|cross_encoder)$")
    rerank_model_dir: str = "../models/bge-reranker-v2-m3"
    rerank_candidates: int = Field(default=12, ge=1, le=100)
    # 질문 + 조각을 합쳐 이 토큰 수에서 자른다. (문서에 따라 수정이 필요하다.)
    rerank_max_length: int = Field(default=512, ge=64, le=8192)
    # 크로스 인코더 점수가 0 ~ 1 범위에 못 미치면 근거 부족
    rerank_threshold: float = Field(default=0.2, ge=0.0, le=1.0)


    # --- 관측 langfuse ---
    # 기본값을 False 로 둔다
    # - 관측은 있으면 좋은 것이고, 없어서 앱이 멈춰서는 안 된다
    # - 키를 안 넣은 사람도, langfuse 를 설치하지 않은 사람도 그대로 실행된다
    langfuse_enabled: bool = False
    # 셀프 호스팅 기본 주소. 클라우드면 https://cloud.langfuse.com (리전별로 주소가 다르다)
    langfuse_host: str = "http://localhost:3000"
    # public key 는 pk-lf-... 로 시작하고 화면에서 다시 볼 수 있어 SecretStr 로 두지 않았다
    langfuse_public_key: str | None = None
    # secret key 는 sk-lf-... 로 시작한다. 로그·print 에 실수로 찍히지 않게 SecretStr 로 감싼다
    langfuse_secret_key: SecretStr | None = None

    # live 모드인지 확인 
    # settings.app_mode == "live"
    # settings.is_live => True/False
    @property
    def is_live(self) -> bool:
        return self.app_mode == "live"

@lru_cache
def get_settings() -> Settings:
    return Settings()

def mask(secret: str | None, keep: int = 8) -> str:
    if not secret:
        return "(없음)"
    return f"{secret[:keep]}...({len(secret)}자)"