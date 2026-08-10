from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import (
	create_access_token,
	create_refresh_token,
	decode_token,
	hash_password,
	verify_password,
)
from app.core.config import get_settings
from app.core.rate_limit import InMemoryRateLimiter
from app.models.user import User
from app.schemas.auth import (
	AuthMeResponse,
	LoginRequest,
	RefreshRequest,
	RegisterRequest,
	TokenResponse,
	UserResponse,
)
from app.services.audit import record_audit_event

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
login_rate_limiter = InMemoryRateLimiter(
	limit=settings.auth_rate_limit_per_minute,
	window_seconds=settings.auth_rate_limit_window_seconds,
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
	existing_user = db.scalar(
		select(User).where(
			or_(
				User.email == payload.email.lower(),
				User.username == payload.username,
			)
		)
	)
	if existing_user is not None:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already exists")

	user = User(
		email=payload.email.lower(),
		username=payload.username,
		hashed_password=hash_password(payload.password),
		role=payload.role,
		is_active=True,
	)
	db.add(user)
	db.flush()
	record_audit_event(
		db,
		user=user,
		action="auth.register",
		resource_type="user",
		resource_id=str(user.id),
		raw_address=None,
	)
	db.commit()
	db.refresh(user)
	return user


@router.post("/token", response_model=TokenResponse)
def login(
	payload: LoginRequest,
	request: Request,
	db: Session = Depends(get_db),
) -> TokenResponse:
	client_ip = request.client.host if request.client else "unknown"
	rate_key = f"{client_ip}:{payload.username.strip().lower()}"
	if not login_rate_limiter.is_allowed(rate_key):
		raise HTTPException(
			status_code=status.HTTP_429_TOO_MANY_REQUESTS,
			detail="Too many login attempts. Please try again later.",
		)

	user = db.scalar(select(User).where(User.username == payload.username))
	if user is None or not verify_password(payload.password, user.hashed_password):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
	if not user.is_active:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

	record_audit_event(
		db,
		user=user,
		action="auth.login",
		resource_type="user",
		resource_id=str(user.id),
		raw_address=None,
	)
	db.commit()

	access_token = create_access_token(str(user.id), user.role.value)
	refresh_token = create_refresh_token(str(user.id))
	return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
	try:
		token_payload = decode_token(payload.refresh_token)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
	if token_payload.get("type") != "refresh":
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

	subject = token_payload.get("sub")
	if not subject:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

	user = db.scalar(select(User).where(User.id == subject))
	if user is None or not user.is_active:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

	record_audit_event(
		db,
		user=user,
		action="auth.refresh",
		resource_type="user",
		resource_id=str(user.id),
		raw_address=None,
	)
	db.commit()

	return TokenResponse(
		access_token=create_access_token(str(user.id), user.role.value),
		refresh_token=create_refresh_token(str(user.id)),
	)


@router.get("/me", response_model=AuthMeResponse)
def me(current_user: User = Depends(get_current_user)) -> AuthMeResponse:
	return AuthMeResponse(user=current_user)
