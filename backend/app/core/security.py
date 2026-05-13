from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from fastapi import Cookie, Header, HTTPException, status

from app.core.config import Settings, get_settings

_admin_sessions: dict[str, datetime] = {}


def is_valid_admin_secret(value: str | None, settings: Settings | None = None) -> bool:
    cfg = settings or get_settings()
    return bool(value) and value == cfg.admin_secret


def create_admin_session(settings: Settings | None = None) -> str:
    cfg = settings or get_settings()
    token = token_urlsafe(32)
    _admin_sessions[token] = datetime.now(timezone.utc) + timedelta(seconds=cfg.admin_session_ttl_seconds)
    return token


def is_valid_admin_session(token: str | None) -> bool:
    if not token:
        return False
    expires_at = _admin_sessions.get(token)
    if not expires_at:
        return False
    if expires_at <= datetime.now(timezone.utc):
        _admin_sessions.pop(token, None)
        return False
    return True


def require_admin(
    x_admin_secret: str | None = Header(default=None, alias="X-Admin-Secret"),
    admin_session: str | None = Cookie(default=None),
) -> None:
    cfg = get_settings()
    if is_valid_admin_secret(x_admin_secret, cfg) or is_valid_admin_session(admin_session):
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Admin credentials are required for document mutation.",
    )


def clear_admin_sessions_for_tests() -> None:
    _admin_sessions.clear()
