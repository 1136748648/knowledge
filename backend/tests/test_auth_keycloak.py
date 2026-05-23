import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport


class TestKeycloakOAuth2:
    """FR-AUTH-004: Keycloak OAuth2集成单元测试"""

    @pytest.fixture
    async def client_with_mock_db(self):
        """创建带有mock数据库的测试客户端"""
        from app.main import app
        from app.db.session import get_db
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        def override_get_db():
            return mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_keycloak_login_success(self, client):
        """测试Keycloak登录接口 - 返回授权URL"""
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                KEYCLOAK_SERVER_URL="https://keycloak.example.com",
                KEYCLOAK_REALM="knowledge-realm",
                KEYCLOAK_CLIENT_ID="knowledge-client",
            )

            response = await client.get("/api/auth/keycloak/login")

            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data
            assert "keycloak.example.com" in data["authorization_url"]
            assert "knowledge-realm" in data["authorization_url"]
            assert "knowledge-client" in data["authorization_url"]
            assert "response_type=code" in data["authorization_url"]

    @pytest.mark.asyncio
    async def test_keycloak_login_not_configured(self, client):
        """测试Keycloak登录接口 - Keycloak未配置时返回503"""
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(KEYCLOAK_SERVER_URL=None)

            response = await client.get("/api/auth/keycloak/login")

            assert response.status_code == 503
            assert "Keycloak 未配置" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_keycloak_callback_success(self, client):
        """测试Keycloak回调接口 - 成功获取token"""
        mock_token_response = {
            "access_token": "valid-keycloak-token",
            "token_type": "bearer",
            "expires_in": 3600,
        }

        mock_user_context = MagicMock(
            user_id="keycloak-user-123",
            username="testuser",
            email="test@example.com",
            roles=["employee"],
            dept_id="dept-001",
        )

        from app.main import app
        from app.db.session import get_db
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("app.config.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(
                    KEYCLOAK_SERVER_URL="https://keycloak.example.com",
                    KEYCLOAK_REALM="knowledge-realm",
                    KEYCLOAK_CLIENT_ID="knowledge-client",
                    KEYCLOAK_CLIENT_SECRET="test-secret",
                )

                with patch("httpx.AsyncClient") as mock_http_client:
                    mock_post = MagicMock()
                    mock_post.status_code = 200
                    mock_post.json.return_value = mock_token_response
                    mock_http_client.return_value.__aenter__.return_value.post.return_value = mock_post

                    with patch("app.api.auth.verify_keycloak_token") as mock_verify:
                        mock_verify.return_value = mock_user_context

                        response = await client.post(
                            "/api/auth/keycloak/callback",
                            json={"code": "valid-authorization-code", "state": "random-state"},
                        )

                        assert response.status_code == 200
                        data = response.json()
                        assert "access_token" in data
                        assert data["token_type"] == "bearer"
                        assert "expires_in" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_keycloak_callback_token_exchange_failed(self, client):
        """测试Keycloak回调接口 - token交换失败"""
        from app.main import app
        from app.db.session import get_db
        
        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("app.config.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(
                    KEYCLOAK_SERVER_URL="https://keycloak.example.com",
                    KEYCLOAK_REALM="knowledge-realm",
                    KEYCLOAK_CLIENT_ID="knowledge-client",
                    KEYCLOAK_CLIENT_SECRET="test-secret",
                )

                with patch("httpx.AsyncClient") as mock_http_client:
                    mock_post = MagicMock()
                    mock_post.status_code = 401
                    mock_post.text = "Invalid grant"
                    mock_http_client.return_value.__aenter__.return_value.post.return_value = mock_post

                    response = await client.post(
                        "/api/auth/keycloak/callback",
                        json={"code": "invalid-code", "state": "random-state"},
                    )

                    assert response.status_code == 401
                    assert "Keycloak 认证失败" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_keycloak_callback_no_access_token(self, client):
        """测试Keycloak回调接口 - 未返回access_token"""
        mock_token_response = {"token_type": "bearer", "expires_in": 3600}

        from app.main import app
        from app.db.session import get_db
        
        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("app.config.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(
                    KEYCLOAK_SERVER_URL="https://keycloak.example.com",
                    KEYCLOAK_REALM="knowledge-realm",
                    KEYCLOAK_CLIENT_ID="knowledge-client",
                    KEYCLOAK_CLIENT_SECRET="test-secret",
                )

                with patch("httpx.AsyncClient") as mock_http_client:
                    mock_post = MagicMock()
                    mock_post.status_code = 200
                    mock_post.json.return_value = mock_token_response
                    mock_http_client.return_value.__aenter__.return_value.post.return_value = mock_post

                    response = await client.post(
                        "/api/auth/keycloak/callback",
                        json={"code": "valid-code", "state": "random-state"},
                    )

                    assert response.status_code == 401
                    assert "Keycloak 未返回 access_token" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_keycloak_callback_token_verification_failed(self, client):
        """测试Keycloak回调接口 - token验证失败"""
        mock_token_response = {"access_token": "invalid-token", "token_type": "bearer"}

        from app.main import app
        from app.db.session import get_db
        
        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("app.config.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(
                    KEYCLOAK_SERVER_URL="https://keycloak.example.com",
                    KEYCLOAK_REALM="knowledge-realm",
                    KEYCLOAK_CLIENT_ID="knowledge-client",
                    KEYCLOAK_CLIENT_SECRET="test-secret",
                )

                with patch("httpx.AsyncClient") as mock_http_client:
                    mock_post = MagicMock()
                    mock_post.status_code = 200
                    mock_post.json.return_value = mock_token_response
                    mock_http_client.return_value.__aenter__.return_value.post.return_value = mock_post

                    with patch("app.api.auth.verify_keycloak_token") as mock_verify:
                        mock_verify.return_value = None

                        response = await client.post(
                            "/api/auth/keycloak/callback",
                            json={"code": "valid-code", "state": "random-state"},
                        )

                        assert response.status_code == 401
                        assert "Keycloak token 验证失败" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_keycloak_callback_http_error(self, client):
        """测试Keycloak回调接口 - HTTP请求失败"""
        from app.main import app
        from app.db.session import get_db
        
        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("app.config.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(
                    KEYCLOAK_SERVER_URL="https://keycloak.example.com",
                    KEYCLOAK_REALM="knowledge-realm",
                    KEYCLOAK_CLIENT_ID="knowledge-client",
                    KEYCLOAK_CLIENT_SECRET="test-secret",
                )

                with patch("httpx.AsyncClient") as mock_http_client:
                    import httpx
                    mock_http_client.return_value.__aenter__.return_value.post.side_effect = httpx.HTTPError(
                        "Connection refused"
                    )

                    response = await client.post(
                        "/api/auth/keycloak/callback",
                        json={"code": "valid-code", "state": "random-state"},
                    )

                    assert response.status_code == 503
                    assert "无法连接 Keycloak 服务器" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_keycloak_callback_with_existing_local_user(self, client):
        """测试Keycloak回调接口 - 本地用户已存在"""
        mock_token_response = {"access_token": "valid-token", "token_type": "bearer"}

        mock_user_context = MagicMock(
            user_id="keycloak-id",
            username="existing-user",
            email="existing@example.com",
            roles=["employee"],
            dept_id=None,
        )

        mock_local_user = MagicMock(
            id=123,
            username="existing-user",
            roles=["admin"],
            dept_id="dept-002",
        )

        from app.main import app
        from app.db.session import get_db
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_local_user
        mock_db.execute.return_value = mock_result
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("app.config.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(
                    KEYCLOAK_SERVER_URL="https://keycloak.example.com",
                    KEYCLOAK_REALM="knowledge-realm",
                    KEYCLOAK_CLIENT_ID="knowledge-client",
                    KEYCLOAK_CLIENT_SECRET="test-secret",
                )

                with patch("httpx.AsyncClient") as mock_http_client:
                    mock_post = MagicMock()
                    mock_post.status_code = 200
                    mock_post.json.return_value = mock_token_response
                    mock_http_client.return_value.__aenter__.return_value.post.return_value = mock_post

                    with patch("app.api.auth.verify_keycloak_token") as mock_verify:
                        mock_verify.return_value = mock_user_context

                        response = await client.post(
                            "/api/auth/keycloak/callback",
                            json={"code": "valid-code", "state": "random-state"},
                        )

                        assert response.status_code == 200
                        data = response.json()
                        assert "access_token" in data
                        assert data["token_type"] == "bearer"
        finally:
            app.dependency_overrides.clear()
