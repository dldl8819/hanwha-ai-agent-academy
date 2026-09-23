# 채점기 — 고치지 말 것
import pytest

import 시작


def test_통과하면_공백이_걷어진_질문이_돌아온다():
    assert 시작.check_question("  부산 출장 숙박비?  ") == "부산 출장 숙박비?"


def test_짧으면_막힌다():
    assert 시작.MIN_QUESTION_LEN == 2
    for 나쁜 in ["", "   ", "가", " 가 "]:
        with pytest.raises(시작.GuardTripped):
            시작.check_question(나쁜)


def test_None_이_와도_터지지_않고_GuardTripped():
    with pytest.raises(시작.GuardTripped):
        시작.check_question(None)


def test_길면_막히고_메시지에_숫자가_들어간다():
    상한 = 시작.get_settings().max_input_chars
    assert 시작.check_question("가" * 상한)                    # 경계는 통과
    with pytest.raises(시작.GuardTripped) as e:
        시작.check_question("가" * (상한 + 1))
    assert str(상한) in str(e.value)
    assert str(상한 + 1) in str(e.value)


def test_모델은_허용_목록_방식이다():
    assert "claude-haiku-4-5" in 시작.ALLOWED_MODELS
    assert 시작.check_model("claude-haiku-4-5") == "claude-haiku-4-5"

    for 나쁜 in ["gpt-4", "claude-opus-5", "", "CLAUDE-HAIKU-4-5"]:
        with pytest.raises(시작.GuardTripped):
            시작.check_model(나쁜)


def test_막힌_모델_이름이_메시지에_보인다():
    with pytest.raises(시작.GuardTripped) as e:
        시작.check_model("gpt-4")
    assert "gpt-4" in str(e.value)


def test_한도는_도달에서_막힌다():
    한도 = 시작.get_settings().daily_call_limit
    assert 시작.check_daily_limit(한도 - 1) is None          # 통과하면 아무것도 안 돌려준다
    for 넘김 in [한도, 한도 + 1]:
        with pytest.raises(시작.RateLimited):
            시작.check_daily_limit(넘김)
