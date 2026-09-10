# 필요한 클래스와 함수 가져오기
from app.models.base import Base, TimestampMixin
from app.models.documents import Department, Document, DocumentVersion

__all__ = "Base", "TimestampMixin", "Department", "Document", "DocumentVersion"