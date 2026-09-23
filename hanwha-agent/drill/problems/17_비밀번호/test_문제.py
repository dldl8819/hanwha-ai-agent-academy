# 채점기 — 고치지 말 것
import 시작

RAW = "sample-pw-1234"


def test_해시는_평문과_다르다():
    h = 시작.hash_password(RAW)
    assert isinstance(h, str)
    assert h != RAW
    assert RAW not in h


def test_같은_평문이라도_해시는_매번_다르다():
    # 소금이 섞이지 않으면 같은 값이 나온다
    assert 시작.hash_password(RAW) != 시작.hash_password(RAW)


def test_맞으면_True_틀리면_False():
    h = 시작.hash_password(RAW)
    assert 시작.verify_password(RAW, h) is True
    assert 시작.verify_password("틀린비번", h) is False
    assert 시작.verify_password("", h) is False


def test_깨진_해시를_줘도_예외가_나가지_않는다():
    # 문자열이되 bcrypt 해시가 아닌 값들 — DB 값이 잘렸거나 옛 형식일 때
    for 나쁜 in ["", "not-a-hash", "$2b$12$짧음", "plain-text-password"]:
        assert 시작.verify_password(RAW, 나쁜) is False


def test_한글과_이모지도_된다():
    for pw in ["비밀번호1234", "pass워드🙂"]:
        h = 시작.hash_password(pw)
        assert 시작.verify_password(pw, h) is True
        assert 시작.verify_password(pw + "x", h) is False
