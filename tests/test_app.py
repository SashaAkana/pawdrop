import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from config import DATA_DIR, COOKIE_NAME, MAX_UPLOAD_BYTES
from main import app
import security
import storage

PASSWORD = 'test-password-only-123456'
KEY = 'a_random_key_for_testing_123456'


def login(client):
    res = client.post('/admin/login', data={'password': PASSWORD})
    assert res.status_code == 303
    return re.search(r'name="csrf" value="([^"]+)"', client.get('/admin').text)[1]


def upload(client, csrf, key=KEY, content=b'hello', name='note.txt'):
    return client.post('/admin/upload', data={'uuid': key, 'csrf': csrf}, files={'file': (name, content, 'text/plain')})


def test_health_and_hidden_docs(client):
    assert client.get('/health').text == 'ok\n'
    assert client.get('/').headers['location'] == '/admin'
    for path in ('/docs', '/redoc', '/openapi.json'):
        assert client.get(path).status_code == 404


def test_unauthenticated(client):
    assert 'Sign in' in client.get('/admin').text
    assert upload(client, '').status_code == 403
    assert client.post('/admin/delete', data={'uuid': KEY}).status_code == 403
    assert client.get('/admin/download/' + KEY).status_code == 403
    assert client.get('/' + KEY).status_code == 404


def test_wrong_unicode_password(client):
    assert client.post('/admin/login', data={'password': '猫'}).status_code == 401


def test_cross_site_login(client):
    assert client.post('/admin/login', data={'password': PASSWORD}, headers={'sec-fetch-site': 'cross-site'}).status_code == 403


def test_session_replaced_and_revoked(client):
    csrf = login(client)
    old = client.cookies.get(COOKIE_NAME)
    csrf2 = login(client)
    assert csrf != csrf2
    new = client.cookies.get(COOKIE_NAME)
    with TestClient(app, cookies={COOKIE_NAME: old}) as other:
        assert other.get('/admin/download/' + KEY).status_code == 403
    assert client.post('/admin/logout', data={'csrf': csrf2}).status_code == 303
    with TestClient(app, cookies={COOKIE_NAME: new}) as other:
        assert other.get('/admin/download/' + KEY).status_code == 403


def test_session_expires(client, monkeypatch):
    login(client)
    expiry = security._session[2]
    monkeypatch.setattr(security.time, 'monotonic', lambda: expiry + 1)
    assert client.get('/admin/download/' + KEY).status_code == 403


def test_csrf(client):
    csrf = login(client)
    assert upload(client, 'bad').status_code == 403
    assert upload(client, csrf).status_code == 303
    assert client.post('/admin/delete', data={'uuid': KEY, 'csrf': 'bad'}).status_code == 403
    assert client.post('/admin/logout', data={'csrf': 'bad'}).status_code == 403
    assert client.get('/' + KEY).status_code == 200


def test_round_trip(client):
    csrf = login(client)
    assert upload(client, csrf).status_code == 303
    for url in ('/' + KEY, '/admin/download/' + KEY):
        r = client.get(url)
        assert r.content == b'hello'
        assert r.headers['content-disposition'].startswith('attachment;')
        assert r.headers['cache-control'] == 'no-store'
        assert r.headers['referrer-policy'] == 'no-referrer'
        assert r.headers['x-content-type-options'] == 'nosniff'
    assert client.post('/admin/delete', data={'uuid': KEY, 'csrf': csrf}).status_code == 303
    assert client.get('/' + KEY).status_code == 404


def test_generated_key(client):
    csrf = login(client)
    for _ in range(2):
        assert upload(client, csrf, key='').status_code == 303
    keys = list(storage.load_meta())
    assert len(keys) == 2 and all(len(k) == 43 for k in keys)


@pytest.mark.parametrize('key', ['short', '../escape', 'x'*129, 'a b'*20])
def test_invalid_key(client, key):
    assert upload(client, login(client), key=key).status_code == 400


def test_duplicate_preserves_original(client):
    csrf = login(client)
    assert upload(client, csrf).status_code == 303
    assert upload(client, csrf, content=b'overwrite').status_code == 409
    assert client.get('/' + KEY).content == b'hello'


def test_size_boundary(client):
    csrf = login(client)
    assert upload(client, csrf, content=b'x'*MAX_UPLOAD_BYTES).status_code == 303
    assert upload(client, csrf, key=KEY+'2', content=b'x'*(MAX_UPLOAD_BYTES+1)).status_code == 413
    assert not (DATA_DIR / (KEY+'2')).exists()


def test_filename_and_host(client):
    csrf = login(client)
    assert upload(client, csrf, name='test.exe').status_code == 400
    assert upload(client, csrf, name='<img onerror=alert(1)>.txt').status_code == 303
    r = client.get('/admin', headers={'Host': 'untrusted.example'})
    assert '&lt;img' in r.text and '<img onerror' not in r.text
    assert 'untrusted.example' not in r.text


def test_legacy_metadata(client):
    (DATA_DIR / 'old_key1').write_bytes(b'old')
    storage._save_meta({'old_key1': {'filename': 'old.txt'}})
    assert client.get('/old_key1').content == b'old'


def test_meta_failure_rollback(client, monkeypatch):
    csrf = login(client)
    def fail(_):
        raise OSError('simulated write error')
    monkeypatch.setattr(storage, '_save_meta', fail)
    with pytest.raises(OSError):
        upload(client, csrf)
    assert not (DATA_DIR / KEY).exists()
    assert not list(DATA_DIR.glob('.upload-*'))


def test_parallel_duplicates(client):
    csrf = login(client)
    token = client.cookies.get(COOKIE_NAME)
    def send(i):
        with TestClient(app, cookies={COOKIE_NAME: token}, follow_redirects=False) as other:
            return upload(other, csrf, content=str(i).encode()).status_code
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert sorted(pool.map(send, range(4))) == [303,409,409,409]
    assert len(storage.load_meta()) == 1
    assert not list(DATA_DIR.glob('.upload-*'))


@pytest.mark.parametrize('settings', [
    {'COOKIE_SECURE': 'typo'},
    {'COOKIE_SECURE': 'false', 'BASE_URL': 'https://drop.example.com'},
    {'COOKIE_SECURE': 'false', 'BIND_HOST': '0.0.0.0'},
    {'ADMIN_PASSWORD': 'replace-with-a-long-random-password'},
])
def test_unsafe_config_rejected(settings):
    import os
    import subprocess
    import sys
    env = dict(os.environ, **settings)
    result = subprocess.run([sys.executable, '-c', 'import config'], cwd=Path(__file__).resolve().parents[1] / 'app', env=env, capture_output=True)
    assert result.returncode != 0
    assert b'RuntimeError' in result.stderr
