# Troubleshooting

Symptom → cause → fix, for failures supported by the repository. Nothing here is invented.

---

## Backend will not start

### `pip install -r requirements.txt` fails to parse the file

`requirements.txt` is UTF-16 with a BOM. Convert first:

```powershell
Get-Content requirements.txt | Set-Content -Encoding utf8 requirements.utf8.txt
pip install -r requirements.utf8.txt
```

```bash
iconv -f UTF-16 -t UTF-8 requirements.txt > requirements.utf8.txt
pip install -r requirements.utf8.txt
```

[AUDIT.md](../../AUDIT.md) issue 4.

### `ModuleNotFoundError: No module named 'google.genai'` (or `fitz`, `docx`, `pymysql`, `rapidfuzz`, `langchain_*`)

Eight packages are imported but undeclared. `google.genai` in particular is the **new** SDK, while
`requirements.txt` pins the old `google-generativeai`.

```bash
pip install google-genai langchain-google-genai langchain-chroma langchain-core \
            pymupdf python-docx pymysql rapidfuzz
```

[AUDIT.md](../../AUDIT.md) issue 5.

### `RuntimeError: GOOGLE_API_KEY not found`

`GOOGLE_API_KEY` is missing from `backend/.env`. `photo_service` reads it at **import time**, so the
backend cannot start — even if you never intend to use try-on.

### `AttributeError: 'NoneType' object has no attribute 'strip'`

Same cause, different module — `services/vector_db.py` does `env("GOOGLE_API_KEY").strip()` at import.

### `FileNotFoundError: vision-key.json`

The Cloud Vision service-account key is missing, misnamed, or uvicorn was started from the wrong
directory. Place it in `backend/` and start uvicorn from `backend/`. Generation steps:
[../setup/google-cloud-credentials.md](../setup/google-cloud-credentials.md).

### `ValueError: Service account info was not in the expected format`

The downloaded file is not a service-account key (e.g. an OAuth client ID) or is truncated. Re-download
a **service account** key of type **JSON**.

### `TypeError` from `quote_plus`

`DB_PASSWORD` is missing. `urllib.parse.quote_plus(None)` raises. Set it, even to an empty string in a
trust-auth setup.

### `RuntimeError: Directory 'storage' does not exist` (or `uploads`, `models`)

All static mounts use **relative** paths. Start uvicorn from `backend/`, and ensure `storage/`,
`uploads/` and `models/` exist. Only `try_on/` is created automatically.

### First start hangs for several minutes

Expected. `ultralytics` downloads `yolov8s.pt` (~22 MB) and `sentence-transformers` downloads
`all-mpnet-base-v2` (~420 MB) on first use. Both are cached afterwards.

### `[Errno 10048] address already in use` on port 8000

```bash
uvicorn app.main:app --reload --port 8001
```

Then update **both** `NEXT_PUBLIC_API_URL` (frontend) and `BASE_URL` (backend) — `BASE_URL` is embedded
in returned image URLs.

---

## Database

### `❌ Database connection failed`

Check `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`, and that PostgreSQL is running:

```bash
psql -h localhost -p 5432 -U postgres -d fashion_discovery -c "SELECT 1;"
```

> `CONNECT_TIMEOUT` and `SSLMODE` in `.env` are **not read**. To require SSL you must add
> `connect_args={"sslmode": "require"}` in `connection.py`.

### A column I added to a model does not exist in the database

There are no migrations. `create_all()` creates missing tables but **never alters existing ones**. Apply
the DDL manually, or drop the table and let it be recreated. [AUDIT.md](../../AUDIT.md) issue 19.

### `StringDataRightTruncation` when saving search history

`tbl_search_history.search_result` is `String(2048)`, smaller than the enriched payloads written to it.
Widen the column to `TEXT` or `JSONB`. [AUDIT.md](../../AUDIT.md) issue 14.

### Some product brands/colours/images silently disappear

`tbl_products` stores those ID lists as comma-separated `String(255)`. Long lists are truncated at 255
characters. [AUDIT.md](../../AUDIT.md) issue 13.

---

## Image search

### Search returns detected items, but every `product_list` is empty

**Cause 1 — the vector index is empty.** `init_collection("products")` runs at import and calls
`recreate_collection`, wiping the collection on **every** backend start, including every `--reload`
cycle. The startup line `Total points: 0` confirms it.

**Fix:** re-save every product (`POST /product/save`), or comment out the module-scope
`init_collection("products")` call in `app/vector/vector_db.py` once the collection exists.
[AUDIT.md](../../AUDIT.md) issue 3.

**Cause 2 — the filters are AND-only.** `filter_search_vector` applies `must` conditions on brand,
colour, gender and category. If Gemini reports a brand you do not stock, or a colour that is not a master
colour, the query returns **zero** results rather than approximate ones. There is no unfiltered fallback.

**Fix:** widen your master data, or relax the filter conditions.

**Cause 3 — category naming.** The category filter uses the detected `type` (e.g. `t-shirt`), not the
coarse `category` (`clothing`). Your master categories must be named for garment types.

See [../ai/vector-search.md](../ai/vector-search.md).

### Search returns nothing at all

Check the backend console — the pipeline prints `query_text` and matched product names for every item.
If no items were detected, Gemini may have returned unparseable output; `describe` prints both the parse
error and the raw response.

### `Code 4002 — Invalid image: nudity or unsafe content detected`

`gemini_is_safe_tryon` rejected the upload. The gate runs before any analysis.

### Earrings and rings never get a bounding box

Working as implemented. The small-item gate requires anatomical landmarks, `choose_best_bbox` is never
given any, and `small_item_valid` returns `False` when `landmarks is None`. The attributes still reach
product matching; only the box is dropped.
See [../ai/image-analysis-pipeline.md](../ai/image-analysis-pipeline.md).

### Only one person is analysed in a group photo

Working as implemented — `persons[:1]` after sorting by bounding-box area. Only the largest person is
processed.

---

## Virtual try-on

### `{"status": "Fail", "message": "No human face detected"}`

`gemini_has_face` rejected the user photo. Note this returns **HTTP 200** — check `status`, not the
status code.

### `404 Cloth image not found: <path>`

`cloth_url` did not resolve to a file under `backend/storage/`. Pass either a full URL containing
`/storage/` or a path relative to `storage/`.

### `400 Invalid cloth path`

The resolved path escaped `CLOTH_STORAGE_DIR`. This is the traversal guard working correctly.

### `RuntimeError: Gemini did not return an image`

The model responded without an inline image part — usually a safety refusal or a quota problem. Check
`logs/errors.log`.

### The generated image changed clothing I did not select

The prompt restricts input to shirt, t-shirt, pants, jeans or sunglasses, but **nothing validates this
server-side**. Behaviour with other garment types is undefined.

---

## Frontend ↔ backend

### Every page loads but all data is empty

**Cause 1 — missing trailing slash.** Most route handlers concatenate directly, so
`NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` produces `http://127.0.0.1:8000product/list`.
Set `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/`.

**Cause 2 — token mismatch.** The backend returns `Code 5002` with **HTTP 200**, so pages that only check
`res.ok` show an empty state. Verify:

```bash
curl -H "PK-apiToken: <token>" -H "Content-Type: application/json" \
     -d '{"limit":10,"offset":0}' http://localhost:8000/master/category/list
```

Restart the Next.js dev server after editing `.env.local` — env vars are read at boot.

### `Code 5001 — API Token required`

`API_TOKEN` is unset in `frontend/.env.local`, so `utils/api.ts` falls back to `""`.

### Pattern or sub-type dropdowns are always empty

The frontend calls `master/pattern/list` and `master/subtype/list`. **Neither backend route exists** —
the backend has `master/subcategory/list`, and no pattern route at all, despite both models existing.
[AUDIT.md](../../AUDIT.md) issue 10.

### Phase 3 (cosmetics) pages are blank

There is **no `cosmetics/*` backend**. Eight frontend handlers call a router that was never implemented.
See [../features/phase3-cosmetics.md](../features/phase3-cosmetics.md).

### Some Phase 2 screens fail to load data

Four endpoints the frontend calls do not exist yet: `models/get-categories`, `models/save-categories`,
`models/model-detail`, `models/get-body-measurement-by-gender`. Phase 2 is in development.
See [../features/phase2-models.md](../features/phase2-models.md).

### CORS errors

You are calling FastAPI directly from a browser on another origin. The backend registers no CORS
middleware by design. Route through the Next.js handlers, or call the backend server-side.

### The dev server is not on port 3000

`package.json` sets `next dev -p 3002`. Use <http://localhost:3002>.

---

## Diagnostics

| Source | Contents |
| ------ | -------- |
| **Backend console** | AI-pipeline `print()` output — `query_text`, matched products and scores, `Total points`, Gemini parse errors and raw responses |
| `backend/logs/errors.log` | Unhandled exceptions with tracebacks |
| `backend/logs/requests.log` | Request/response detail |
| `backend/logs/slow_queries.log` | Statements over 300 ms, **with bound parameters** |

Loggers set `propagate = False`, so **file logs never appear in the console and console output never
reaches the files.** Check both — most AI diagnostics are console-only.

> The startup banner prints the full database URL **including the password**, and `slow_queries.log`
> contains bound parameters. Treat both as sensitive.
