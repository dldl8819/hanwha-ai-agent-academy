from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False # APP_MODE 든 app_mode든 같은 것으로 보게 설정 
    )
    
    # --- 실행 모드 ---
    # 기본값 mock으로 설정
    # mock이 아니면 live로 설정
    app_mode: str = Field(default="mock", pattern=r"^(mock|live)$")
    anthropic_api_key: SecretStr | None = None
    llm_model: str = "claude-haiku-4-5"
    max_tokens: int = Field(default=400, ge=1, le=8192)
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    daily_call_limit: int = Field(default=200, ge=1)
    max_input_chars: int = Field(default=200, ge=1)
    database_url: str = "sqlite:///./app.db"
    debug: bool = False
    allow_external_send: bool = False
    # 실습 - 환경변수 값 추가 top_k, upstage_api_key
    top_k: int = Field(default=3, ge=1, le=20)
    upstage_api_key: SecretStr | None = None

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