# Environment Variables

Complete inventory, established by cross-referencing every `env(...)` call in the backend and every
`process.env` reference in the frontend against the files that declare them.

Neither env file is committed — `.gitignore` excludes `.env`, `.env.*` and `*.env` — and no
`.env.example` exists. Both must be created by hand.

**No secret values appear in this document.**

---

## Backend — `backend/.env`

### Required — read by the code

| Variable | Purpose | Read by | Safe example |
| -------- | ------- | ------- | ------------ |
| `DB_HOST` | PostgreSQL host | [`connection.py`](../../backend/app/database/connection.py) | `localhost` |
| `DB_PORT` | PostgreSQL port | `connection.py` | `5432` |
| `DB_NAME` | Database name | `connection.py` | `fashion_discovery` |
| `DB_USERNAME` | Database user | `connection.py` | `postgres` |
| `DB_PASSWORD` | Database password — URL-quoted before use | `connection.py` | `<secret>` |
| `API_TOKEN` | Shared token compared against `PK-apiToken` | [`auth_middleware.py`](../../backend/app/middlewares/auth_middleware.py), `swagger_headers.py` | `<secret>` |
| `TOKEN_SECRET` | SHA-256 seed for the Fernet key | [`crypto.py`](../../backend/app/utils/crypto.py) | `<secret>` |
| `GOOGLE_API_KEY` | Gemini API key | `vision_service.py`, `photo_service.py`, `services/vector_db.py` | `<secret>` |
| `STORAGE_DIR` | Root for uploaded images and analysis JSON | `gallery_service.py`, `product_service.py` | `storage` |
| `VECTOR_DB_DIR` | Qdrant embedded storage path | [`vector/vector_db.py`](../../backend/app/vector/vector_db.py) | `qdrant_storage` |
| `BASE_URL` | Public base URL prefixed to returned image URLs — **must end with `/`** | `decision_engine.py`, `photo_route.py`, `admin_gallery_model.py` | `http://127.0.0.1:8000/` |

Three of these fail hard when absent, all at **import time**:

- **`GOOGLE_API_KEY`** — `photo_service` raises `RuntimeError("GOOGLE_API_KEY not found")`;
  `services/vector_db.py` raises `AttributeError` on `None.strip()`.
- **`TOKEN_SECRET`** — `crypto.py` derives the Fernet key at import.
- **`DB_PASSWORD`** — `urllib.parse.quote_plus(None)` raises `TypeError`.

### Optional — read, with defaults

| Variable | Default | Purpose | Read by |
| -------- | ------- | ------- | ------- |
| `GOOGLE_AI_MODEL` | `gemini-2.0-flash` | Gemini model id | LLM services |
| `GOOGLE_APPLICATION_CREDENTIALS` | `vision-key.json` | Path to the Cloud Vision service-account key | `vision_service.py` |
| `DEFAULT_COUNTRY` | `IN` | Fallback for the `PK-country` header | `auth_middleware.py` |
| `DEFAULT_TZ` | `Asia/Kolkata` | Fallback for the `PK-timezone` header | `auth_middleware.py` |

**None of these four appear in the repository's `.env`** — the defaults always apply unless you add them.
`GOOGLE_APPLICATION_CREDENTIALS` in particular is worth setting explicitly if you keep the key outside
`backend/`; see [google-cloud-credentials.md](google-cloud-credentials.md).

### Read by code, but not defined anywhere

| Variable | Read by | Status |
| -------- | ------- | ------ |
| `DB_USER` | [`services/user_db.py`](../../backend/app/services/user_db.py) — MariaDB layer | The project defines `DB_USERNAME`, not `DB_USER`. Latent: nothing imports that module. [AUDIT.md](../../AUDIT.md) issue 17 |

### Present in `.env` but never read

Confirmed by exhaustive search — no `env("…")` call references any of these:

| Variable | Value in `.env` | Status |
| -------- | --------------- | ------ |
| `API_VERSION` | `1.0.0` | Unused. **Purpose not verified from the current implementation.** |
| `ISPRODUCTION` | `false` | Unused — there is no environment switch in the code |
| `API_PORT` | `5004` | **Unused and misleading.** The port comes only from the uvicorn command line; `BASE_URL` and `backend/readme` both assume **8000** |
| `TIMEZONE` | `Asia/Kolkata` | Unused — models hard-code an IST `timedelta` |
| `DATE_FORMAT`, `DB_DATE_FORMAT`, `DOB_DATE_FORMAT`, `DB_DOB_DATE_FORMAT` | date patterns | Unused — models hard-code `"%d-%b-%Y %H:%M:%S"` |
| `ENCRYPT_SECRET` | — | Unused. `crypto.py` uses `TOKEN_SECRET` |
| `CONNECT_TIMEOUT` | `10` | Unused — not passed to `create_engine` |
| `SSLMODE` | `prefer` | Unused — no `connect_args` configured |

These are inherited configuration. They are harmless, but changing them has no effect.

### Non-variable requirement

`backend/vision-key.json` is **not** an environment variable but is mandatory. It is now covered by
`.gitignore`. See [google-cloud-credentials.md](google-cloud-credentials.md).

### Minimal working `backend/.env`

```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fashion_discovery
DB_USERNAME=postgres
DB_PASSWORD=<secret>

API_TOKEN=<secret>
TOKEN_SECRET=<secret>
GOOGLE_API_KEY=<secret>
GOOGLE_AI_MODEL=gemini-2.0-flash

STORAGE_DIR=storage
VECTOR_DB_DIR=qdrant_storage
BASE_URL=http://127.0.0.1:8000/
```

---

## Frontend — `frontend/.env.local`

### Required

| Variable | Purpose | Read by | Ships to browser? |
| -------- | ------- | ------- | :---------------: |
| `NEXT_PUBLIC_API_URL` | Backend base URL — **must end with `/`** | [`utils/api.ts`](../../frontend/app/utils/api.ts) | yes (harmless) |
| `API_TOKEN` | Sent as `PK-apiToken`; must equal the backend value | `utils/api.ts` | **no** |
| `NEXT_PUBLIC_OLA_MAPS_API_KEY` | Ola Maps nearby search + reverse geocoding | `api/nearby-stores/route.ts`, `add-store/page.tsx` | **yes** |
| `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` | Google Maps JS SDK | `uploade/page.tsx` | **yes** |

**On the trailing slash.** Most of the 37 route handlers concatenate directly —
`` fetch(`${API_URL}product/list`) `` — so omitting it yields `http://127.0.0.1:8000product/list`. A few
normalise with `.replace(/\/$/, "")`.

**On `API_TOKEN`.** It deliberately has no `NEXT_PUBLIC_` prefix and is imported only by server-side
route handlers, so Next.js excludes it from the client bundle. Adding the prefix would expose the shared
token to every visitor.

**On the Maps keys.** Both are `NEXT_PUBLIC_` and therefore visible in the browser — unavoidable for the
Google Maps JS SDK. Restrict them by HTTP referrer in the Google Cloud and Ola Maps consoles.
Note that `NEXT_PUBLIC_OLA_MAPS_API_KEY` is used inside a **server-side** handler
(`api/nearby-stores/route.ts`) where a non-public variable would have been sufficient —
[AUDIT.md](../../AUDIT.md) security item S8.

### Declared but never consumed

Exported by `utils/api.ts`, referenced by no other file:

| Variable | Status |
| -------- | ------ |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` | **Purpose not verified from the current implementation** — no OAuth flow exists |
| `SESSION_SECRET` | Defaults to `"dev-secret"`. No session handling exists |
| `ISSUER_URL`, `CLIENT_ID` | Purpose not verified from the current implementation |
| `COOKIE_SECRET` | Read by `utils/crypto.ts`, which is imported by nothing |

### Listed in `frontend/README.md` but read by nothing

`OLA_MAPS_API_KEY` and `GOOGLE_MAPS_API_KEY` (the non-prefixed variants). Only the `NEXT_PUBLIC_` forms
are used. Do not provision these.

### Minimal working `frontend/.env.local`

```ini
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/
API_TOKEN=<same value as backend API_TOKEN>
NEXT_PUBLIC_OLA_MAPS_API_KEY=<secret>
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=<secret>
```

---

## Cross-application consistency

| Backend | Frontend | Must match |
| ------- | -------- | ---------- |
| `API_TOKEN` | `API_TOKEN` | **Yes** — a mismatch makes every request fail with `Code 5002` |
| uvicorn `--port` | host:port in `NEXT_PUBLIC_API_URL` | **Yes** |
| `BASE_URL` | — | Must point at the reachable backend, since it is embedded in returned image URLs |

A mismatched token is the most common setup failure and is easy to misread, because the backend returns
it with **HTTP 200**. See [../troubleshooting/common-issues.md](../troubleshooting/common-issues.md).
