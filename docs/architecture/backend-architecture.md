# Backend Architecture

FastAPI application in [`backend/app/`](../../backend/app/) — 95 Python files.

## Directory layout

```
backend/app/
├── main.py               FastAPI instance, middleware, routers, static mounts
├── config/env.py         dotenv loader + env() getter
├── database/connection.py engine, SessionLocal, Base, get_db, slow-query listener
├── docs/swagger_headers.py Header dependencies shown in Swagger
├── middlewares/          auth, exception, jwt_error, request_logger
├── routes/       (11)    router definitions
├── controllers/  (14)    request handling and response shaping
├── services/     (18)    business logic and AI orchestration
├── models/       (21)    SQLAlchemy models
├── schemas/       (9)    Pydantic request models
├── repositories/  (4)    data access — not used by any live flow
├── vector/               Qdrant client and search
├── core/          (4)    LLM prompts
├── utils/         (4)    crypto, logger, response, document parser
└── validations/          shared validators
```

## Entry point

[`app/main.py`](../../backend/app/main.py):

```python
app = FastAPI()

app.add_middleware(request_logger.RequestLoggingMiddleware)
app.add_middleware(auth_middleware.UserApiVerifyMiddleware)
exception_handler.register_exception_handlers(app)
jwt_error_handler.register_jwt_error_handler(app)

app.include_router(photo_router)       # /photo
app.include_router(public_router)      # /user  — login_routes, EMPTY
app.include_router(protected_router)   # /user  — login_routes, EMPTY
app.include_router(master_router)      # /master
app.include_router(gallery_router)     # /gallery
app.include_router(store_router)       # /store
app.include_router(product_route)      # /product
# app.include_router(user_router)      # profile_routes — DISABLED
app.include_router(models_router)      # /models
app.include_router(model_router)       # /model
app.include_router(router)             # /product/analyze

@app.on_event("startup")
def startup_event(): create_all_tables()
```

`FastAPI()` is constructed with **no title, version or description**, so `/docs` is untitled and carries
no response models.

### Static mounts

```python
os.makedirs("try_on", exist_ok=True)
app.mount("/try_on",  StaticFiles(directory="try_on"))
app.mount("/debug",   StaticFiles(directory="/tmp/debug_boxes"))
app.mount("/crops",   StaticFiles(directory="/tmp/person_crops"))
app.mount("/storage", StaticFiles(directory="storage"))
app.mount("/uploads", StaticFiles(directory="uploads"))
app.mount("/models",  StaticFiles(directory="models"))
```

All paths are **relative**, so the backend must be started from `backend/`. The `/tmp` directories are
created at import time by `decision_engine`, which runs before the mounts because it is imported
transitively through `product_routes`.

`app.mount("/models", ...)` collides with the `models_router` prefix — see
[AUDIT.md](../../AUDIT.md) issues 1 and 12.

## Router inventory

| Router | Prefix | Endpoints | Registered | Source |
| ------ | ------ | --------: | :--------: | ------ |
| `photo_router` | `/photo` | 1 | ✅ | `photo_route.py` |
| `public_router` / `protected_router` | `/user` | **0** | ✅ | `login_routes.py` — every route commented out |
| `master_router` | `/master` | 17 | ✅ | `master_routes.py` |
| `gallery_router` | `/gallery` | 2 | ✅ | `product_routes.py` |
| `store_router` | `/store` | 4 | ✅ | `store_routes.py` |
| `product_route` | `/product` | 7 | ✅ | `product_routes.py` |
| `router` | `/product` | 1 | ✅ | `routes.py` — `/analyze` |
| `models_router` | `/models` | 10 | ✅ | `models_routes.py` |
| `model_router` | `/model` | 3 | ✅ | `model_analysis_routes.py` |
| `user_router` | `/user` | 4 | ❌ | `profile_routes.py` — commented out at `main.py:44` |
| — | `/user` | 4 | ❌ | `user_routes.py` — never imported |
| `admin_router` | `/admin_user` | 2 | ❌ | `admin_routes.py` — commented out; **imports two schema modules that do not exist** |

**45 live endpoints + `GET /`.**

## Layering

The intended chain is `route → controller → service → model`. What is actually implemented:

| Module | Route | Controller | Service | Repository |
| ------ | :---: | :--------: | :-----: | :--------: |
| Products | ✅ | ✅ | ✅ | ✗ |
| Gallery | ✅ | ✅ | ✅ | ✗ |
| Masters | ✅ | ✅ | ✅ | ✗ |
| Stores | ✅ | ✅ (queries directly) | ✗ | ✗ |
| Try-on | ✅ | ✗ — route calls the service | ✅ | ✗ |
| Models (Phase 2) | ✅ | ✅ | ✅ | ✗ |

`app/repositories/` contains four modules (`auth`, `document`, `otp`, `user`) that **no live flow uses**.

Two endpoints bypass the chain: `/product/historylist` calls `ProductService` directly from the route,
and `/photo/try-on` calls `photo_service` directly.

## Middleware

Registered in `main.py` in the order logging → auth → exception handling. Starlette executes the
**last-added first**, so the effective order is exception handling wraps auth wraps logging.

### `UserApiVerifyMiddleware`

[`app/middlewares/auth_middleware.py`](../../backend/app/middlewares/auth_middleware.py) — the only
enforced access control:

```python
if request.url.path.startswith("/storage"): return await call_next(request)
if request.url.path.startswith("/debug"):   return await call_next(request)
if request.url.path.startswith("/try_on"):  return await call_next(request)
if request.url.path.startswith("/uploads"): return await call_next(request)
if request.url.path.startswith("/models"):  return await call_next(request)   # ← also matches the router
if request.url.path in ALLOWED_PATHS:       return await call_next(request)

api_token = request.headers.get("PK-apiToken")
if not api_token:                   return error_response("API Token required", code=5001)
if api_token != env('API_TOKEN'):   return error_response("Invalid API Token", code=5002)

request.state.country      = request.headers.get("PK-country",  env("DEFAULT_COUNTRY", "IN"))
request.state.timezone     = request.headers.get("PK-timezone", env("DEFAULT_TZ", "Asia/Kolkata"))
request.state.dialing_code = 1 if request.state.country == "CA" else 91
request.state.base_url     = str(request.base_url).rstrip("/")
```

`UserSessionVerifyMiddleware` also exists in this file but is never registered.

### Others

- `RequestLoggingMiddleware` — writes request/response detail to `logs/requests.log`.
- `GlobalExceptionMiddleware` — `RequestValidationError` → 422, anything else → 500, logged to
  `logs/errors.log`.
- `jwt_error_handler` — maps `jose.JWTError` to 401 / `Code 4010`. No live path raises it.

## Response envelope

[`app/utils/response.py`](../../backend/app/utils/response.py):

```python
success_response(message=None, data=None, code=0)   # HTTP 200
error_response(message="Error", code=5000)          # HTTP 200  ← note
throw_error_response(message, code=5000)            # raises HTTPException(status_code=200)
```

```json
{ "Success": { "message": "...", "data": {} }, "Code": 0,    "Error": null }
{ "Success": null,                             "Code": 4000, "Error": { "message": "..." } }
```

The only non-200 responses are the 400 from the `RequestValidationError` handler in `main.py`, the 422
and 500 from the exception middleware, the 401 from the JWT handler, and the raw `HTTPException`s raised
by `/photo/try-on`.

Full code list: [../api/error-codes.md](../api/error-codes.md).

## Database layer

[`app/database/connection.py`](../../backend/app/database/connection.py):

- URL built as `postgresql+psycopg2://…`, password URL-quoted with `quote_plus`.
- `create_engine(..., pool_pre_ping=True)`.
- `auto_import_models()` walks `app.models` with `pkgutil`, so every model registers on `Base` without an
  explicit import list — adding a model file is enough.
- `create_all_tables()` → `Base.metadata.create_all(bind=engine)`. Creates missing tables, **never
  alters existing ones**.
- Two event listeners time every statement and log anything over **300 ms** to `logs/slow_queries.log`,
  including bound parameters.
- `test_connection()` is guarded by `if __name__ == "__main__":`, so it does **not** run on import.

## Logging

[`app/utils/logger.py`](../../backend/app/utils/logger.py) returns named loggers writing to
`logs/{name}.log` with `propagate = False` — **file logs never reach the console, and `print()` output
never reaches the files.** Check both when debugging.

| Logger | File |
| ------ | ---- |
| `requests` | `logs/requests.log` |
| `errors` | `logs/errors.log` |
| `slow_queries` | `logs/slow_queries.log` |

The AI pipeline uses bare `print()` extensively (`query_text`, matched product names and scores, Qdrant
point counts, JS console bridge output), so the console is the primary diagnostic surface for search.

## Background processing

**Not found in implementation.** No Celery, Redis, broker, queue, scheduler or `BackgroundTasks`. The
only asynchrony is `loop.run_in_executor` wrapping the blocking Gemini call in `vision_service.describe`,
which keeps the event loop free during a network round trip.

The `backend/readme` claim of "Celery with Redis for async job processing" is unsupported —
[AUDIT.md](../../AUDIT.md) issue 6.
