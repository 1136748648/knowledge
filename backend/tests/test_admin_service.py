import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.admin_service import AdminService
from app.models.schemas import UserContext


@pytest.fixture
def mock_audit_log_repo():
    return AsyncMock()


@pytest.fixture
def admin_service(mock_audit_log_repo):
    return AdminService(mock_audit_log_repo)


@pytest.fixture
def admin_user():
    return UserContext(
        user_id="admin-1",
        username="admin",
        email="admin@test.com",
        roles=["admin"],
        dept_id="dept-1",
    )


@pytest.fixture
def normal_user():
    return UserContext(
        user_id="user-1",
        username="normaluser",
        email="user@test.com",
        roles=["employee"],
        dept_id="dept-1",
    )


class TestAdminServiceCheckAdminAccess:
    @pytest.mark.asyncio
    async def test_check_admin_access_returns_true_for_admin(self, admin_service, admin_user):
        result = await admin_service.check_admin_access(admin_user)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_admin_access_returns_false_for_normal_user(self, admin_service, normal_user):
        result = await admin_service.check_admin_access(normal_user)
        assert result is False


class TestAdminServiceGetAuditLogs:
    @pytest.mark.asyncio
    async def test_get_audit_logs_raises_error_for_non_admin(self, admin_service, normal_user):
        with pytest.raises(PermissionError, match="Admin access required"):
            await admin_service.get_audit_logs(normal_user)

    @pytest.mark.asyncio
    async def test_get_audit_logs_returns_logs_for_admin(self, admin_service, admin_user):
        mock_logs = [MagicMock(), MagicMock()]
        admin_service.audit_log_repo.get_logs.return_value = mock_logs
        
        result = await admin_service.get_audit_logs(admin_user)
        
        admin_service.audit_log_repo.get_logs.assert_called_once()
        assert result == mock_logs

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_filters(self, admin_service, admin_user):
        mock_logs = [MagicMock()]
        admin_service.audit_log_repo.get_logs.return_value = mock_logs
        
        result = await admin_service.get_audit_logs(
            admin_user,
            target_user_id="user-123",
            action="login",
            page=1,
            page_size=10,
        )
        
        admin_service.audit_log_repo.get_logs.assert_called_once_with(
            "user-123", "login", 1, 10
        )
        assert result == mock_logs


class TestAdminServiceListUsers:
    @pytest.mark.asyncio
    async def test_list_users_raises_error_for_non_admin(self, admin_service, normal_user):
        with pytest.raises(PermissionError, match="Admin access required"):
            await admin_service.list_users(normal_user)

    @pytest.mark.asyncio
    async def test_list_users_returns_empty_list_for_admin(self, admin_service, admin_user):
        result = await admin_service.list_users(admin_user)
        assert result == []


class TestAdminServiceGetPermissions:
    @pytest.mark.asyncio
    async def test_get_permissions_raises_error_for_non_admin(self, admin_service, normal_user):
        with pytest.raises(PermissionError, match="Admin access required"):
            await admin_service.get_permissions(normal_user)

    @pytest.mark.asyncio
    async def test_get_permissions_raises_error_without_policy_manage(self, admin_service, admin_user):
        with patch("app.services.admin_service.check_permission", return_value=False):
            with pytest.raises(PermissionError, match="Permission denied"):
                await admin_service.get_permissions(admin_user)

    @pytest.mark.asyncio
    async def test_get_permissions_returns_permissions(self, admin_service, admin_user):
        mock_permissions = ["wiki:read", "wiki:write"]
        
        with patch("app.services.admin_service.check_permission", return_value=True):
            with patch("app.services.admin_service.get_user_permissions", return_value=mock_permissions):
                result = await admin_service.get_permissions(admin_user)
                assert result == mock_permissions


class TestAdminServicePolicyOperations:
    @pytest.mark.asyncio
    async def test_create_policy_raises_error_for_non_admin(self, admin_service, normal_user):
        with pytest.raises(PermissionError, match="Admin access required"):
            await admin_service.create_policy(normal_user, "user:1", "wiki", "read")

    @pytest.mark.asyncio
    async def test_create_policy_calls_add_policy(self, admin_service, admin_user):
        with patch("app.services.admin_service.check_permission", return_value=True):
            with patch("app.services.admin_service.add_policy", return_value=True) as mock_add:
                result = await admin_service.create_policy(admin_user, "user:1", "wiki", "read")
                mock_add.assert_called_once_with("user:1", "wiki", "read")
                assert result is True

    @pytest.mark.asyncio
    async def test_delete_policy_calls_remove_policy(self, admin_service, admin_user):
        with patch("app.services.admin_service.check_permission", return_value=True):
            with patch("app.services.admin_service.remove_policy", return_value=True) as mock_remove:
                result = await admin_service.delete_policy(admin_user, "user:1", "wiki", "read")
                mock_remove.assert_called_once_with("user:1", "wiki", "read")
                assert result is True


class TestAdminServiceRoleOperations:
    @pytest.mark.asyncio
    async def test_assign_role_raises_error_for_non_admin(self, admin_service, normal_user):
        with pytest.raises(PermissionError, match="Admin access required"):
            await admin_service.assign_role(normal_user, "user:1", "manager")

    @pytest.mark.asyncio
    async def test_assign_role_calls_add_role(self, admin_service, admin_user):
        with patch("app.services.admin_service.check_permission", return_value=True):
            with patch("app.services.admin_service.add_role_for_user", return_value=True) as mock_add:
                result = await admin_service.assign_role(admin_user, "user:1", "manager")
                mock_add.assert_called_once_with("user:1", "manager")
                assert result is True

    @pytest.mark.asyncio
    async def test_unassign_role_calls_remove_role(self, admin_service, admin_user):
        with patch("app.services.admin_service.check_permission", return_value=True):
            with patch("app.services.admin_service.remove_role_for_user", return_value=True) as mock_remove:
                result = await admin_service.unassign_role(admin_user, "user:1", "manager")
                mock_remove.assert_called_once_with("user:1", "manager")
                assert result is True

    @pytest.mark.asyncio
    async def test_get_user_roles_returns_roles(self, admin_service, admin_user):
        mock_roles = ["admin", "manager"]
        
        with patch("app.services.admin_service.get_user_roles", return_value=mock_roles):
            result = await admin_service.get_user_roles(admin_user, "user:1")
            assert result == {"user": "user:1", "roles": mock_roles}