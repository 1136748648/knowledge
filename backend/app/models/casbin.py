from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CasbinRule(Base):
    __tablename__ = "casbin_rule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ptype: Mapped[str] = mapped_column(String(100), nullable=False)
    v0: Mapped[str | None] = mapped_column(String(100))
    v1: Mapped[str | None] = mapped_column(String(100))
    v2: Mapped[str | None] = mapped_column(String(100))
    v3: Mapped[str | None] = mapped_column(String(100))
    v4: Mapped[str | None] = mapped_column(String(100))
    v5: Mapped[str | None] = mapped_column(String(100))
