# Local Development

## Startup order

```
PostgreSQL (5432)
      ↓  must be reachable before the backend connects
Backend  (8000)   — Qdrant starts embedded, in-process
      ↓
Frontend (3002)
```

There is **no Redis, no Celery, no broker and no worker** to start.

| Component | Technology | Port | Command | Depends on |
| --------- | ---------- | ---: | ------- | ---------- |
| Database | PostgreSQL | 5432 | external service | — |
| Backend | FastAPI / uvicorn | 8000 | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` | PostgreSQL, `GOOGLE_API_KEY`, `vision-key.json` |
| Qdrant | embedded | — | starts with the backend | Backend |
| Frontend | Next.js | **3002** | `npm run dev` | Backend |

## Two terminals

```bash
# Terminal 1
cd backend
.\venv\Scripts\activate          # source venv/bin/activate elsewhere
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# Terminal 2
cd frontend
npm run dev
```

Open <http://localhost:3002>.

## Health and verification

### Backend

| Check | How | Expected |
| ----- | --- | -------- |
| Process up | `curl http://localhost:8000/` | `{"message":"FastAPI MVC Running"}` |
| Qdrant initialised | startup console | `✅ Qdrant client initialized with storage at: qdrant_storage` |
| Tables created | startup console | `✅ All tables created successfully!` |
| Token accepted | `curl -H "PK-apiToken: <token>" -H "Content-Type: application/json" -d '{"limit":10,"offset":0}' http://localhost:8000/master/category/list` | `Code: 0` |
| Token rejected | same call without the header | `Code: 5001` |
| Swagger | <http://localhost:8000/docs> | router tags listed |

> `GET /` does **not** touch the database, so it returns 200 even when PostgreSQL is down. There is no
> readiness endpoint. The database connection is only exercised on the first real query — and
> `test_connection()` is guarded by `if __name__ == "__main__":`, so it does not run under uvicorn.

### Frontend

| Check | How | Expected |
| ----- | --- | -------- |
| Server up | <http://localhost:3002> | redirects to `/home` |
| Backend connectivity | open `/product-list` | catalogue loads |
| BFF in use | Network tab | calls go to `:3002/api/...`, never `:8000` |
| Token stays server-side | inspect request headers | no `PK-apiToken` visible |
| Login | — | **Not applicable — there is no login.** See [../security/authentication-and-authorization.md](../security/authentication-and-authorization.md) |

## First end-to-end run

Image search needs a populated catalogue **and** a populated vector index. From a clean database:

1. **Masters** — create at least one category, brand and colour
   (`POST /master/category/save`, `/master/brand/save`, `/master/color/save`).
   Name the category after a garment *type* (e.g. `T-Shirt`), because product matching filters on the
   detected `type`. See [../ai/vector-search.md](../ai/vector-search.md).
2. **Gallery** — upload product images via `/uploade` or `POST /gallery/upload`; note the returned IDs.
3. **Products** — `POST /product/save` referencing those category, brand, colour and image IDs. This is
   what writes the Qdrant vector.
4. **Search** — upload a photo on `/uploade`. Expect detected items each with a `product_list`.
5. **Try-on** — pick a garment and a user photo on `/try-on`.

If step 4 returns items with empty `product_list`, the index is almost certainly empty — see below.

## ⚠️ Re-index after every backend restart

`init_collection("products")` runs at module import and calls `recreate_collection`, which **drops and
recreates** the Qdrant collection. Every backend start — including every `--reload` cycle — empties the
product index.

The startup line `Total points: 0` confirms it.

**Until this is fixed** ([AUDIT.md](../../AUDIT.md) issue 3), after each restart either re-save every
product (`POST /product/save`), or comment out the module-scope `init_collection("products")` call in
[`app/vector/vector_db.py`](../../backend/app/vector/vector_db.py) once the collection exists.

This is the single most disruptive behaviour for day-to-day development — `--reload` on a code save is
enough to wipe the index mid-session.

## Working on the backend

`--reload` watches for changes. Module-level side effects re-run on **every** reload:

- Qdrant collection recreated (index wiped)
- SentenceTransformer model loaded (~420 MB)
- YOLOv8s weights loaded
- Gemini clients constructed, Cloud Vision credentials read
- Fernet key derived

Reloads are therefore slow and destructive. Consider running without `--reload` when working on the
frontend.

### Where to look when something breaks

| Source | Contents |
| ------ | -------- |
| **Backend console** | `print()` diagnostics from the AI pipeline — `query_text`, matched product names and scores, `Total points`, JSON parse errors and raw Gemini responses |
| `logs/errors.log` | Unhandled exceptions with tracebacks |
| `logs/requests.log` | Request/response detail |
| `logs/slow_queries.log` | Statements over 300 ms, with bound parameters |

Loggers set `propagate = False`, so **file logs never appear in the console and console output never
reaches the files.** Check both. Most AI-pipeline diagnostics are console-only.

## Working on the frontend

- Changes to `.env.local` require a **full restart** — Next.js reads env vars at boot.
- Route handlers under `app/api/` are server code; edits apply on the next request.
- The dev port is **3002**, not the Next.js default.

## Port conflicts

| Symptom | Fix |
| ------- | --- |
| Address already in use on 8000 | `uvicorn app.main:app --reload --port 8001`, then update `NEXT_PUBLIC_API_URL` **and** `BASE_URL` |
| Port 3002 taken | `npm run dev -- -p 3003` |

If you move the backend port, both `NEXT_PUBLIC_API_URL` (frontend) and `BASE_URL` (backend) must move
with it — `BASE_URL` is embedded in returned image URLs.

## Resetting local state

```sql
TRUNCATE tbl_search_history, tbl_products, tbl_admin_gallery,
         tbl_master_categories, tbl_master_sub_categories, tbl_master_colors,
         tbl_master_brands, tbl_master_patterns, tbl_master_subtypes,
         tbl_stores RESTART IDENTITY CASCADE;
```

```bash
rm -rf backend/storage/* backend/uploads/* backend/try_on/*
rm -rf backend/qdrant_storage        # recreated on next start
```

Do these together — truncating the database while leaving images behind orphans hundreds of files, and
clearing images while keeping rows leaves broken URLs.

## Things that will surprise you

| Behaviour | Why |
| --------- | --- |
| Errors arrive with HTTP 200 | By design — check the `Code` field |
| The product index empties on restart | `recreate_collection` at import |
| `/models/*` works without a token | Middleware prefix collision — [AUDIT.md](../../AUDIT.md) issue 1 |
| Search returns items but no products | AND-only vector filters; an unknown brand or colour yields zero matches |
| Earrings and rings never get a bounding box | The small-item landmark gate always fails — see [../ai/image-analysis-pipeline.md](../ai/image-analysis-pipeline.md) |
| Phase 3 pages are blank | No `cosmetics/*` backend exists |
| Adding a model column has no effect | No migrations; `create_all` only creates missing tables |
| The startup log prints your DB password | `connection.py:32` |
