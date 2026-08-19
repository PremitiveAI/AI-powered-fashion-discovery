# Feature — Virtual Try-On

Generates a photorealistic image of the user wearing a selected garment.

**Status:** ✅ Complete.

## Business purpose

Removes the largest source of hesitation in online fashion — not knowing how something will look on
you. The user supplies one photograph and picks a garment; the system returns a composite.

## User flow

1. Go to **`/try-on`**.
2. Upload a photograph of yourself.
3. Choose a garment image (from the gallery or an image-search result).
4. Receive a generated image.

## Frontend flow

```
/try-on page
  → POST /api/try-on          multipart: user_photo + cloth_url
  → POST /photo/try-on
  → { status: "success", image_url }   →  render the returned PNG
```

The handler must also cope with `{ status: "Fail", message }`, which arrives with **HTTP 200**.

## Backend flow

```
POST /photo/try-on
  ↓ extract_cloth_id(cloth_url)          strips the /storage/ prefix from a full URL
  ↓ reject if user_photo.content_type does not start with "image/"     → 400
  ↓ cloth_path = normpath(join(CLOTH_STORAGE_DIR, cloth_url))
  ↓ reject if not cloth_path.startswith(CLOTH_STORAGE_DIR)             → 400
  ↓ reject if file missing                                             → 404
  ↓ read cloth bytes; read user bytes; reject empty                    → 400
  ↓ gemini_has_face(user_bytes)          → {"status":"Fail","message":"No human face detected"}
  ↓ gemini_is_safe_tryon(user_bytes)     → {"status":"Fail","message":"…nudity or unsafe…"}
  ↓ generate_final_image_bytes(...)      Gemini 2.5 Flash Image
  ↓ save try_on/{uuid4}.png
  ↓ {"status":"success","image_url": f"{BASE_URL}try_on/{name}"}
```

Model, prompt and safety-gate detail: [../ai/virtual-try-on.md](../ai/virtual-try-on.md).

## API details

`POST /photo/try-on` — full reference:
[../api/photo-try-on.md](../api/photo-try-on.md).

## Request

**Content-Type:** `multipart/form-data`

| Field | Type | Notes |
| ----- | ---- | ----- |
| `user_photo` | file | `content_type` must start `image/` |
| `cloth_url` | form string | Full URL containing `/storage/`, or a path relative to `storage/` |

## Response

```json
{ "status": "success",
  "image_url": "http://127.0.0.1:8000/try_on/588c77cb-2165-4b5c-9dd7-be249e2242b0.png" }
```

> **This endpoint does not use the `{Success, Code, Error}` envelope.** It returns bare dictionaries and
> raises `HTTPException` for input errors. Client code written against the rest of the API will not
> parse it correctly.

## Validation

| Rule | Failure |
| ---- | ------- |
| `user_photo` must be an image | HTTP 400 |
| A full `cloth_url` must contain `/storage/` | HTTP 400 |
| Resolved path must stay inside `CLOTH_STORAGE_DIR` | HTTP 400 |
| Garment file must exist | HTTP 404 |
| User image must be non-empty | HTTP 400 |
| A human face must be detected | HTTP 200, `status: "Fail"` |
| Content must pass the NSFW gate | HTTP 200, `status: "Fail"` |

**Path traversal is correctly defended** — `os.path.normpath` collapses `..` before the prefix check.
This is one of the better-implemented parts of the codebase.

## Business rules

The generation prompt restricts the garment to **shirt, t-shirt, pants, jeans or sunglasses**, and
instructs the model to preserve face, body shape, pose, skin tone, hair, lighting and background
exactly.

**Nothing enforces that restriction server-side.** Any image under `storage/` can be passed as
`cloth_url`; behaviour with a dress, shoes or a bag is undefined.

## Database interaction

**None.** Try-on writes a PNG to `try_on/` and records nothing. There is no history, no association with
a product or a user, and no way to list past generations.

## Authentication

`PK-apiToken` only. No per-user isolation — generated images are not attributed to anyone.

## Error handling

| Situation | Result |
| --------- | ------ |
| Input errors | `HTTPException` with `{"detail": "…"}` and a real 400/404 |
| Safety gate failure | HTTP 200 with `status: "Fail"` |
| Model returns no image part | `RuntimeError` → HTTP 500 |
| Gemini network/quota failure | HTTP 500 |

The 404 message embeds the **absolute server path** (`f"Cloth image not found: {cloth_path}"`),
disclosing filesystem layout to the caller.

## Dependencies

`google-genai` (new SDK), `Pillow`, a Gemini API key, `BASE_URL`.

`photo_service` reads `GOOGLE_API_KEY` via `os.getenv` + `load_dotenv()` rather than the project's
`app.config.env` helper used everywhere else, and raises `RuntimeError` at import if it is missing.

## Known limitations

1. **Generated images are public.** `/try_on` is exempt from token verification, so any composite of a
   user's face is downloadable by anyone who knows the filename. UUID4 is the only protection.
   [AUDIT.md](../../AUDIT.md) issue 9.
2. **No garment-type validation** despite the prompt's restriction.
3. **Both images are declared `image/jpeg`** regardless of actual format; PNG and WebP files exist in
   `storage/`.
4. **No history** — nothing is persisted, so results cannot be retrieved later.
5. **Three sequential Gemini calls per request** (face, safety, generation) with **no timeout, no retry
   and no progress streaming** — the connection stays open for the full duration.
6. **Nothing prunes `try_on/`.**
7. `generate_final_image` — a second, older implementation in the same module — would raise if called;
   it passes paths where the helper expects `(bytes, mime)`. Nothing calls it.
