import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_data = tempfile.TemporaryDirectory()
os.environ.update(DATA_DIR=_data.name, ADMIN_PASSWORD='test-password-only-123456', BASE_URL='', COOKIE_SECURE='false', MAX_UPLOAD_BYTES='5242880', COOKIE_MAX_AGE='86400')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from main import app  # noqa: E402
import security  # noqa: E402


@pytest.fixture(autouse=True)
def reset():
    security._session = None
    for path in Path(_data.name).iterdir():
        path.unlink()
    yield
    security._session = None


@pytest.fixture
def client():
    with TestClient(app, follow_redirects=False) as c:
        yield c
