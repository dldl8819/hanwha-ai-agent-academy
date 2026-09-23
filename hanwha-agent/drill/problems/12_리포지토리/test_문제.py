# 채점기 — 고치지 말 것
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

import 시작


def 새세션() -> Session:
    engine = create_engine("sqlite://")          # 메모리 DB
    시작.Base.metadata.create_all(engine)
    s = Session(engine)
    s.add_all([
        시작.Department(id="HR", name="인사팀"),
        시작.Department(id="PU", name="구매팀"),
    ])
    s.add_all([
        시작.Document(id="DOC-HR-014", title="국내출장 여비 규정", dept_id="HR", security_level="일반"),
        시작.Document(id="DOC-HR-099", title="출장 안내문", dept_id="HR", security_level="일반"),
        시작.Document(id="DOC-PU-007", title="구매 절차", dept_id="PU", security_level="대외비"),
    ])
    s.add_all([
        시작.DocumentVersion(doc_id="DOC-HR-014", version="v1.0", status="폐기"),
        시작.DocumentVersion(doc_id="DOC-HR-014", version="v2.0", status="현행"),
        시작.DocumentVersion(doc_id="DOC-HR-099", version="v1.0", status="현행"),
        시작.DocumentVersion(doc_id="DOC-PU-007", version="v1.2", status="현행"),
    ])
    s.commit()
    return s


@pytest.fixture
def session():
    s = 새세션()
    yield s
    s.close()


def test_조건을_안_주면_전부_나온다(session):
    assert len(시작.list_documents(session)) == 4


def test_조건은_준_것만_걸린다(session):
    assert len(시작.list_documents(session, dept_id="HR")) == 3
    assert len(시작.list_documents(session, security_level="대외비")) == 1
    assert len(시작.list_documents(session, status="현행")) == 3
    # 두 개를 같이 주면 둘 다 만족하는 것만
    assert len(시작.list_documents(session, dept_id="HR", status="현행")) == 2


def test_q_는_제목과_문서번호_양쪽에_걸린다(session):
    # 한 행 = 버전 한 건이다. DOC-HR-014 는 버전이 둘이라 두 행으로 나온다
    assert len(시작.list_documents(session, q="여비")) == 2          # 제목 (문서 1건 × 버전 2건)
    assert len(시작.list_documents(session, q="DOC-PU")) == 1        # 문서번호
    assert len(시작.list_documents(session, q="출장")) == 3          # 제목 2건 (2 + 1 버전)
    # 대소문자를 가리지 않는다
    assert len(시작.list_documents(session, q="doc-pu")) == 1


def test_정렬은_문서번호_오름차순_버전_내림차순(session):
    rows = 시작.list_documents(session)
    문서 = [r[1].id for r in rows]
    assert 문서 == sorted(문서)
    hr = [r[0].version for r in rows if r[1].id == "DOC-HR-014"]
    assert hr == ["v2.0", "v1.0"]


def test_limit_이_먹는다(session):
    assert len(시작.list_documents(session, limit=2)) == 2


def test_세션을_닫은_뒤에도_부서를_읽을_수_있다(session):
    rows = 시작.list_documents(session)
    session.close()                               # 화면이 그리는 시점
    # 미리 같이 읽어두지 않았으면 여기서 DetachedInstanceError 가 난다
    assert rows[0][1].dept.name in {"인사팀", "구매팀"}


def test_session_외에는_키워드_전용이다(session):
    with pytest.raises(TypeError):
        시작.list_documents(session, "HR")


def test_get_document(session):
    assert 시작.get_document(session, "DOC-HR-014").title == "국내출장 여비 규정"
    # 없으면 예외가 아니라 None
    assert 시작.get_document(session, "DOC-NO-000") is None


def test_add_version_은_번호를_매기되_커밋하지_않는다(session):
    doc = 시작.get_document(session, "DOC-PU-007")
    v = 시작.add_version(session, doc, version="v2.0", status="현행")

    assert v.id is not None                       # flush 가 없으면 None 이다
    assert v.doc_id == "DOC-PU-007"

    # 아직 커밋 전이어야 한다 — 되돌리면 사라진다
    session.rollback()
    남은 = session.scalar(
        select(func.count()).select_from(시작.DocumentVersion)
        .where(시작.DocumentVersion.doc_id == "DOC-PU-007")
    )
    assert 남은 == 1
