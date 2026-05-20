import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import UserContext
from app.services.db_service import DBService

logger = logging.getLogger(__name__)


class DBAgent:
    def __init__(self, db: AsyncSession, user: UserContext):
        self.db = db
        self.user = user
        self.db_service = DBService(db, user)

    async def query_employee(self, name: str = None, employee_id: str = None) -> dict | None:
        """查询员工信息"""
        if employee_id:
            employee = await self.db_service.get_employee_by_id(employee_id)
        elif name:
            employee = await self.db_service.get_employee_by_name(name)
        else:
            return None

        if not employee:
            return None

        return {
            "employee_id": employee.employee_id,
            "name": employee.name,
            "department": employee.department,
            "level": employee.level,
            "hire_date": str(employee.hire_date) if employee.hire_date else None,
            "manager_id": employee.manager_id,
            "status": employee.status,
        }

    async def count_department(self, department: str) -> int:
        """统计部门人数"""
        return await self.db_service.count_employees_by_department(department)

    async def get_manager(self, employee_id: str) -> dict | None:
        """获取上级信息"""
        manager = await self.db_service.get_manager(employee_id)
        if not manager:
            return None
        return {
            "employee_id": manager.employee_id,
            "name": manager.name,
            "department": manager.department,
            "level": manager.level,
        }
