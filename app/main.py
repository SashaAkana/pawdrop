from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from routes_admin import router as admin_router
from routes_public import router as public_router
from storage import ensure_data_dir

app = FastAPI(title='PawDrop', docs_url=None, redoc_url=None, openapi_url=None)
ensure_data_dir()


@app.middleware('http')
async def response_policy(request: Request, call_next):
    # Nginx is the external body-size boundary. Reject oversized declared bodies early as well.
    length = request.headers.get('content-length')
    if length is not None and (not length.isascii() or not length.isdecimal() or len(length) > 12 or int(length) > 6 * 1024 * 1024):
        response = PlainTextResponse('Request too large or invalid', status_code=413)
    else:
        response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
    return response


@app.get('/health')
def health():
    return PlainTextResponse('ok\n')


app.include_router(admin_router)
app.include_router(public_router)
