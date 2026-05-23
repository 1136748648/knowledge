import uuid
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.dal import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    dept_id: Mapped[str | None] = mapped_column(String(50))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    source_refs: Mapped[list] = mapped_column(JSONB, default=list)
    embedding_id: Mapped[str | None] = mapped_column(String(100))
    sensitivity: Mapped[str] = mapped_column(String(20), default="public")
    feedback: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
