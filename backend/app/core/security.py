from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
	return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
	return pwd_context.verify(password, hashed_password)


def create_access_token(subject: str, role: str) -> str:
	settings = get_settings()
	expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
	payload = {
		"sub": subject,
		"role": role,
		"type": "access",
		"exp": expires_at,
	}
	return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
	settings = get_settings()
	expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
	payload = {
		"sub": subject,
		"type": "refresh",
		"exp": expires_at,
	}
	return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
	settings = get_settings()
	try:
		payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
	except JWTError as exc:
		raise ValueError("Invalid or expired token") from exc
	return payload
