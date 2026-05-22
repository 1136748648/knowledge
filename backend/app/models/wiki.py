import uuid
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class WikiPage(Base):
    __tablename__ = "wiki_pages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wiki_pages.id"))
    acl: Mapped[dict] = mapped_column(JSONB, default=dict)
    sensitivity: Mapped[str] = mapped_column(String(20), default="public")
    dept_id: Mapped[str | None] = mapped_column(String(50))
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    parent: Mapped["WikiPage | None"] = relationship("WikiPage", remote_side="WikiPage.id")
    versions: Mapped[list["WikiPageVersion"]] = relationship("WikiPageVersion", back_populates="page", cascade="all, delete-orphan")


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
