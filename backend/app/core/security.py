from datetime import datetime, timedelta, timezone
import os

import jwt
from pwdlib import PasswordHash


# Password hashing
password_hasher = PasswordHash.recommended()

# JWT settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-secret-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)


def hash_password(password: str) -> str:
    """Convert plain password into a secure hash."""
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check whether entered password matches stored hash."""
    return password_hasher.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create JWT access token for authenticated user."""

    now = datetime.now(timezone.utc)

    expire = now + (
        expires_delta
        if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """Verify JWT token and return its payload."""

    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
    )