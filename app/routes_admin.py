from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.datastructures import UploadFile

from config import BASE_URL, COOKIE_MAX_AGE, COOKIE_NAME, COOKIE_SECURE
from routes_public import file_download
from security import check_password, end_session, new_key, require_csrf, require_session, session_csrf, start_session, validate_uuid
from storage import delete_file, load_meta, save_upload
from templates import render_admin, render_admin_rows, render_login

router = APIRouter()


def field(form, name: str, default: str = '') -> str:
    value = form.get(name, default)
    if not isinstance(value, str):
        raise HTTPException(400, 'Invalid form field')
    return value


@router.get('/')
def root_redirect():
    return RedirectResponse('/admin', status_code=307)


@router.get('/admin', response_class=HTMLResponse)
def admin_get(request: Request):
    csrf = session_csrf(request)
    if csrf is None:
        return HTMLResponse(render_login())
    return HTMLResponse(render_admin(render_admin_rows(load_meta(), BASE_URL, csrf), csrf))


@router.post('/admin/login')
async def admin_login(request: Request):
    if request.headers.get('sec-fetch-site') == 'cross-site':
        raise HTTPException(403, 'Cross-site login denied')
    async with request.form(max_files=0, max_fields=2, max_part_size=4096) as form:
        if check_password(field(form, 'password')):
            resp = RedirectResponse('/admin', status_code=303)
            resp.set_cookie(COOKIE_NAME, start_session(), httponly=True, samesite='strict', secure=COOKIE_SECURE, max_age=COOKIE_MAX_AGE)
            return resp
    return HTMLResponse(render_login('Incorrect password'), status_code=401)


@router.post('/admin/logout')
async def admin_logout(request: Request):
    require_session(request)
    async with request.form(max_files=0, max_fields=2) as form:
        end_session(request, field(form, 'csrf'))
    resp = RedirectResponse('/admin', status_code=303)
    resp.delete_cookie(COOKIE_NAME, secure=COOKIE_SECURE, httponly=True, samesite='strict')
    return resp


@router.post('/admin/upload')
async def admin_upload(request: Request):
    require_session(request)
    async with request.form(max_files=1, max_fields=2, max_part_size=4096) as form:
        require_csrf(request, field(form, 'csrf'))
        key = new_key(field(form, 'uuid'))
        file = form.get('file')
        if not isinstance(file, UploadFile):
            raise HTTPException(400, 'File required')
        await save_upload(key, file)
    return RedirectResponse('/admin', status_code=303)


@router.post('/admin/delete')
async def admin_delete(request: Request):
    require_session(request)
    async with request.form(max_files=0, max_fields=2) as form:
        require_csrf(request, field(form, 'csrf'))
        delete_file(validate_uuid(field(form, 'uuid')))
    return RedirectResponse('/admin', status_code=303)


@router.get('/admin/download/{uuid}')
def admin_download(request: Request, uuid: str):
    require_session(request)
    return file_download(uuid)
