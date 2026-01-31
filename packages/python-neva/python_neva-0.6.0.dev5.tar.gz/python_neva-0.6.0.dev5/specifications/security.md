# Security Module Specification

This document outlines the security-related features we would like to add to Neva, organized in layers of increasing complexity.

## Overview

Security features are split across multiple modules and packages:

| Layer | Module/Package | Purpose | Dependencies |
|-------|----------------|---------|--------------|
| Core | `neva.security` | Primitives: hashing, encryption, token generation | `cryptography`, `pwdlib` |
| Built-in | `neva.auth` | JWT, password reset, guards | `pyjwt` |
| Extension | `?` | API tokens support | `neva` |
| Extension | `?` | Full OAuth2 implementatino | `neva`, `authlib` |

---

## Layer 1: Core Security (`neva.security`)

Foundational security primitives that most applications need. No opinions on authentication strategy.

### Directory Structure

```
neva/security/
├── __init__.py
├── hashing/
├── encryption/
├── tokens/
├── middleware/
├── facade.py                  # Hash, Crypt facades
└── provider.py                # SecurityServiceProvider (umbrella)
```

### Dependencies

- `cryptography` — encryption, HMAC signatures
- `pwdlib[argon2,bcrypt]` — password hashing

### 1.2 Encryption

#### Interface

```python
from abc import ABC, abstractmethod

class Encrypter(ABC):
    """Interface for symmetric encryption."""

    @abstractmethod
    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data."""
        ...

    @abstractmethod
    def decrypt(self, payload: bytes) -> bytes:
        """Decrypt data."""
        ...

    @abstractmethod
    def encrypt_string(self, data: str) -> str:
        """Encrypt string, return base64-encoded result."""
        ...

    @abstractmethod
    def decrypt_string(self, payload: str) -> str:
        """Decrypt base64-encoded payload to string."""
        ...
```

### 1.3 Token Generation

For generating secure random tokens (password resets, email verification, API keys).

#### Implementation

```python
import secrets
import hashlib
import hmac
import time
import base64
import json
from neva import Result, Ok, Err

class TokenGenerator:
    """Generates secure random tokens."""

    @staticmethod
    def generate(length: int = 32) -> str:
        """Generate a URL-safe random token."""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_hex(length: int = 32) -> str:
        """Generate a hex-encoded random token."""
        return secrets.token_hex(length)

    @staticmethod
    def generate_bytes(length: int = 32) -> bytes:
        """Generate random bytes."""
        return secrets.token_bytes(length)


class SignedTokenManager:
    """Creates and verifies HMAC-signed tokens with expiration."""

    def __init__(self, key: bytes) -> None:
        self._key = key

    def sign(self, data: dict, expires_in: int | None = None) -> str:
        """
        Create a signed token containing data.

        Args:
            data: Payload to include in token
            expires_in: Seconds until expiration (None = no expiry)

        Returns:
            URL-safe base64-encoded signed token
        """
        payload = {
            "data": data,
            "iat": int(time.time()),
        }
        if expires_in is not None:
            payload["exp"] = payload["iat"] + expires_in

        payload_bytes = json.dumps(payload, separators=(",", ":")).encode()
        signature = hmac.new(self._key, payload_bytes, hashlib.sha256).digest()

        token = payload_bytes + b"." + signature
        return base64.urlsafe_b64encode(token).decode("ascii")

    def verify(self, token: str) -> Result[dict, str]:
        """
        Verify a signed token and extract data.

        Returns:
            Ok(data) if valid, Err(reason) if invalid
        """
        try:
            decoded = base64.urlsafe_b64decode(token.encode("ascii"))
            payload_bytes, signature = decoded.rsplit(b".", 1)

            expected_sig = hmac.new(self._key, payload_bytes, hashlib.sha256).digest()
            if not hmac.compare_digest(signature, expected_sig):
                return Err("Invalid signature")

            payload = json.loads(payload_bytes)

            if "exp" in payload and payload["exp"] < time.time():
                return Err("Token expired")

            return Ok(payload["data"])

        except Exception as e:
            return Err(f"Invalid token: {e}")
```

#### Facade

```python
class Token(Facade):
    @classmethod
    def get_facade_accessor(cls) -> type:
        return TokenGenerator

# Usage:
# token = Token.generate()  # Random token
# token = Token.generate(48)  # Longer token
```

### 1.4 CSRF Protection

#### Middleware

```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from neva.support.facade import Config

class CsrfMiddleware(BaseHTTPMiddleware):
    """CSRF protection for state-changing requests."""

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
    TOKEN_HEADER = "X-CSRF-Token"
    TOKEN_FIELD = "_token"
    COOKIE_NAME = "csrf_token"

    def __init__(self, app, *, secret_key: bytes, exclude: list[str] | None = None):
        super().__init__(app)
        self._signer = SignedTokenManager(secret_key)
        self._exclude = exclude or []

    async def dispatch(self, request: Request, call_next):
        # Skip safe methods
        if request.method in self.SAFE_METHODS:
            return await self._add_csrf_cookie(request, call_next)

        # Skip excluded paths
        if any(request.url.path.startswith(p) for p in self._exclude):
            return await call_next(request)

        # Verify CSRF token
        token = await self._get_token(request)
        if token is None:
            return Response("CSRF token missing", status_code=403)

        result = self._signer.verify(token)
        if result.is_err:
            return Response(f"CSRF validation failed: {result.unwrap_err()}", status_code=403)

        return await call_next(request)

    async def _get_token(self, request: Request) -> str | None:
        # Check header first
        if token := request.headers.get(self.TOKEN_HEADER):
            return token

        # Check form field
        if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
            form = await request.form()
            if token := form.get(self.TOKEN_FIELD):
                return token

        return None

    async def _add_csrf_cookie(self, request: Request, call_next):
        response = await call_next(request)

        if self.COOKIE_NAME not in request.cookies:
            token = self._signer.sign({"sid": Token.generate(16)}, expires_in=7200)
            response.set_cookie(
                self.COOKIE_NAME,
                token,
                httponly=True,
                samesite="lax",
                secure=Config.get("app.environment").unwrap_or("production") == "production",
            )

        return response
```

### 1.5 Service Provider

```python
from typing import Self
from contextlib import asynccontextmanager
from neva.arch import ServiceProvider
from neva import Ok, Result

class SecurityServiceProvider(ServiceProvider):
    def register(self) -> Result[Self, str]:
        config = self.app.make(ConfigRepository).unwrap()

        # Hash manager
        hash_config = config.get("hashing").unwrap_or({})

        def create_hash_manager() -> HashManager:
            return HashManager(
                default=hash_config.get("default", "argon2"),
                schemes=hash_config.get("schemes", ["argon2"]),
            )

        self.app.bind(create_hash_manager)

        # Encrypter
        app_key = config.get("app.key")
        if app_key.is_ok:
            key_bytes = AesGcmEncrypter.key_from_base64(app_key.unwrap())
            self.app.bind(lambda: AesGcmEncrypter(key_bytes))

        # Token generator (stateless)
        self.app.bind(TokenGenerator)

        # Signed token manager
        if app_key.is_ok:
            key_bytes = AesGcmEncrypter.key_from_base64(app_key.unwrap())
            self.app.bind(lambda: SignedTokenManager(key_bytes))

        return Ok(self)
```

---

## Layer 2: Authentication (`neva.auth`)

Built-in authentication features. Provides JWT support, password reset flows, and authentication guards.

### Directory Structure

```
neva/auth/
├── __init__.py
├── jwt/
│   ├── __init__.py
│   ├── manager.py             # JWT encoding/decoding
│   ├── middleware.py          # JWT auth middleware
│   └── provider.py            # JWTServiceProvider
├── tokens/
│   ├── __init__.py
│   ├── repository.py          # Token storage interface
│   ├── password_reset.py      # Password reset tokens
│   └── email_verification.py  # Email verification tokens
├── guards/
│   ├── __init__.py
│   ├── guard.py               # Guard interface
│   ├── jwt_guard.py           # JWT-based authentication
│   └── session_guard.py       # Session-based authentication
├── middleware/
│   ├── __init__.py
│   └── authenticate.py        # Auth middleware
├── facade.py                  # Auth facade
└── provider.py                # AuthServiceProvider
```

### Dependencies

- `pyjwt` — JWT encoding/decoding

#### Why PyJWT?

- Simple, focused library for JWT operations
- Actively maintained
- Minimal dependencies
- Covers standard JWT use cases
- Well-documented

### 2.1 JWT Manager

```python
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from neva import Result, Ok, Err

class JWTManager:
    """Manages JWT creation and validation."""

    def __init__(
        self,
        secret: str,
        algorithm: str = "HS256",
        expiry: int = 3600,
        issuer: str | None = None,
        audience: str | None = None,
    ) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._expiry = expiry
        self._issuer = issuer
        self._audience = audience

    def encode(
        self,
        payload: dict[str, Any],
        expires_in: int | None = None,
    ) -> str:
        """Create a JWT with the given payload."""
        now = datetime.now(timezone.utc)
        exp = expires_in if expires_in is not None else self._expiry

        claims = {
            **payload,
            "iat": now,
            "exp": now + timedelta(seconds=exp),
        }

        if self._issuer:
            claims["iss"] = self._issuer
        if self._audience:
            claims["aud"] = self._audience

        return jwt.encode(claims, self._secret, algorithm=self._algorithm)

    def decode(self, token: str) -> Result[dict[str, Any], str]:
        """Decode and validate a JWT."""
        try:
            options = {}
            kwargs = {"algorithms": [self._algorithm]}

            if self._issuer:
                kwargs["issuer"] = self._issuer
            if self._audience:
                kwargs["audience"] = self._audience

            payload = jwt.decode(token, self._secret, **kwargs)
            return Ok(payload)

        except jwt.ExpiredSignatureError:
            return Err("Token has expired")
        except jwt.InvalidAudienceError:
            return Err("Invalid audience")
        except jwt.InvalidIssuerError:
            return Err("Invalid issuer")
        except jwt.InvalidTokenError as e:
            return Err(f"Invalid token: {e}")

    def refresh(self, token: str, expires_in: int | None = None) -> Result[str, str]:
        """Decode a token and issue a new one with refreshed expiry."""
        result = self.decode(token)
        if result.is_err:
            return Err(result.unwrap_err())

        payload = result.unwrap()
        # Remove JWT-specific claims
        for claim in ("iat", "exp", "iss", "aud", "nbf"):
            payload.pop(claim, None)

        return Ok(self.encode(payload, expires_in))
```

### 2.2 Authentication Guards

```python
from abc import ABC, abstractmethod
from typing import Any
from fastapi import Request
from neva import Result, Option

class Authenticatable(Protocol):
    """Protocol for objects that can be authenticated."""

    def get_auth_identifier(self) -> Any:
        """Return the unique identifier for authentication."""
        ...

class Guard(ABC):
    """Interface for authentication guards."""

    @abstractmethod
    async def user(self, request: Request) -> Option[Authenticatable]:
        """Get the authenticated user from the request."""
        ...

    @abstractmethod
    async def validate(self, credentials: dict) -> Result[Authenticatable, str]:
        """Validate credentials and return the user."""
        ...

    @abstractmethod
    def login(self, user: Authenticatable) -> str:
        """Create authentication token/session for user."""
        ...

    @abstractmethod
    async def logout(self, request: Request) -> None:
        """Invalidate the current authentication."""
        ...


class JWTGuard(Guard):
    """JWT-based authentication guard."""

    def __init__(
        self,
        jwt_manager: JWTManager,
        user_provider: "UserProvider",
    ) -> None:
        self._jwt = jwt_manager
        self._users = user_provider

    async def user(self, request: Request) -> Option[Authenticatable]:
        token = self._extract_token(request)
        if token.is_nothing:
            return Nothing()

        result = self._jwt.decode(token.unwrap())
        if result.is_err:
            return Nothing()

        payload = result.unwrap()
        user_id = payload.get("sub")
        if user_id is None:
            return Nothing()

        return await self._users.find_by_id(user_id)

    async def validate(self, credentials: dict) -> Result[Authenticatable, str]:
        user = await self._users.find_by_credentials(credentials)
        if user.is_nothing:
            return Err("Invalid credentials")
        return Ok(user.unwrap())

    def login(self, user: Authenticatable) -> str:
        return self._jwt.encode({"sub": user.get_auth_identifier()})

    async def logout(self, request: Request) -> None:
        # JWT is stateless; client should discard token
        # For token blacklisting, implement a token repository
        pass

    def _extract_token(self, request: Request) -> Option[str]:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return Some(auth_header[7:])
        return Nothing()
```

### 2.3 Password Reset Tokens

```python
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from neva import Result, Ok, Err, Option

class TokenRepository(ABC):
    """Interface for storing authentication tokens."""

    @abstractmethod
    async def create(self, user_id: str, token: str, expires_at: datetime) -> None:
        """Store a token."""
        ...

    @abstractmethod
    async def find(self, token: str) -> Option[dict]:
        """Find a token record."""
        ...

    @abstractmethod
    async def delete(self, token: str) -> None:
        """Delete a token."""
        ...

    @abstractmethod
    async def delete_expired(self) -> int:
        """Delete all expired tokens. Returns count deleted."""
        ...


class PasswordResetManager:
    """Manages password reset tokens."""

    def __init__(
        self,
        repository: TokenRepository,
        hasher: HashManager,
        expiry: int = 3600,  # 1 hour
    ) -> None:
        self._repository = repository
        self._hasher = hasher
        self._expiry = expiry

    async def create_token(self, user_id: str) -> str:
        """Create a password reset token for a user."""
        # Generate random token
        raw_token = TokenGenerator.generate(32)

        # Store hashed version
        hashed = self._hasher.make(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self._expiry)

        await self._repository.create(user_id, hashed, expires_at)

        # Return raw token (sent to user via email)
        return raw_token

    async def verify_token(self, token: str) -> Result[str, str]:
        """Verify a token and return the user_id if valid."""
        # Find all non-expired tokens and check against each
        # (We can't look up by token since we only store hashes)
        record = await self._repository.find(token)

        if record.is_nothing:
            return Err("Invalid or expired token")

        data = record.unwrap()

        if data["expires_at"] < datetime.now(timezone.utc):
            await self._repository.delete(token)
            return Err("Token has expired")

        if not self._hasher.check(token, data["token_hash"]):
            return Err("Invalid token")

        return Ok(data["user_id"])

    async def invalidate_token(self, token: str) -> None:
        """Invalidate a token after use."""
        await self._repository.delete(token)
```

### 2.4 Configuration

```python
# config/auth.py
import os

config = {
    "defaults": {
        "guard": "jwt",
    },
    "guards": {
        "jwt": {
            "driver": "jwt",
            "secret": os.environ.get("JWT_SECRET"),
            "algorithm": "HS256",
            "expiry": 3600,
            "issuer": None,
            "audience": None,
        },
        "session": {
            "driver": "session",
            "lifetime": 7200,
        },
    },
    "passwords": {
        "users": {
            "table": "password_reset_tokens",
            "expiry": 3600,
        },
    },
    "verification": {
        "expiry": 86400,  # 24 hours
    },
}
```

---

## Layer 3: API Tokens (`neva-sanctum`)

Separate package for database-backed API tokens.

### Purpose

Provides simple, database-stored API tokens for:

- Personal access tokens (like GitHub PATs)
- Mobile app authentication
- Third-party API access without full OAuth

### Directory Structure

```
neva-sanctum/
├── src/neva_sanctum/
│   ├── __init__.py
│   ├── models/
│   │   └── personal_access_token.py
│   ├── sanctum.py             # Main API
│   ├── middleware.py          # Token auth middleware
│   ├── guard.py               # Sanctum guard
│   └── provider.py            # SanctumServiceProvider
├── pyproject.toml
└── README.md
```

### Dependencies

- `neva`
- `tortoise-orm` (or database layer)

### Key Features

```python
# Creating tokens
token = await user.create_token(
    name="mobile-app",
    abilities=["read", "write"],
    expires_at=datetime.now() + timedelta(days=30),
)
# Returns: "neva_1a2b3c4d5e..."  (plaintext token, only shown once)

# Using tokens
# Authorization: Bearer neva_1a2b3c4d5e...

# Checking abilities
if request.user.token_can("write"):
    # Allow write operation

# Revoking tokens
await user.tokens().where(name="mobile-app").delete()
await user.tokens().delete()  # Revoke all
```

### Model

```python
from tortoise import fields
from tortoise.models import Model

class PersonalAccessToken(Model):
    id = fields.IntField(pk=True)
    tokenable_type = fields.CharField(max_length=255)  # e.g., "User"
    tokenable_id = fields.IntField()
    name = fields.CharField(max_length=255)
    token = fields.CharField(max_length=64, unique=True)  # Hashed
    abilities = fields.JSONField(default=list)
    last_used_at = fields.DatetimeField(null=True)
    expires_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "personal_access_tokens"
        indexes = [("tokenable_type", "tokenable_id")]
```

---

## Layer 4: OAuth2 Server (`neva-passport`)

Separate package for full OAuth2 server implementation.

### Purpose

Provides complete OAuth2 server capabilities:

- Authorization code grant
- Client credentials grant
- Refresh tokens
- Token revocation
- OpenID Connect (optional)

### Dependencies

- `neva`
- `authlib` — handles OAuth2/OIDC complexity
- `tortoise-orm`

#### Why Authlib?

- Comprehensive OAuth2/OIDC implementation
- Spec-compliant
- Actively maintained
- Well-documented
- Handles the complex parts of OAuth correctly

### Directory Structure

```
neva-passport/
├── src/neva_passport/
│   ├── __init__.py
│   ├── models/
│   │   ├── client.py
│   │   ├── authorization_code.py
│   │   ├── access_token.py
│   │   └── refresh_token.py
│   ├── grants/
│   │   ├── authorization_code.py
│   │   ├── client_credentials.py
│   │   ├── password.py
│   │   └── refresh_token.py
│   ├── endpoints/
│   │   ├── authorize.py
│   │   ├── token.py
│   │   ├── revoke.py
│   │   └── introspect.py
│   ├── server.py              # OAuth2 server setup
│   └── provider.py            # PassportServiceProvider
├── pyproject.toml
└── README.md
```

### Configuration

```python
# config/passport.py
config = {
    "token_expiry": {
        "access_token": 3600,       # 1 hour
        "refresh_token": 604800,    # 7 days
        "authorization_code": 600,  # 10 minutes
    },
    "grants": [
        "authorization_code",
        "client_credentials",
        "refresh_token",
    ],
    "scopes": {
        "read": "Read access to resources",
        "write": "Write access to resources",
        "profile": "Access to user profile",
    },
}
```

---

## Summary

| Feature | Module | Status | Dependencies |
|---------|--------|--------|--------------|
| Password hashing | `neva.security` | Core | `pwdlib` |
| Encryption | `neva.security` | Core | `cryptography` |
| Token generation | `neva.security` | Core | stdlib |
| CSRF protection | `neva.security` | Core | — |
| JWT authentication | `neva.auth` | Built-in | `pyjwt` |
| Password reset | `neva.auth` | Built-in | — |
| Auth guards | `neva.auth` | Built-in | — |
| API tokens | `neva-sanctum` | Extension | `tortoise-orm` |
| OAuth2 server | `neva-passport` | Extension | `authlib` |

## Implementation Priority

1. **Phase 1**: `neva.security` — foundational primitives
2. **Phase 2**: `neva.auth` with JWT — covers most API auth needs
3. **Phase 3**: `neva-sanctum` — when database-backed tokens needed
4. **Phase 4**: `neva-passport` — when full OAuth2 required
