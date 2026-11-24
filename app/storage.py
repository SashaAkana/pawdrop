import json
import os
import tempfile
from threading import RLock

from fastapi import HTTPException, UploadFile

from config import DATA_DIR, MAX_UPLOAD_BYTES, META_FILE

_lock = RLock()


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)


def load_meta() -> dict:
    with _lock:
        if not META_FILE.exists():
            return {}
        try:
            data = json.loads(META_FILE.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or any(not isinstance(v, dict) for v in data.values()):
                raise ValueError('Invalid metadata')
            return data
        except (ValueError, OSError):
            raise HTTPException(500, 'Metadata unavailable') from None


def _save_meta(meta: dict) -> None:
    fd, path = tempfile.mkstemp(dir=DATA_DIR, prefix='.meta-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(meta, out, ensure_ascii=False, indent=2)
            out.flush()
            os.fsync(out.fileno())
        os.replace(path, META_FILE)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def clean_filename(name: str | None) -> str:
    if not isinstance(name, str):
        raise HTTPException(400, 'Only .txt filenames are allowed')
    name = name.replace('\\', '/').rsplit('/', 1)[-1]
    if not name.lower().endswith('.txt') or len(name) > 255 or any(ord(c) < 32 or ord(c) == 127 for c in name):
        raise HTTPException(400, 'Only .txt filenames are allowed')
    return name


async def save_upload(key: str, file: UploadFile) -> None:
    filename = clean_filename(file.filename)
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, 'File exceeds configured size limit')
    with _lock:
        meta = load_meta()
        dest = DATA_DIR / key
        if key in meta or dest.exists():
            raise HTTPException(409, 'Key already exists; delete it or use another key')
        fd, path = tempfile.mkstemp(dir=DATA_DIR, prefix='.upload-')
        try:
            with os.fdopen(fd, 'wb') as out:
                out.write(content)
                out.flush()
                os.fsync(out.fileno())
            os.replace(path, dest)
            try:
                meta[key] = {'filename': filename}
                _save_meta(meta)
            except Exception:
                dest.unlink(missing_ok=True)
                raise
        finally:
            if os.path.exists(path):
                os.unlink(path)


def delete_file(key: str) -> None:
    with _lock:
        meta = load_meta()
        if key in meta:
            del meta[key]
            _save_meta(meta)
            (DATA_DIR / key).unlink(missing_ok=True)


def read_file(key: str) -> tuple[bytes, str]:
    with _lock:
        meta = load_meta()
        if key not in meta:
            raise HTTPException(404, 'Not found')
        try:
            with (DATA_DIR / key).open('rb') as stream:
                content = stream.read(5 * 1024 * 1024 + 1)
        except FileNotFoundError:
            raise HTTPException(404, 'Not found') from None
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(500, 'Stored file exceeds supported size')
        try:
            filename = clean_filename(meta[key].get('filename'))
        except HTTPException:
            filename = 'download.txt'
        return content, filename
