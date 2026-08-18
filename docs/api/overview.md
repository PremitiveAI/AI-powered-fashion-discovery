# API Overview

Conventions that apply to every endpoint. Read this before the individual references.

**Base URL:** `http://127.0.0.1:8000/` in local development.

> Swagger at `/docs` lists paths but declares no response models, summaries or descriptions —
> `FastAPI()` is constructed without metadata. These documents are the authoritative reference.

---

## Authentication

Every endpoint requires:

```
PK-apiToken: <value of API_TOKEN from backend/.env>
```

This is a **single shared application token**, not a user credential. There are no users, roles,
sessions or per-record authorization. See
[../security/authentication-and-authorization.md](../security/authentication-and-authorization.md).

### ⚠️ Exempt paths

The middleware passes these through **before** checking the token:

| Path prefix | Intent | Reality |
| ----------- | ------ | ------- |
| `/storage`, `/uploads`, `/try_on`, `/debug` | static file mounts | Uploaded and generated images are public |
| **`/models`** | the `/models` static mount | **Also matches the `/models` router** — all 10 Phase 2 endpoints are unauthenticated |
| `/`, `/docs`, `/redoc`, `/openapi.json` | root and docs | as intended |

The `/models` collision is [AUDIT.md](../../AUDIT.md) issue 1.

### Headers

| Header | Required | Default | Effect |
| ------ | -------- | ------- | ------ |
| `PK-apiToken` | **Yes** | — | `5001` if absent, `5002` if wrong |
| `PK-country` | No | `IN` | Sets `request.state.country`; `dialing_code` becomes `1` for `CA`, else `91` |
| `PK-timezone` | No | `Asia/Kolkata` | Sets `request.state.timezone` |
| `PK-role`, `PK-deviceid`, `PK-sessionToken` | No | — | Declared in Swagger, **never read for any decision** |

The Next.js BFF sends `PK-apiToken` on every call.

---

## Response envelope

```json
{ "Success": { "message": "…", "data": { } }, "Code": 0,    "Error": null }
{ "Success": null,                            "Code": 4000, "Error": { "message": "…" } }
```

### Errors are returned with HTTP 200

This is the most important convention in the API. `error_response` in
[`app/utils/response.py`](../../backend/app/utils/response.py) returns `status_code=200`.

```js
// ❌ Wrong — this branch is almost never taken
if (!res.ok) handleError();

// ✅ Correct
const json = await res.json();
if (json.Code !== 0) handleError(json.Error.message);
```

### Exceptions to the envelope

| Status | Source | Shape |
| -----: | ------ | ----- |
| 400 | `RequestValidationError` handler in `main.py` | Envelope, `Code: 1`, **first error message only** |
| 422 | `GlobalExceptionMiddleware` | Envelope with a `details` array |
| 500 | `GlobalExceptionMiddleware` | Envelope, `Code: 5000` |
| 400 / 404 | **`POST /photo/try-on`** | Raw `HTTPException` → `{"detail": "…"}` |
| 200 | `POST /photo/try-on` safety gates | `{"status": "Fail", "message": "…"}` — **not the envelope** |

`/photo/try-on` is the one endpoint that does not follow house conventions at all — it returns bare
dicts. See [photo-try-on.md](photo-try-on.md).

### `Success` may be an empty object

`success_response` omits falsy fields, so `"Success": {}` is possible. Never assume `Success.data`
exists.

---

## Endpoint groups

| Group | Prefix | Count | Auth | Reference |
| ----- | ------ | ----: | ---- | --------- |
| Products | `/product` | 7 | token | [products-and-gallery.md](products-and-gallery.md) |
| Gallery | `/gallery` | 2 | token | [products-and-gallery.md](products-and-gallery.md) |
| Masters | `/master` | 17 | token | [masters.md](masters.md) |
| Stores | `/store` | 4 | token | [stores.md](stores.md) |
| Try-on | `/photo` | 1 | token | [photo-try-on.md](photo-try-on.md) |
| Phase 2 models | `/models` | 10 | **none** | [models-phase2.md](models-phase2.md) |
| Phase 2 analysis | `/model` | 3 | token | [models-phase2.md](models-phase2.md) |
| Root | `/` | 1 | none | returns `{"message": "FastAPI MVC Running"}` |

**45 live endpoints + `GET /`.**

Routers that exist but are **not registered**: `profile_routes` (`/user` — register, upload-photo,
send-otp, verify-otp), `user_routes` (`/user` CRUD), `admin_routes` (`/admin_user` — and it imports two
schema modules that do not exist). The `login_routes` routers **are** registered but contain zero routes
— every one is commented out.

---

## List endpoints

Most list endpoints accept a common payload (`UserListReq` / `productListReq` / `StoreListRequest`).
Every field is optional:

```json
{ "search": "", "filter": "", "startDate": null, "endDate": null,
  "sort": "createdAt", "order": "DESC", "limit": 10, "offset": 0 }
```

| Field | Behaviour |
| ----- | --------- |
| `search` | Case-insensitive `ILIKE %value%` on the module's name column |
| `sort` / `order` | Resolved via `getattr`; an unknown column silently falls back |
| `limit` / `offset` | SQL `LIMIT`/`OFFSET` |

Responses report totals as `totalRecords` (products, stores) or `total` (masters) — the naming is not
consistent across modules.

---

## Content types

| Situation | Content-Type |
| --------- | ------------ |
| Most requests | `application/json` |
| `POST /product/search` | `multipart/form-data`, field `file` |
| `POST /gallery/upload` | `multipart/form-data`, field `files` (repeatable) |
| `POST /photo/try-on` | `multipart/form-data`, `user_photo` + form field `cloth_url` |
| All responses | `application/json` |

---

## Timestamps

Stored in UTC, returned as IST-formatted strings via model properties:

```python
self.createdAt.astimezone(IST).strftime("%d-%b-%Y %H:%M:%S")   # "18-Aug-2026 07:05:52"
```

`IST` is a hard-coded `timezone(timedelta(hours=5, minutes=30))`. The `TIMEZONE` and `DATE_FORMAT`
environment variables are **not** consulted, and responses carry no timezone marker.

> `admin_model.py` defines `IST = timezone(timedelta())` — i.e. **UTC**, not IST. Admin timestamps are
> therefore formatted differently from every other model.

---

## Image URLs

Endpoints that return images build absolute URLs from `BASE_URL`:

```python
return base_url + self.imagePath.lstrip("/")
```

`BASE_URL` **must end with a slash** or the URLs are malformed. It is also embedded in `debug_url` from
the analysis pipeline and `image_url` from try-on.

---

## No CORS, no rate limiting, no versioning

The backend registers no CORS middleware — the browser only calls same-origin Next.js handlers. There is
no rate limiter and no `/v1` prefix (the unused `API_VERSION` variable notwithstanding).
