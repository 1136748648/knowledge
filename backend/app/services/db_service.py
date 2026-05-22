from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.schemas import UserContext


class DBService:
    def __init__(self, db: AsyncSession, user: UserContext):
        self.db = db
        self.user = user

    async def get_employee_by_id(self, employee_id: str) -> Employee | None:
        """根据工号查询员工"""
        result = await self.db.execute(
            select(Employee).where(Employee.employee_id == employee_id)
        )
        employee = result.scalar_one_or_none()
        if employee and not await self._can_access_employee(employee):
            return None
        return employee

    async def get_employee_by_name(self, name: str) -> Employee | None:
        """根据姓名查询员工"""
        result = await self.db.execute(
            select(Employee).where(Employee.name == name)
        )
        employee = result.scalar_one_or_none()
        if employee and not await self._can_access_employee(employee):
            return None
        return employee

    async def get_employees_by_department(
        self, department: str, page: int = 1, page_size: int = 20
    ) -> list[Employee]:
        """查询部门员工"""
        query = select(Employee).where(Employee.department == department)
        query = self._apply_access_filter(query)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_employees_by_department(self, department: str) -> int:
        """统计部门人数"""
        query = select(func.count()).select_from(Employee).where(Employee.department == department)
        query = self._apply_access_filter(query)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_manager(self, employee_id: str) -> Employee | None:
        """获取员工上级"""
        employee = await self.get_employee_by_id(employee_id)
        if not employee or not employee.manager_id:
            return None
        return await self.get_employee_by_id(employee.manager_id)

    async def _can_access_employee(self, employee: Employee) -> bool:
        """检查是否可以访问该员工信息"""
        if "admin" in self.user.roles:
            return True
        if employee.employee_id == self.user.user_id:
            return True
        if "hr" in self.user.roles:
            return True
        if "manager" in self.user.roles and employee.dept_id == self.user.dept_id:
            return True
        return False

    def _apply_access_filter(self, query):
        """应用数据访问范围过滤"""
        if "admin" in self.user.roles:
            return query
        if "hr" in self.user.roles:
            return query
        if "manager" in self.user.roles:
            return query.where(Employee.dept_id == self.user.dept_id)
        # 普通员工只能看自己
        return query.where(Employee.employee_id == self.user.user_id)
