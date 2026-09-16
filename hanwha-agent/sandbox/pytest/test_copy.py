# fixture 를 쓰기 전 모습 (비교용으로 남겨둔 파일)
# - 같은 준비 데이터를 테스트마다 복사해서 쓰고 있다
# - 값 하나만 바뀌어도 세 군데를 전부 고쳐야 한다 -> test_fixture.py 가 이걸 정리한 버전
def test_제목이_있다():
    문서 = {"doc_id": "DOC-HR-014", "title": "국내출장 여비 규정", "security_level": "일반"}
    assert 문서["title"]


def test_보안등급이_세_값_중_하나다():
    문서 = {"doc_id": "DOC-HR-014", "title": "국내출장 여비 규정", "security_level": "일반"}
    assert 문서["security_level"] in ("일반", "3급", "대외비")


def test_문서번호_형식이_맞다():
    문서 = {"doc_id": "DOC-HR-014", "title": "국내출장 여비 규정", "security_level": "일반"}
    assert 문서["doc_id"].startswith("DOC-")
