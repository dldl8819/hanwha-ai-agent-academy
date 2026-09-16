# test_copy.py 의 중복을 fixture 로 정리한 버전
import pytest

# 준비 데이터를 한 곳에만 적어둔다
@pytest.fixture
def travel_doc():
    return {"doc_id": "DOC-HR-014", "title": "국내출장 여비 규정", "security_level": "일반"}


# 함수 인자 이름을 fixture 이름과 맞추면 pytest 가 알아서 넣어준다
# - 직접 호출하지 않는다
def test_제목이_있다(travel_doc):
    assert travel_doc["title"]


def test_보안등급이_세_값_중_하나다(travel_doc):
    assert travel_doc["security_level"] in ("일반", "3급", "대외비")


# fixture 는 테스트마다 다시 실행되므로, 앞 테스트에서 값을 고쳐도 여기는 깨끗한 값을 받는다
def test_문서번호_형식이_맞다(travel_doc):
    assert travel_doc["doc_id"].startswith("DOC-")
