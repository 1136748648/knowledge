import uuid
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class KnowledgeNav(Base):
    __tablename__ = "knowledge_nav"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_nav.id", ondelete="CASCADE"))
    path: Mapped[str | None] = mapped_column(String(500))  # ltree type in PostgreSQL
    icon: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    visibility_roles: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    created_by: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    parent: Mapped["KnowledgeNav | None"] = relationship("KnowledgeNav", remote_side="KnowledgeNav.id")
    children: Mapped[list["KnowledgeNav"]] = relationship("KnowledgeNav", back_populates="parent")


class NavContentLink(Base):
    __tablename__ = "nav_content_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nav_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_nav.id", ondelete="CASCADE"), nullable=False)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
