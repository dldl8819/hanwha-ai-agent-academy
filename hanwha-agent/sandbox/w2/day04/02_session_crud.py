from demo_models import Department, Document, SessionLocal, reset_db

def main() -> None:
    # 원활한 테스트를 위한 DB 초기화 기능
    reset_db()

    # 세션 공장에서 session 하나 생성해 받기 
    with SessionLocal() as session:
        # 추가 add()
        # - 객체를 저장 대상으로 등록
        # - 아직 DB에 가지는 않음
        hr = Department(id="HR", name="인사")
        session.add(hr)
        print(f"add 후 new : {session.new}")

        # flush 
        # - 등록해둔 것을 SQL로 내보낸다.
        # 아직 commit 전
        session.flush()
        print(f"flush 후 new : {session.new}")
        print(f"DB에서 조회는 가능 : {session.get(Department, "HR")}")

        # add_all 
        # 여러 건을 한 번에 등록
        session.add_all([
            Document(id="DOC-HR-012", title="출장 여비 규정", dept_id="HR", page_count=18),
            Document(id="DOC-HR-013", title="재택근무 운영 지침", dept_id="HR", page_count=9)
        ])

        # commit 
        # - 데이터 확정
        # - 커밋을 안하면 데이터베이스에 남지 않는다.
        session.commit()
        print("commit 완료")

    with SessionLocal() as session:
        # get
        # - 기본키로 한 건 조회
        document = session.get(Document, "DOC-HR-012")
        print(f"get : {document} / 없는 id : {session.get(Document, "DOC-HR-999")}")

        # update 없음
        # - 객체의 속성만 변경
        document.page_count = 20
        print(f"update - dirty : {session.dirty}")
        session.commit()
        print(f"commit 후 page_count : {document.page_count}")

    with SessionLocal() as session:
        # rollback
        # - 확정 전에 되돌리면 아무 일도 없던 것처럼 되돌아감
        session.add(Document(id="DOC-TMP-001", title="실수", dept_id="HR"))
        # 쿼리문 나가고 조회하면 조회되나 commit을 하지 않아 영구 반영은 아니다.
        session.flush()
        print("rollback 전 : ", session.get(Document, "DOC-TMP-001"))
        # 되돌리기 rollback()
        session.rollback()
        print("rollback 후 : ", session.get(Document, "DOC-TMP-001"))

        # delete 
        # - 객체 단위로 삭제된다.
        doc = session.get(Document, "DOC-HR-013") 
        print(f"삭제 전 조회 : {doc}")
        session.delete(doc)
        session.commit()
        print(f"삭제 후 조회 : {doc}")


if __name__ == "__main__":
    main()

'''
hanwha-agent\sandbox\w2\day04 에서 실행
python -m 02_session_crud
'''