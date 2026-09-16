def clean_title(raw):
    return raw.strip()

def test_앞뒤_공백을_지운다():
    assert clean_title("     앞뒤 공백이 있는 문자열    ") == "앞뒤 공백이 있는 문자열"

def test_공백이_없으면_그대로다():
    assert clean_title("안녕 테스트야") == "안녕 테스트야"

# test_ 앞에 안붙어 있어서 실행되지 않는다.
def 빈_제목이면_빈_문자열():
    assert clean_title("   ") == ""

