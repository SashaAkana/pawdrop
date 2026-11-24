import os
from pathlib import Path
from urllib.parse import urlsplit

DATA_DIR = Path(os.getenv('DATA_DIR', '/data'))
META_FILE = DATA_DIR / 'meta.json'
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')
if len(ADMIN_PASSWORD) < 16 or ADMIN_PASSWORD == 'replace-with-a-long-random-password':
    raise RuntimeError('Set ADMIN_PASSWORD to a strong password (at least 16 characters)')
BASE_URL = os.getenv('BASE_URL', '').rstrip('/')
if BASE_URL:
    url = urlsplit(BASE_URL)
    if url.scheme not in {'http', 'https'} or not url.hostname or url.username or url.password or url.path or url.query or url.fragment or any(c.isspace() for c in BASE_URL):
        raise RuntimeError('BASE_URL must be an HTTP(S) origin without a path')
MAX_UPLOAD_BYTES = int(os.getenv('MAX_UPLOAD_BYTES', str(5 * 1024 * 1024)))
if not 1 <= MAX_UPLOAD_BYTES <= 5 * 1024 * 1024:
    raise RuntimeError('MAX_UPLOAD_BYTES must be between 1 and 5242880')
COOKIE_NAME = 'pawdrop_session'
COOKIE_MAX_AGE = int(os.getenv('COOKIE_MAX_AGE', '86400'))
if not 1 <= COOKIE_MAX_AGE <= 86400:
    raise RuntimeError('COOKIE_MAX_AGE must be between 1 and 86400')
_cookie_secure = os.getenv('COOKIE_SECURE', 'true').lower()
if _cookie_secure not in {'1', 'true', 'yes', 'on', '0', 'false', 'no', 'off'}:
    raise RuntimeError('COOKIE_SECURE must be a boolean')
COOKIE_SECURE = _cookie_secure in {'1', 'true', 'yes', 'on'}
if not COOKIE_SECURE and (
    os.getenv('BIND_HOST', '127.0.0.1') not in {'127.0.0.1', '::1', 'localhost'}
    or (BASE_URL and urlsplit(BASE_URL).hostname not in {'127.0.0.1', '::1', 'localhost'})
):
    raise RuntimeError('Insecure cookies are allowed only for loopback demos')
