# Try-On API

Router: `photo_router` (`/photo`), defined in
[`app/routes/photo_route.py`](../../backend/app/routes/photo_route.py). One endpoint.

Requires `PK-apiToken`.

> **This endpoint does not follow house conventions.** It returns bare dictionaries rather than the
> `{Success, Code, Error}` envelope, and raises `HTTPException` with real 400/404 statuses. Client code
> written against the rest of the API will not parse it correctly.

## POST `/photo/try-on`

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Notes |
| ----- | ---- | :------: | ----- |
| `user_photo` | file | ✅ | Must have a `content_type` starting `image/` |
| `cloth_url` | form string | ✅ | Full URL containing `/storage/`, or a path relative to `storage/` |

### `cloth_url` resolution

```python
def extract_cloth_id(value: str) -> str:
    if value.startswith("http"):
        if "/storage/" not in value:
            raise HTTPException(400, "Invalid cloth image URL")
        return value.split("/storage/", 1)[-1]
    return value
```

Both of these are accepted:

```
http://127.0.0.1:8000/storage/1/product_search_20260115_074544.jpg
1/product_search_20260115_074544.jpg
```

### Processing

```
1. extract_cloth_id(cloth_url)
2. reject non-image user_photo                     → 400
3. cloth_path = normpath(join(CLOTH_STORAGE_DIR, cloth_url))
4. reject if not cloth_path.startswith(CLOTH_STORAGE_DIR)   → 400   ← traversal guard
5. reject if file missing                          → 404
6. read cloth bytes; read user bytes; reject empty → 400
7. gemini_has_face(user_bytes)                     → {"status":"Fail"}
8. gemini_is_safe_tryon(user_bytes)                → {"status":"Fail"}
9. generate_final_image_bytes(...)   Gemini 2.5 Flash Image
10. save try_on/{uuid4}.png
```

`CLOTH_STORAGE_DIR` and `TRY_ON_DIR` derive from `os.getcwd()`, so the backend **must** run from
`backend/`.

## Responses

**Success — HTTP 200:**

```json
{ "status": "success",
  "image_url": "http://127.0.0.1:8000/try_on/588c77cb-2165-4b5c-9dd7-be249e2242b0.png" }
```

`image_url` is built as `f"{env('BASE_URL')}try_on/{output_name}"` — `BASE_URL` **must end with a slash**.

**Safety rejection — also HTTP 200:**

```json
{ "status": "Fail", "message": "No human face detected" }
{ "status": "Fail", "message": "Invalid image: nudity or unsafe content detected" }
```

Clients must check `status`, not the HTTP status code.

**Input errors — real HTTP statuses, `detail` shape:**

| Status | `detail` |
| -----: | -------- |
| 400 | `user_photo must be an image` |
| 400 | `Invalid cloth image URL` |
| 400 | `Invalid cloth path` |
| 400 | `Invalid user image` |
| 404 | `Cloth image not found: <absolute server path>` |

> The 404 message embeds the **absolute filesystem path**, disclosing server layout to the caller.

**Generation failure — HTTP 500:** `RuntimeError("Gemini did not return an image")` when the model
responds without an inline image part (typically a safety refusal or quota problem), surfaced by the
global exception middleware as `Code 5000`.

## Model and prompt

`gemini-2.5-flash-image` with `response_modalities=["IMAGE"]`. The prompt instructs the model to replace
**only** the selected garment while preserving face, body shape, pose, skin tone, hair, lighting and
background, and restricts the garment to **shirt, t-shirt, pants, jeans or sunglasses**.

**Nothing validates that restriction server-side** — any image under `storage/` can be passed, and
behaviour with other garment types is undefined.

Full prompt text and model detail: [../ai/virtual-try-on.md](../ai/virtual-try-on.md).

## Output storage and exposure

Generated PNGs accumulate in `backend/try_on/`, served by
`app.mount("/try_on", StaticFiles(directory="try_on"))`.

> `/try_on` is **exempt from token verification** in the auth middleware. Anyone who can reach the
> backend and knows a filename can retrieve any generated image — including composites of a user's face.
> UUID4 filenames are the only protection. Nothing prunes the directory.
> [AUDIT.md](../../AUDIT.md) issue 9.

## Performance

Three sequential Gemini calls per request — face check, safety check, then image generation. Generation
is slow; there is **no timeout, no retry and no progress streaming**, so the HTTP connection stays open
for the full duration.

## Frontend usage

| BFF handler | Page |
| ----------- | ---- |
| `POST /api/try-on` | `/try-on` |

The page passes a garment image URL obtained from the gallery or from an image-search result.

## Related

- [../features/virtual-try-on.md](../features/virtual-try-on.md) — user-facing feature
- [../ai/virtual-try-on.md](../ai/virtual-try-on.md) — model, prompt, safety gates
- [../integrations/google-gemini.md](../integrations/google-gemini.md) — cost and failure modes
