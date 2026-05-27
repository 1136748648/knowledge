import hashlib
import hmac
import os
import time
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import get_settings
from app.models.schemas import UserContext

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
    return f"{salt}${key}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, key = password_hash.split("$", 1)
        new_key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
        return hmac.compare_digest(key, new_key)
    except Exception:
        return False


def create_local_token(user_id: str, username: str, roles: list[str], dept_id: str | None = None) -> dict:
    settings = get_settings()
    jwt_secret = settings.ENCRYPTION_KEY or "knowledge-platform-local-secret-key-change-in-production"
    jwt_algorithm = "HS256"
    
    expires_in = 86400
    expire = int(time.time()) + expires_in
    payload = {
        "sub": user_id,
        "preferred_username": username,
        "roles": roles,
        "dept_id": dept_id,
        "exp": expire,
        "iat": int(time.time()),
        "iss": "knowledge-platform-local",
    }
    token = jwt.encode(payload, jwt_secret, algorithm=jwt_algorithm)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


class KeycloakPublicKey(BaseModel):
    kid: str
    kty: str
    alg: str
    use: str
    n: str
    e: str


@lru_cache(maxsize=1)
def _fetch_keycloak_realm_public_keys() -> dict:
    import httpx
    settings = get_settings()
    url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"
    try:
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        keys = resp.json().get("keys", [])
        return {k["kid"]: k for k in keys}
    except Exception:
        return {}


def _verify_local_token(token: str) -> UserContext | None:
    try:
        settings = get_settings()
        jwt_secret = settings.ENCRYPTION_KEY or "knowledge-platform-local-secret-key-change-in-production"
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        return UserContext(
            user_id=payload.get("sub", ""),
            username=payload.get("preferred_username", ""),
            email="",
            roles=payload.get("roles", []),
            dept_id=payload.get("dept_id"),
            clearance_level=1,
        )
    except JWTError:
        return None


def _verify_keycloak_token(token: str) -> UserContext | None:
    try:
        settings = get_settings()
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            return None

        keys = _fetch_keycloak_realm_public_keys()
        if kid not in keys:
            _fetch_keycloak_realm_public_keys.cache_clear()
            keys = _fetch_keycloak_realm_public_keys()
            if kid not in keys:
                return None

        key_data = keys[kid]
        import base64
        from jose.utils import long_to_base64
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization

        def base64_to_long(value):
            padding = 4 - len(value) % 4
            if padding != 4:
                value += "=" * padding
            return int.from_bytes(base64.urlsafe_b64decode(value), "big")

        n = base64_to_long(key_data["n"])
        e = base64_to_long(key_data["e"])
        public_numbers = RSAPublicNumbers(e, n)
        public_key = public_numbers.public_key(default_backend())
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        payload = jwt.decode(
            token,
            pem,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.KEYCLOAK_CLIENT_ID,
            options={"verify_exp": True},
        )

        return UserContext(
            user_id=payload.get("sub", ""),
            username=payload.get("preferred_username", ""),
            email=payload.get("email", ""),
            roles=payload.get("realm_access", {}).get("roles", []),
            dept_id=payload.get("dept_id"),
            clearance_level=payload.get("clearance_level", 1),
        )
    except Exception:
        return None


def verify_keycloak_token(token: str) -> UserContext | None:
    return _verify_keycloak_token(token)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserContext:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = _verify_local_token(token)
    if user:
        return user

    user = _verify_keycloak_token(token)
    if user:
        return user

    raise credentials_exception


async def get_current_active_user(current_user: UserContext = Depends(get_current_user)) -> UserContext:
    return current_user


def require_roles(*required_roles: str):
    async def role_checker(current_user: UserContext = Depends(get_current_active_user)):
        if not any(role in current_user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(required_roles)}",
            )
        return current_user
    return role_checker
