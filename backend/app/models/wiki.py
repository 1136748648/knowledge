import uuid
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dal import Base


class WikiPage(Base):
    __tablename__ = "wiki_pages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wiki_pages.id"))
    sensitivity: Mapped[str] = mapped_column(String(20), default="public")
    dept_id: Mapped[str | None] = mapped_column(String(50))
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    processing_status: Mapped[str] = mapped_column(String(20), default="pending")
    processing_error: Mapped[str | None] = mapped_column(Text)

    parent: Mapped["WikiPage | None"] = relationship("WikiPage", remote_side=[id])
    versions: Mapped[list["WikiPageVersion"]] = relationship("WikiPageVersion", back_populates="page", cascade="all, delete-orphan")
    files: Mapped[list["WikiFile"]] = relationship("WikiFile", back_populates="page", cascade="all, delete-orphan")
    tags: Mapped[list["WikiTag"]] = relationship("WikiTag", secondary="wiki_page_tags", back_populates="pages")

    @property
    def current_file(self):
        for f in self.files:
            if f.is_current:
                return f
        return None


class WikiPageVersion(Base):
    __tablename__ = "wiki_page_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wiki_pages.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    edited_by: Mapped[str] = mapped_column(String(100), nullable=False)
    edit_summary: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    page: Mapped["WikiPage"] = relationship("WikiPage", back_populates="versions")
