from __future__ import annotations


# ── 예외와 설정은 이미 있다 ──
class AgentError(Exception):
    status_code = 400
    code = "agent_error"

    def __init__(self, message: str, *, detail: str | None = None):
        super().__init__(message)
        self.message = message
        self.detail = detail


class GuardTripped(AgentError):
    status_code = 400
    code = "guard_tripped"


class RateLimited(AgentError):
    status_code = 429
    code = "rate_limited"


class _설정:
    max_input_chars = 200
    daily_call_limit = 200


def get_settings() -> _설정:
    return _설정()


# ══════ 여기부터 직접 채운다 ══════

# MIN_QUESTION_LEN = ...
# ALLOWED_MODELS = ...
# def check_question(text: str) -> str: ...
# def check_model(model: str) -> str: ...
# def check_daily_limit(used_today: int) -> None: ...
