from __future__ import annotations

from sqlalchemy import ForeignKey, Row, String, desc, or_, select
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, Session, joinedload, mapped_column, relationship,
)


# ── 모델은 이미 있다. 아래 세 함수만 채우면 된다 ──
class Base(DeclarativeBase):
    pass


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    documents: Mapped[list["Document"]] = relationship(back_populates="dept")


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    dept_id: Mapped[str] = mapped_column(ForeignKey("departments.id"))
    security_level: Mapped[str] = mapped_column(String(10))
    dept: Mapped["Department"] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]] = relationship(back_populates="document")


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    doc_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    version: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(10))
    document: Mapped["Document"] = relationship(back_populates="versions")


# ══════ 여기부터 직접 채운다 ══════

# def list_documents(session: Session, *, dept_id=None, security_level=None,
#                    status=None, q=None, limit: int = 50) -> list[Row]: ...
# def get_document(session: Session, doc_id: str) -> Document | None: ...
# def add_version(session: Session, doc: Document, **fields) -> DocumentVersion: ...
