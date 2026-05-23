from app.dal import EmployeeRepository, get_adapter
from app.models.schemas import UserContext
from app.core.casbin_policy import check_permission


class DBService:
    def __init__(self, user: UserContext):
        adapter = get_adapter()
        self.employee_repo = EmployeeRepository(adapter)
        self.user = user

    async def get_employee_by_id(self, employee_id: str):
        if not await check_permission(self.user.roles, "employee", "read"):
            return None

        employee = await self.employee_repo.get_by_id(employee_id)
        if employee and not await self._can_access_employee(employee):
            return None
        return employee

    async def get_employee_by_name(self, name: str):
        if not await check_permission(self.user.roles, "employee", "read"):
            return None

        employee = await self.employee_repo.get_by_name(name)
        if employee and not await self._can_access_employee(employee):
            return None
        return employee

    async def get_employees_by_department(
        self, department: str, page: int = 1, page_size: int = 20
    ):
        if not await check_permission(self.user.roles, "employee", "read"):
            return []

        employees = await self.employee_repo.list_by_department(department, page, page_size)
        return [e for e in employees if await self._can_access_employee(e)]

    async def count_employees_by_department(self, department: str) -> int:
        if not await check_permission(self.user.roles, "employee", "read"):
            return 0

        return await self.employee_repo.count_by_department(department)

    async def get_manager(self, employee_id: str):
        if not await check_permission(self.user.roles, "employee", "read"):
            return None

        employee = await self.get_employee_by_id(employee_id)
        if not employee or not employee.manager_id:
            return None
        return await self.get_employee_by_id(employee.manager_id)

    async def _can_access_employee(self, employee) -> bool:
        if await check_permission(self.user.roles, "employee", "read"):
            if "admin" in self.user.roles:
                return True
            if employee.employee_id == self.user.user_id:
                return True
            if "hr" in self.user.roles:
                return True
            if "manager" in self.user.roles and employee.dept_id == self.user.dept_id:
                return True
        return False
