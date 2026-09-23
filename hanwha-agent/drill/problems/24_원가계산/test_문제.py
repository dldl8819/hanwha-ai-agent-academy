# 채점기 — 고치지 말 것
import 시작

백만 = 1_000_000


def test_단가표와_환율이_이름으로_있다():
    assert 시작.PRICING["input"] == 1.0
    assert 시작.PRICING["output"] == 5.0
    assert 시작.PRICING["cache_write"] == 1.25
    assert 시작.PRICING["cache_read"] == 0.1
    assert 시작.USD_KRW == 1400.0


def test_토큰이_없으면_0원():
    assert 시작.estimate_cost_krw(0, 0) == 0.0


def test_백만_토큰_기준():
    assert 시작.estimate_cost_krw(백만, 0) == 1400.0
    assert 시작.estimate_cost_krw(0, 백만) == 7000.0


def test_출력이_입력의_다섯_배():
    assert 시작.estimate_cost_krw(0, 백만) == 5 * 시작.estimate_cost_krw(백만, 0)


def test_소수_첫째_자리까지_반올림():
    # (1200/1e6 * 1.0 + 300/1e6 * 5.0) * 1400 = 3.78 -> 3.8
    assert 시작.estimate_cost_krw(1200, 300) == 3.8
    # 실제 호출 한 건 규모
    assert 시작.estimate_cost_krw(1200, 300) == round(
        (1200 / 백만 * 1.0 + 300 / 백만 * 5.0) * 1400.0, 1
    )


def test_결과는_실수다():
    assert isinstance(시작.estimate_cost_krw(1200, 300), float)
