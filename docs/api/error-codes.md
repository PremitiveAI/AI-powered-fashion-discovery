# Error Codes

The `Code` field is the **only reliable success/failure signal** — almost every response carries HTTP
200. `Code: 0` means success; anything else is a failure.

There is no central error-code registry in the source. This table was assembled by tracing every
`error_response(...)`, `throw_error_response(...)` and `JSONResponse(...)` call in the backend.

## Complete table

| Code | HTTP | Meaning | Raised by |
| ---: | ---: | ------- | --------- |
| `0` | 200 | Success | `success_response()` |
| `1` | 400 | Request validation failed — **first Pydantic error only** | `RequestValidationError` handler, [`main.py`](../../backend/app/main.py) |
| `400` | 200 | Bad request / invalid input | assorted controllers |
| `401` | 200 | Unauthorized (non-middleware paths) | assorted |
| `404` | 200 | Resource not found | assorted |
| `422` | 422 | Validation error with a `details` array | [`exception_handler.py`](../../backend/app/middlewares/exception_handler.py) |
| `500` | 200 | Handled internal failure | assorted |
| `505` | 200 | Used in at least one controller path | assorted |
| `4000` | 200 | Business-rule failure — record missing, no files uploaded, referenced IDs do not exist | product / master / store controllers |
| `4001` | 200 | Related-record failure | assorted |
| `4002` | 200 | **Unsafe image detected** | `ProductController.search` |
| `5000` | 500 | Unhandled server error | `GlobalExceptionMiddleware` |
| `5001` | 200 | `PK-apiToken` header missing | [`auth_middleware.py`](../../backend/app/middlewares/auth_middleware.py) |
| `5002` | 200 | `PK-apiToken` incorrect | `auth_middleware.py` |
| `5003` | — | Invalid or expired session | Defined in `UserSessionVerifyMiddleware` — **unreachable** |
| `5004` | — | Session token mismatch | Defined in disabled session code — **unreachable** |
| `5010` | — | Account blocked by admin | Defined in disabled session code — **unreachable** |
| `5011` | — | Device blocked by admin | Defined in disabled session code — **unreachable** |
| `4010` | 401 | Invalid or expired token | `jwt_error_handler` — **no code path raises it** |

Codes `5003`, `5004`, `5010`, `5011` and `4010` belong to the session/JWT machinery, which is never
registered. They can never be returned. See
[../security/authentication-and-authorization.md](../security/authentication-and-authorization.md).

## Numbering is not systematic

Be aware before writing client logic:

- **HTTP status codes are reused as application codes** — `400`, `401`, `404`, `422`, `500`, `505` appear
  as `Code` values alongside the `4xxx`/`5xxx` scheme.
- **`404` and `4000` both mean "not found"** in different modules.
- **`500` appears both as a `Code` on an HTTP-200 response** (handled failure) **and as a real HTTP
  status** (unhandled exception, where `Code` is `5000`).
- **`5000` is the default argument of `error_response()`**, so a call that omits `code=` is
  indistinguishable from a crash.

Match on the pair `(Code, message)` when precision matters, and treat any non-zero `Code` as failure.

## Worked examples

**Missing token**

```json
{ "Success": null, "Code": 5001, "Error": { "message": "API Token required" } }
```

**Wrong token** — the most common setup mistake, and easy to miss because it is HTTP 200:

```json
{ "Success": null, "Code": 5002, "Error": { "message": "Invalid API Token" } }
```

**Unsafe image on search**

```json
{ "Success": null, "Code": 4002,
  "Error": { "message": "Invalid image: nudity or unsafe content detected" } }
```

**Referenced master records do not exist** — `POST /product/save` validates each ID list:

```json
{ "Success": null, "Code": 4000, "Error": { "message": "Brand IDs [7, 9] do not exist" } }
```

Variants: `"Category with id 3 does not exist"`, `"Color IDs [...] do not exist"`,
`"Image IDs [...] do not exist"`.

**Pydantic rejection** (HTTP 400, only the first error):

```json
{ "Success": null, "Code": 1, "Error": { "message": "Field required" } }
```

**Unhandled exception** (HTTP 500):

```json
{ "Success": null, "Code": 5000, "Error": { "message": "…" } }
```

## Endpoints that do not use codes at all

`POST /photo/try-on` returns bare dictionaries:

```json
{ "status": "success", "image_url": "http://127.0.0.1:8000/try_on/<uuid>.png" }
{ "status": "Fail", "message": "No human face detected" }
{ "status": "Fail", "message": "Invalid image: nudity or unsafe content detected" }
```

and raises `HTTPException` for input errors, producing `{"detail": "…"}` with a real 400/404 status.
Clients must special-case this endpoint. See [photo-try-on.md](photo-try-on.md).

## Recommended client handling

```ts
type Envelope<T> = {
  Success: { message?: string; data?: T } | null;
  Code: number;
  Error: { message: string } | null;
};

async function call<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);

  // Real transport/server failures still surface here (400, 422, 500)
  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  const body: Envelope<T> = await res.json();

  // The important check — everything else arrives as HTTP 200
  if (body.Code !== 0) throw new Error(body.Error?.message ?? `Code ${body.Code}`);

  return body.Success?.data as T;   // may be undefined — Success can be {}
}
```
