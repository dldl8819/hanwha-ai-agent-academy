from sqlalchemy import select

from demo_models import Department, Document, SessionLocal, reset_db, seed


def main() -> None:
    reset_db()
    # 샘플 데이터
    seed()

    with SessionLocal() as session:
        # join : Document -> Department로 이어지는 관계(relationship)를 그대로 넘기면
        # SQLAlchemy가 ON 조건(documents.dept_id = departments.id)을 알아서 만들어준다
        print("만들어진 SQL문")
        print(select(Document.id, Department.name).join(Document.department))

        # 문제 1 : 문서의 id와 부서명을 모두 출력
        stmt = select(Document.id, Department.name).join(Document.department)
        print("전체 문서 id + 부서명")
        for doc_id, dept_name in session.execute(stmt):
            print(f"  {doc_id} / {dept_name}")

        # 문제 2 : 보안팀의 문서 id와 부서명을 출력
        # - join 이후에도 where는 똑같이 붙일 수 있다
        stmt = (
            select(Document.id, Department.name)
            .join(Document.department)
            .where(Department.name == "보안팀")
        )
        print("보안팀 문서 id + 부서명")
        for doc_id, dept_name in session.execute(stmt):
            print(f"  {doc_id} / {dept_name}")

        # 참고 : 관계 없이 ON 조건을 직접 지정하는 방식도 가능하다
        # stmt = select(Document.id, Department.name).join(
        #     Department, Document.dept_id == Department.id
        # )


if __name__ == "__main__":
    main()
