import httpx
from fastapi import Request
from fastapi.responses import Response

from ..config import settings

# Shared clients (initialized in lifespan)
_ocr_client: httpx.AsyncClient | None = None
_proxy_client: httpx.AsyncClient | None = None


async def init_clients():
    global _ocr_client, _proxy_client
    _ocr_client = httpx.AsyncClient(base_url=settings.OCR_API_URL, timeout=30)
    _proxy_client = httpx.AsyncClient(base_url=settings.PROXY_API_URL, timeout=30, verify=False)


async def close_clients():
    if _ocr_client:
        await _ocr_client.aclose()
    if _proxy_client:
        await _proxy_client.aclose()


_OCR_ROUTES = {"/ocr"}


async def proxy_request(request: Request) -> Response:
    path = request.url.path
    client = _ocr_client if path in _OCR_ROUTES else _proxy_client

    body = await request.body()
    url = path
    if request.url.query:
        url = f"{path}?{request.url.query}"

    upstream = await client.request(
        method=request.method,
        url=url,
        content=body,
        headers={
            k: v for k, v in request.headers.items()
            if k.lower() not in ("host", "x-api-key", "content-length")
        },
    )

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=dict(upstream.headers),
        media_type=upstream.headers.get("content-type"),
    )
