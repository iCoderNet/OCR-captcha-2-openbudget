# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install dependencies:**
```bash
pip install -r requirments.txt
```

**Train the CNN model** (requires `dataset/` directory populated with labeled character images):
```bash
python train.py
```

**Run inference on a single image via CLI:**
```bash
python predict.py --image path/to/captcha.png
```

**Run the standalone OCR API** (port 8520):
```bash
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8520
```

**Run the OpenBudget proxy API** (port 8521):
```bash
python openbudget_api.py
# or
uvicorn openbudget_api:app --host 0.0.0.0 --port 8521
```

**Extract characters from raw captcha images into the dataset:**
```bash
python extra/extract_characters_from_circles.py
```

## Architecture

The project is a two-layer system: a CNN-based OCR engine for math captchas, and a proxy API that wraps openbudget.uz to automate voting flows.

### OCR Pipeline (core)

1. **`segment.py`** — Takes a raw captcha image (PIL or ndarray), applies Otsu thresholding + contour detection, filters contours by aspect ratio (~1:1, width 15–100px), and returns a list of 28×28 RGB character crops sorted left-to-right.

2. **`predict.py`** — Loads `symbol_cnn_model.pt` at import time. Accepts a file path, bytes, or file-like object. Calls `segment_characters()`, runs each segment through the CNN, maps class indices back to display characters (`+`, `-`, `*`, `0`–`9`), and returns the full expression string (e.g. `"3+4"`).

3. **`train.py`** — Trains the `SymbolCNN` (2 conv layers → 2 FC layers, input 28×28 grayscale). Dataset is an `ImageFolder` at `dataset/` where each subdirectory name is the class label (digits `0`–`9` plus `plus`, `minus`, `mul`). Saves checkpoint as `symbol_cnn_model.pt` containing `model_state_dict` and `class_to_idx`.

### API Layer

- **`main.py`** — Minimal FastAPI app (port 8520). Single `POST /ocr` endpoint: accepts `{"image": "<base64>"}`, decodes, runs `predict_full_captcha()`, evaluates the expression with `eval()`, returns `{"ok": true, "text": "3+4", "math_solution": 7}`.

- **`openbudget_api.py`** — Full proxy API (port 8521) that mirrors openbudget.uz endpoints and automates the voting flow. On captcha-requiring endpoints it calls `predict_full_captcha()` directly (not via the OCR API). Uses a hardcoded `access-captcha` token and Android `User-Agent` from the mobile app. Key endpoints: `GET /captcha/solve`, `POST /vote/start`, `POST /vote/{otp_key}/verify`, `POST /vote/initiative-token`.

### Model checkpoint format

`symbol_cnn_model.pt` is a dict with keys `model_state_dict` and `class_to_idx`. Both `predict.py` and `train.py` must use the same `SymbolCNN` architecture — they are kept in sync manually.

---

## Gateway (pay-per-use auth layer)

`gateway/` is a separate FastAPI service (port 8000) that sits in front of `ocr_api` and `proxy_api`, adding authentication, per-route billing, and client/admin dashboards.

### Running with Docker

```bash
cp gateway/.env.example gateway/.env   # edit secrets
docker compose up --build
```

- Gateway API: `http://localhost:8000`
- Frontend dashboard: `http://localhost:3000`
- Seed (admin user + default prices): runs automatically as a one-shot container

### Local development (without Docker)

```bash
# Start PostgreSQL + Redis separately, then:
cd gateway
pip install -r requirements.txt
python scripts/seed.py          # creates admin + route prices
uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173 (proxies /api → localhost:8000)
```

### Gateway architecture

- **`app/middleware/auth_billing.py`** — Starlette middleware that intercepts all non-public routes: extracts `X-API-Key` header, validates against DB (Redis-cached, 60s TTL), checks balance, forwards request, then schedules async deduction via `asyncio.create_task`.
- **`app/core/billing.py`** — `deduct_and_log()` uses `SELECT FOR UPDATE` to prevent race conditions. Also holds the in-process route price cache.
- **`app/routers/proxy.py`** — Registers all 15 proxy routes; each forwards via `reverse_proxy.proxy_request()`.
- **`app/proxy/reverse_proxy.py`** — Shared `httpx.AsyncClient` pools: routes `/ocr` → `ocr_api:8520`, everything else → `proxy_api:8521`.
- **`app/routers/auth.py`** — `POST /auth/register`, `POST /auth/login` (JWT), `GET /auth/me`.
- **`app/routers/client/`** — `keys`, `balance`, `logs` (JWT-protected, client-scoped).
- **`app/routers/admin/`** — `users`, `prices`, `logs` (JWT + admin role).

### API key security

Raw keys are generated with `secrets.token_urlsafe(32)`, prefixed with `ob_`. Only the SHA-256 hash is stored in DB (`api_keys.key_hash`). The raw key is returned **once** at creation time — it cannot be recovered.

### Default route prices (seeded)

| Route | Cost |
|-------|------|
| GET simple endpoints | $0.0001 |
| GET statistics/initiatives | $0.0002 |
| POST /ocr | $0.0020 |
| GET /captcha/solve | $0.0050 |
| POST /vote/start | $0.0100 |
| POST /vote/*/verify | $0.0050 |

Admin can change prices at `/admin/prices`.

---

### Dataset structure

```
dataset/
  0/    ← images of digit "0"
  1/    ← images of digit "1"
  ...
  9/
  plus/
  minus/
  mul/
```

Raw unannotated captchas go in `dataset/.mixed/`; run `extra/extract_characters_from_circles.py` to segment them into `dataset/.characters/` for manual labeling.
