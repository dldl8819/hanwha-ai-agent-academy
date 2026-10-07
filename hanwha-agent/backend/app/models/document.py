from __future__ import annotations

from datetime import date
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, EMBED_DIM
from pgvector.sqlalchemy import Vector

# 문서 모델
class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    # 자연키
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    dept_id: Mapped[str] = mapped_column(ForeignKey("departments.id"), index=True)
    
    security_level: Mapped[str] = mapped_column(String(10), index=True)  
    
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    dept: Mapped["Department"] = relationship(back_populates="documents")
    owner: Mapped["User | None"] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document",
        order_by="DocumentVersion.version",
    )

    # 현행(시행 중) 버전 리턴
    # - 현행이 아니면 None으로 리턴
    @property
    def current(self) -> "DocumentVersion | None":
        for v in self.versions:
            if v.status == "현행":
                return v
        return None

# 문서 버전별 저장 모델
class DocumentVersion(Base, TimestampMixin):
    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    doc_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    version: Mapped[str] = mapped_column(String(10))    
    status: Mapped[str] = mapped_column(String(10))     

    effective_from: Mapped[date]
    expires_at: Mapped[date | None]

    # 파일 자체는 디스크에 두고 DB에는 경로만 저장
    file_path: Mapped[str | None] = mapped_column(String(300))
    file_format: Mapped[str] = mapped_column(String(10))  

    # 색인(index) 관련
    # - 추후 파싱/임베딩에 사용될 필드
    chunk_count: Mapped[int] = mapped_column(default=0)
    embed_model: Mapped[str | None] = mapped_column(String(50))
    index_status: Mapped[str] = mapped_column(String(10), default="대기")  
    index_progress: Mapped[int] = mapped_column(default=0)                
    indexed_at: Mapped[date | None]

    document: Mapped["Document"] = relationship(back_populates="versions")
    # 청크는 버전에 딸린다. 문서가 아니라 버전이다.
    # - v1.4 와 v2.0 은 같은 문서여도 본문이 달라 청크를 공유할 수 없다.
    # - cascade 로 delete-orphan 을 건 이유: 버전을 지우면 청크도 같이 지워져야 한다.
    #   안 걸면 version_id 가 가리킬 데가 없는 청크가 남아 외래키 제약에서 터진다.
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )


    __table_args__ = (UniqueConstraint("doc_id", "version", name="uq_doc_version"),)

    # 화면에 '시행~만료' 칸에 그대로 들어갈 문자열 리턴
    @property
    def period(self) -> str:
        if self.expires_at is None:
            return f"{self.effective_from} ~"
        return f"{self.effective_from} ~ {self.expires_at}"

    # 검색 결과에 내보내도 되는지 판단하는 기능
    # - 현행이며 색인이 완료된 경우에만 True
    @property
    def is_searchable(self) -> bool:
        return self.status == "현행" and self.index_status == "완료"

# 청크 한 조각을 저장하는 모델
# - chunker.ChunkDraft 를 그대로 받아 적는 자리다. 필드 이름도 맞춰 뒀다.
# - 아직 임베딩 벡터 칼럼이 없다. 지금은 "조각난 본문과 그 출처"까지만 남긴다.
class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 어느 문서의 어느 판에서 나온 조각인지
    # - index=True : 청크는 늘 "이 버전의 청크 전부" 형태로 조회된다.
    #   색인이 없으면 버전 하나 읽을 때마다 chunks 전체를 훑는다.
    version_id: Mapped[int] = mapped_column(ForeignKey("document_versions.id"), index=True)
    # 문서 안에서의 순서
    # - 검색 결과를 원문 순서로 되돌리거나 앞뒤 조각을 붙여 볼 때 쓴다.
    ord: Mapped[int] = mapped_column(default=0)
    kind: Mapped[str] = mapped_column(String(16))      # "조항" | "표"
    locator: Mapped[str] = mapped_column(String(200))  # "제3장 제2절 제14조(숙박비)", "표2"
    # 본문
    # - String 이 아니라 Text 다. String(n) 은 길이 상한이 있어 조항 하나가 잘린다.
    #   표는 마크다운으로 변환해 넣으므로 더 길어진다.
    text: Mapped[str] = mapped_column(Text)

    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBED_DIM), nullable=True)

    version: Mapped["DocumentVersion"] = relationship(back_populates="chunks")
