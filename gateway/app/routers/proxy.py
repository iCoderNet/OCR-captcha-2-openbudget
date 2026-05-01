from fastapi import APIRouter, Request
from fastapi.responses import Response

from ..proxy.reverse_proxy import proxy_request

router = APIRouter(tags=["Proxy"])

# All routes proxied to upstream services.
# Auth + billing is handled by APIKeyMiddleware before reaching here.

PROXY_ROUTES = [
    ("GET", "/boards"),
    ("GET", "/budget-params"),
    ("GET", "/news"),
    ("GET", "/initiatives/{initiative_id}"),
    ("GET", "/my-school/boards/active"),
    ("GET", "/board/{board_id}/initiatives"),
    ("GET", "/initiative/{initiative_id}/count"),
    ("GET", "/statistics/boards"),
    ("GET", "/statistics/board/{board_id}/budget"),
    ("GET", "/votes/{initiative_token}"),
    ("GET", "/captcha/solve"),
    ("POST", "/vote/start"),
    ("POST", "/vote/{otp_key}/verify"),
    ("POST", "/vote/initiative-token"),
]


async def _proxy(request: Request) -> Response:
    return await proxy_request(request)


for _method, _path in PROXY_ROUTES:
    router.add_api_route(_path, _proxy, methods=[_method])
