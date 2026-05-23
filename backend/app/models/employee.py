import uuid
from datetime import datetime, date

from sqlalchemy import String, Date, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dal import Base


class Employee(Base):
    __tablename__ = "employees"

    employee_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100))
    level: Mapped[str | None] = mapped_column(String(20))
    hire_date: Mapped[date | None] = mapped_column(Date)
    manager_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("employees.employee_id"))
    email: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="active")
    clearance_level: Mapped[int] = mapped_column(default=1)
    dept_id: Mapped[str | None] = mapped_column(String(50))
    salary: Mapped[float | None] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    manager: Mapped["Employee | None"] = relationship("Employee", remote_side="Employee.employee_id")
