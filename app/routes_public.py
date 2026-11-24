from urllib.parse import quote

from fastapi import APIRouter
from fastapi.responses import Response

from security import validate_uuid
from storage import read_file

router = APIRouter()


def file_download(key: str) -> Response:
    content, filename = read_file(validate_uuid(key))
    return Response(content, media_type='text/plain; charset=utf-8', headers={
        'Content-Disposition': "attachment; filename*=UTF-8''" + quote(filename, safe=''),
    })


@router.get('/{uuid}')
def download(uuid: str):
    return file_download(uuid)
