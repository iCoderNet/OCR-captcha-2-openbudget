"""
OpenBudget.uz 3-tomon proxy API
===============================
- openbudget.uz barcha endpointlarini mirror qiladi
- Captcha avtomatik OCR orqali hal qilinadi
- Ovoz berish oqimi to'liq avtomatlashtirilgan

Port: 8521
"""

import io
import base64

import httpx
from fastapi import FastAPI, Query, Path, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from predict import predict_full_captcha

# ─────────────────────────────────────────────
# Sozlamalar
# ─────────────────────────────────────────────
BASE_URL = "https://openbudget.uz"

# Ilovaning asl headerlari (APK dan olingan)
APP_HEADERS = {
    "User-Agent": "OchiqBudjetApp/android 2.14.0 (SM-G988N)",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Host": "openbudget.uz",
}

# APK dan olingan statik captcha access token
ACCESS_CAPTCHA = "czM2ZTEzMms3MnIxMDhlNTV0"

# ─────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────
app = FastAPI(
    title="OpenBudget.uz Proxy API",
    description="openbudget.uz ustiga qurilgan 3-tomon API. Captcha avtomatik OCR bilan hal qilinadi.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Yordamchi funksiyalar
# ─────────────────────────────────────────────

def _headers(extra: dict = None) -> dict:
    h = dict(APP_HEADERS)
    if extra:
        h.update(extra)
    return h


async def _get(path: str, params: dict = None, extra_headers: dict = None):
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        r = await client.get(
            BASE_URL + path,
            params=params,
            headers=_headers(extra_headers),
        )
    return r


async def _post(path: str, json_body: dict, extra_headers: dict = None):
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        r = await client.post(
            BASE_URL + path,
            json=json_body,
            headers=_headers({"Content-Type": "application/json", **(extra_headers or {})}),
        )
    return r


def _solve_captcha_b64(image_b64: str):
    """Base64 rasm → OCR yechim (matn va hisob)"""
    image_bytes = base64.b64decode(image_b64)
    image_io = io.BytesIO(image_bytes)
    text = predict_full_captcha(image_io)
    try:
        solution = eval(text)  # "3+4" → 7
    except Exception:
        solution = None
    return text, solution


def _resp(r: httpx.Response):
    """httpx javobini FastAPI JSONResponse ga aylantirish"""
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}
    return JSONResponse(status_code=r.status_code, content=data)


# ─────────────────────────────────────────────
# Pydantic modellar
# ─────────────────────────────────────────────

class VoteStartPayload(BaseModel):
    initiativeId: str
    boardId: int
    phoneNumber: str  # "998XXXXXXXXX" formatda


class VoteVerifyPayload(BaseModel):
    otpKey: str
    otpCode: str
    initiativeId: str


class InitiativeTokenPayload(BaseModel):
    initiativeId: str


# ═══════════════════════════════════════════════
# GET endpointlar — oddiy proxy
# ═══════════════════════════════════════════════

@app.get("/boards", summary="Barcha boardlar ro'yxati")
async def get_boards():
    """GET /api/v1/boards"""
    r = await _get("/api/v1/boards")
    return _resp(r)


@app.get("/budget-params", summary="Byudjet parametrlari")
async def get_budget_params():
    """GET /api/v1/budget-params"""
    r = await _get("/api/v1/budget-params")
    return _resp(r)


@app.get("/news", summary="Yangiliklar")
async def get_news(
    offset: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=100),
):
    """GET /api/v1/news?offset=&limit="""
    r = await _get("/api/v1/news", params={"offset": offset, "limit": limit})
    return _resp(r)


@app.get("/initiatives/{initiative_id}", summary="Bitta initiative ma'lumoti")
async def get_initiative(initiative_id: str = Path(...)):
    """GET /api/v1/initiatives/{id}"""
    r = await _get(
        f"/api/v1/initiatives/{initiative_id}",
        extra_headers={"Referer": f"{BASE_URL}/boards-list/0/{initiative_id}"},
    )
    return _resp(r)


@app.get("/my-school/boards/active", summary="Aktiv maktab boardlari")
async def get_my_school_boards():
    """GET /api/v1/my-school/boards/active"""
    r = await _get("/api/v1/my-school/boards/active")
    return _resp(r)


@app.get("/board/{board_id}/initiatives", summary="Board bo'yicha initiativlar (sahifalash)")
async def get_board_initiatives(
    board_id: int = Path(...),
    size: int = Query(12, ge=1, le=100),
    page: int = Query(0, ge=0),
    stage: Optional[str] = Query(None, description="PASSED | NOT_PASSED | WINNER"),
):
    """GET /api/v2/info/board/{boardId}?size=&page=&stage="""
    params = {"size": size, "page": page}
    if stage:
        params["stage"] = stage
    r = await _get(f"/api/v2/info/board/{board_id}", params=params)
    return _resp(r)


@app.get("/initiative/{initiative_id}/count", summary="Initiative ovoz soni")
async def get_initiative_count(initiative_id: str = Path(...)):
    """GET /api/v2/info/initiative/count/{id}"""
    r = await _get(
        f"/api/v2/info/initiative/count/{initiative_id}",
        extra_headers={"Referer": f"{BASE_URL}/boards-list/0/{initiative_id}"},
    )
    return _resp(r)


@app.get("/statistics/boards", summary="Barcha boardlar statistikasi")
async def get_board_statistics():
    """GET /api/v2/info/statistics/board"""
    r = await _get("/api/v2/info/statistics/board")
    return _resp(r)


@app.get("/statistics/board/{board_id}/budget", summary="Board byudjet summasi")
async def get_board_budget_sum(
    board_id: int = Path(...),
    region_id: Optional[str] = Query(None),
    district_id: Optional[str] = Query(None),
):
    """GET /api/v2/info/statistics/board-budget-sum/{boardId}"""
    params = {}
    if region_id is not None:
        params["regionId"] = region_id
    if district_id is not None:
        params["districtId"] = district_id
    r = await _get(f"/api/v2/info/statistics/board-budget-sum/{board_id}", params=params)
    return _resp(r)


@app.get("/votes/{initiative_token}", summary="Initiative ovoz berganlar ro'yxati")
async def get_initiative_votes(
    initiative_token: str = Path(...),
    page: int = Query(0, ge=0),
    size: int = Query(12, ge=1, le=100),
):
    """GET /api/v2/info/votes/{initiative_token}?page=&size="""
    r = await _get(
        f"/api/v2/info/votes/{initiative_token}",
        params={"page": page, "size": size},
    )
    return _resp(r)


# ═══════════════════════════════════════════════
# Captcha endpoint — auto-solve
# ═══════════════════════════════════════════════

@app.get(
    "/captcha/solve",
    summary="Captcha olish va avtomatik yechish",
    response_description="captchaKey, captchaText, captchaResult (hisoblangan javob)",
)
async def captcha_solve():
    """
    openbudget.uz dan yangi captcha oladi va OCR orqali avtomatik yechadi.

    Qaytaradi:
    - **captchaKey**: keyingi so'rovlarda ishlatiladi
    - **captchaText**: OCR tomonidan aniqlangan matn, masalan "3+4"
    - **captchaResult**: hisoblangan javob, masalan 7
    - **image**: captcha rasmi base64 formatda (tekshirish uchun)
    """
    r = await _get(
        "/api/v2/vote/captcha-2",
        extra_headers={
            "access-captcha": ACCESS_CAPTCHA,
            "x-xsrf-token": "",
        },
    )

    if r.status_code != 200:
        return JSONResponse(
            status_code=r.status_code,
            content={"ok": False, "error": "Captcha olishda xato", "detail": r.text},
        )

    data = r.json()
    image_b64: str = data.get("image", "")
    captcha_key: str = data.get("captchaKey", "")

    if not image_b64:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": "Captcha rasmi bo'sh qaytdi"},
        )

    captcha_text, captcha_result = _solve_captcha_b64(image_b64)

    return {
        "ok": True,
        "captchaKey": captcha_key,
        "captchaText": captcha_text,
        "captchaResult": captcha_result,
        "image": image_b64,
    }


# ═══════════════════════════════════════════════
# Ovoz berish oqimi
# ═══════════════════════════════════════════════

@app.post(
    "/vote/start",
    summary="Ovoz berishni boshlash (captcha avtomatik hal qilinadi)",
)
async def vote_start(payload: VoteStartPayload):
    """
    Ovoz berish oqimini boshlaydi:
    1. Captcha olinadi
    2. OCR bilan avtomatik yechiladi
    3. POST /api/v2/vote/check ga yuboriladi
    4. OTP kalit qaytariladi

    **phoneNumber** formati: "998XXXXXXXXX" (plus belgisisiz)
    """
    # 1. Captcha olish
    cap_r = await _get(
        "/api/v2/vote/captcha-2",
        extra_headers={
            "access-captcha": ACCESS_CAPTCHA,
            "Referer": f"{BASE_URL}/boards-list/{payload.boardId}/{payload.initiativeId}",
            "x-xsrf-token": "",
        },
    )

    if cap_r.status_code != 200:
        return JSONResponse(
            status_code=cap_r.status_code,
            content={"ok": False, "step": "captcha_fetch", "error": cap_r.text},
        )

    cap_data = cap_r.json()
    image_b64 = cap_data.get("image", "")
    captcha_key = cap_data.get("captchaKey", "")

    if not image_b64:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "step": "captcha_fetch", "error": "Rasm bo'sh"},
        )

    # 2. OCR bilan yechish
    captcha_text, captcha_result = _solve_captcha_b64(image_b64)

    if captcha_result is None:
        return JSONResponse(
            status_code=422,
            content={
                "ok": False,
                "step": "captcha_solve",
                "error": f"OCR captchani yecha olmadi: '{captcha_text}'",
                "captchaText": captcha_text,
            },
        )

    # 3. Vote check
    check_body = {
        "captchaKey": captcha_key,
        "captchaResult": captcha_result,
        "phoneNumber": payload.phoneNumber,
        "boardId": payload.boardId,
        "initiativeId": payload.initiativeId,
    }

    check_r = await _post(
        f"/api/v2/vote/dfghgtrgffg/check",
        json_body=check_body,
        extra_headers={
            "Referer": f"{BASE_URL}/boards-list/{payload.boardId}/{payload.initiativeId}",
            "x-xsrf-token": "",
            "cookie": "",
        },
    )

    try:
        check_data = check_r.json()
    except Exception:
        check_data = {"raw": check_r.text}

    return JSONResponse(
        status_code=check_r.status_code,
        content={
            "ok": check_r.status_code == 200,
            "step": "vote_check",
            "captchaText": captcha_text,
            "captchaResult": captcha_result,
            "captchaKey": captcha_key,
            "upstream": check_data,
        },
    )


@app.post(
    "/vote/{otp_key}/verify",
    summary="OTP kod bilan ovozni tasdiqlash",
)
async def vote_verify(
    otp_key: str = Path(..., description="vote/start dan olingan otpKey"),
    payload: VoteVerifyPayload = ...,
):
    """
    SMS orqali kelgan OTP kodni yuboradi va ovozni tasdiqlaydi.

    **otpKey** — `/vote/start` javobidagi `otpKey` qiymati
    """
    body = {
        "otpKey": payload.otpKey,
        "otpCode": payload.otpCode,
        "initiativeId": payload.initiativeId,
        "subinitiativesId": [],
        "secretKey": "3bb560304ad0df6cce226060a6d17c725a2d559012bbae515372a52a90657a55",
    }

    r = await _post(
        f"/api/v2/vote/iutyjmjyfgnmg/verify",
        json_body=body,
        extra_headers={
            "device-type": "ANDROID",
            "Referer": f"{BASE_URL}/boards-list/0/{payload.initiativeId}",
            "x-xsrf-token": "",
            "cookie": "",
        },
    )

    return _resp(r)


@app.post(
    "/vote/initiative-token",
    summary="Initiative token olish (captcha avtomatik hal qilinadi)",
)
async def get_initiative_token(payload: InitiativeTokenPayload):
    """
    Initiative uchun token oladi. Captcha avtomatik yechiladi.
    POST /api/v2/info/get-initiative-token
    """
    # Captcha olish va yechish
    cap_r = await _get(
        "/api/v2/vote/captcha-2",
        extra_headers={
            "access-captcha": ACCESS_CAPTCHA,
            "Referer": f"{BASE_URL}/boards/initiatives/initiative/{payload.initiativeId}",
            "x-xsrf-token": "",
        },
    )

    if cap_r.status_code != 200:
        return JSONResponse(
            status_code=cap_r.status_code,
            content={"ok": False, "step": "captcha_fetch", "error": cap_r.text},
        )

    cap_data = cap_r.json()
    image_b64 = cap_data.get("image", "")
    captcha_key = cap_data.get("captchaKey", "")

    captcha_text, captcha_result = _solve_captcha_b64(image_b64)

    if captcha_result is None:
        return JSONResponse(
            status_code=422,
            content={
                "ok": False,
                "step": "captcha_solve",
                "error": f"OCR captchani yecha olmadi: '{captcha_text}'",
            },
        )

    body = {
        "initiativeId": payload.initiativeId,
        "captchaKey": captcha_key,
        "captchaResult": str(captcha_result),
    }

    r = await _post(
        "/api/v2/info/get-initiative-token",
        json_body=body,
        extra_headers={
            "access-captcha": ACCESS_CAPTCHA,
            "Referer": f"{BASE_URL}/boards/initiatives/initiative/{payload.initiativeId}",
            "x-xsrf-token": "",
            "cookie": "",
        },
    )

    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}

    return JSONResponse(
        status_code=r.status_code,
        content={
            "ok": r.status_code == 200,
            "captchaText": captcha_text,
            "captchaResult": captcha_result,
            "captchaKey": captcha_key,
            "upstream": data,
        },
    )


# ─────────────────────────────────────────────
# Ishga tushirish
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8521)
