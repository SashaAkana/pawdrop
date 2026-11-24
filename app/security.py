import re
import secrets
import time
from threading import Lock

from fastapi import HTTPException, Request

from config import ADMIN_PASSWORD, COOKIE_MAX_AGE, COOKIE_NAME

KEY_RE = re.compile(r'[A-Za-z0-9_-]{8,128}')
_lock = Lock()
# A single active administrator session. Deliberately process-local.
_session: tuple[str, str, float] | None = None


def equal(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode('utf-8'), b.encode('utf-8'))


def validate_uuid(value: str) -> str:
    if not KEY_RE.fullmatch(value):
        raise HTTPException(404, 'Not found')
    return value


def new_key(value: str = '') -> str:
    if not value:
        return secrets.token_urlsafe(32)
    if len(value) < 22 or not KEY_RE.fullmatch(value):
        raise HTTPException(400, 'Use a random key of 22–128 URL-safe characters or leave blank')
    return value


def check_password(password: str) -> bool:
    return equal(password, ADMIN_PASSWORD)


def start_session() -> str:
    global _session
    with _lock:
        token = secrets.token_urlsafe(32)
        _session = (token, secrets.token_urlsafe(32), time.monotonic() + COOKIE_MAX_AGE)
        return token


def session_csrf(request: Request) -> str | None:
    global _session
    with _lock:
        if _session is None:
            return None
        token, csrf, expires = _session
        if time.monotonic() >= expires:
            _session = None
            return None
        return csrf if equal(request.cookies.get(COOKIE_NAME, ''), token) else None


def require_session(request: Request) -> str:
    csrf = session_csrf(request)
    if csrf is None:
        raise HTTPException(403, 'Login required')
    return csrf


def require_csrf(request: Request, value: str) -> None:
    if not equal(require_session(request), value):
        raise HTTPException(403, 'Invalid CSRF token')


def end_session(request: Request, csrf: str) -> None:
    global _session
    with _lock:
        if _session is None or time.monotonic() >= _session[2] or not equal(request.cookies.get(COOKIE_NAME, ''), _session[0]) or not equal(csrf, _session[1]):
            raise HTTPException(403, 'Invalid session or CSRF token')
        _session = None
