# Code Audit — Confirmed Issues

Every item was verified by reading the source; each cites a file and, where useful, a line. Nothing here
is speculative.

**Scope of verification.** All 95 backend Python files were inventoried; routes, models, middleware, the
AI pipeline, the vector layer, configuration and the complete 37-handler frontend BFF map were read
directly. The application was **not executed**, and the live PostgreSQL schema was **not inspected** —
no dump or migration history exists. Runtime items are verified by code reading, not reproduction.

> **The repository was under active development during this audit.** `backend/app/main.py` changed
> mid-review (Phase 2 routers were registered). Items 7, 8, 10 and 12 describe a moving target and should
> be re-checked before acting on them.

**Total: 24 confirmed issues — 22 open, 2 resolved.**

| Category | Count |
| -------- | ----: |
| [Security](#security) | 4 |
| [Data loss and integrity](#data-loss-and-integrity) | 4 |
| [Setup and dependencies](#setup-and-dependencies) | 2 |
| [API contract](#api-contract) | 4 |
| [Dead and unreachable code](#dead-and-unreachable-code) | 3 |
| [Operations](#operations) | 4 |
| [Documentation](#documentation) | 3 |

---

## Security

### 1. All `/models/*` endpoints bypass authentication — **Critical**

- **Evidence:** [`app/middlewares/auth_middleware.py:31`](backend/app/middlewares/auth_middleware.py)
  skips token verification for any path beginning `/models`:
  ```python
  if request.url.path.startswith("/models"):
      return await call_next(request)
  ```
  The intent is to let the `/models` **static mount** ([`app/main.py:66`](backend/app/main.py)) serve
  files. But [`app/routes/models_routes.py:14`](backend/app/routes/models_routes.py) declares
  `prefix="/models"` — the same prefix. The check runs before any routing decision, so it matches both.
- **Impact:** All 10 Phase 2 API endpoints — `user-photo`, `last-user-photo`, `upload-gallery`,
  `gallery-list`, `gallery-delete`, `category_create`, `category-list`, `save-models`, `user-try-on`,
  `models-list` — are callable **with no `PK-apiToken` at all**. This includes endpoints that accept
  uploads and write to the database.
- **Recommendation:** Give the static mount a distinct path (e.g. `/model-assets`) and remove the
  `/models` skip, or replace the prefix skip with an exact static-path match.

### 2. Google service-account private key was not ignored — ✅ **RESOLVED**

- **Evidence:** `backend/vision-key.json` (`"type": "service_account"`) was present and
  `git check-ignore` returned no match, so it would have been committed on the next `git add -A`.
- **Status:** **Resolved.** [`.gitignore`](.gitignore) now covers `vision-key.json`, `**/vision-key.json`,
  `service-account*.json`, `*-service-account.json`, `gcp-credentials*.json`, `credentials.json`,
  `*.pem`, `*.key` and `*.p12`. Verified with `git check-ignore -v`, and confirmed the file **never
  entered git history**, so no history rewrite is required.
- **Remaining action for you:** the key existed unprotected on disk. If it was ever shared, copied or
  backed up, rotate it in Google Cloud. Generation instructions:
  [docs/setup/google-cloud-credentials.md](docs/setup/google-cloud-credentials.md).

### 9. Uploaded photos and generated images are served without authentication — **High**

- **Evidence:** [`app/main.py:59-66`](backend/app/main.py) mounts `/try_on`, `/storage`, `/uploads` and
  `/models`; [`auth_middleware.py:19-32`](backend/app/middlewares/auth_middleware.py) exempts `/storage`,
  `/debug`, `/try_on`, `/uploads` and `/models` from token checks.
- **Impact:** User-submitted photographs (`storage/1/*.jpg`), generated try-on images (`try_on/*.png`)
  and debug crops are downloadable by anyone who can reach the backend, with no credential. Paths are
  guessable (`/storage/{admin_id}/{filename}`).
- **Recommendation:** Serve user media through an authenticated handler, or block these paths at the
  reverse proxy and never expose port 8000 publicly.

### 24. All errors return HTTP 200 — **Medium**

- **Evidence:** [`app/utils/response.py`](backend/app/utils/response.py) — `success_response`,
  `error_response` and `throw_error_response` all use `status_code=200`.
- **Impact:** Monitoring, load balancers and generic retry logic cannot distinguish success from
  failure; clients must parse `Code`. The only non-200 responses come from the
  `RequestValidationError` handler (400) and unhandled exceptions.
- **Recommendation:** Map error codes to real HTTP statuses while keeping the envelope shape.

---

## Data loss and integrity

### 3. Product vectors are wiped on every backend start — **Critical**

- **Evidence:** [`app/vector/vector_db.py:20-32`](backend/app/vector/vector_db.py):
  ```python
  def init_collection(collection_name="products", vector_size=768):
      client.recreate_collection(...)

  init_collection("products")     # executed at module import
  ```
  `recreate_collection` **deletes** an existing collection and creates an empty one, and the call is at
  module scope — it runs on every import, i.e. every application start and every `--reload` cycle.
- **Impact:** The entire product index is destroyed on restart. Image search returns nothing until every
  product is re-saved. This is silent — the subsequent `client.count(...)` simply prints `0`.
- **Recommendation:** Replace with a create-if-absent check (`collection_exists` / catch-and-create), and
  move it out of module scope into an explicit startup or admin action.

### 13. Product foreign keys are stored as comma-separated strings — **Medium**

- **Evidence:** [`app/models/products_model.py`](backend/app/models/products_model.py) —
  `pattern_id`, `subtype_id`, `category_id`, `subcategory_id`, `brand_id`, `color_id` and `images` are
  all `String(255)`. `ProductController.save` writes them via `list_to_comma_string(...)`.
- **Impact:** No referential integrity, no index usability, and **silent truncation at 255 characters** —
  a product with many brands, colours or images loses the overflow. Deleting a master record leaves
  dangling IDs.
- **Recommendation:** Normalise into join tables, or at minimum widen to `Text` and validate length.

### 14. `search_result` column is too small for what is written to it — **Medium**

- **Evidence:** [`app/models/search_history_model.py`](backend/app/models/search_history_model.py) —
  `search_result = Column(String(2048))`. `ProductService.save_history` stores the enriched analysis,
  which contains every detected item plus up to three matched products each (id, hsn_code,
  product_code, name, mrp, price, gender, category, brands, colors).
- **Impact:** Realistic payloads exceed 2,048 characters; PostgreSQL rejects the insert with a
  `StringDataRightTruncation` error rather than truncating, failing the history write.
- **Recommendation:** Change to `Text` or `JSONB`.

### 20. Vector deletion is commented out on product delete — **Medium**

- **Evidence:** [`app/services/product_service.py:219`](backend/app/services/product_service.py) —
  `# print(delete_vector("products", id))`.
- **Impact:** Deleting a product soft-deletes the row but leaves its vector in Qdrant, so image search
  continues to recommend deleted products.
- **Recommendation:** Call `delete_vector` in the delete path.

---

## Setup and dependencies

### 4. `requirements.txt` is UTF-16 encoded — **High**

- **Evidence:** `file` reports *"Unicode text, UTF-16, little-endian, with CRLF line terminators"*;
  the first bytes are `ff fe`.
- **Impact:** `pip install -r requirements.txt` — the command in `backend/readme` — cannot parse the
  file. Setup fails at the first step.
- **Recommendation:** Re-save as UTF-8 without BOM. Workaround in
  [docs/setup/backend-setup.md](docs/setup/backend-setup.md).

### 5. Eight imported packages are undeclared, including the wrong Gemini SDK — **High**

- **Evidence:** import scan across `app/` versus `requirements.txt`:

  | Missing package | Imported as | Used by |
  | --------------- | ----------- | ------- |
  | `google-genai` | `from google import genai` | `vision_service.py`, `photo_service.py` |
  | `langchain-google-genai` | `langchain_google_genai` | `services/vector_db.py` |
  | `langchain-chroma` | `langchain_chroma` | `services/vector_db.py` |
  | `langchain-core` | `langchain_core` | `services/vector_db.py` |
  | `pymupdf` | `fitz` | `utils/kyc_document_parser.py` |
  | `python-docx` | `docx` | `utils/kyc_document_parser.py` |
  | `pymysql` | `pymysql` | `services/user_db.py` |
  | `rapidfuzz` | `rapidfuzz` | product/master services |

  Note the SDK conflict: the code uses the **new** `google-genai` SDK, while `requirements.txt` pins the
  **old** `google-generativeai`. Installing only what is declared leaves the imports unsatisfiable.
- **Impact:** `ModuleNotFoundError` on startup after a clean install.
- **Recommendation:** Add all eight with pinned versions; drop `google-generativeai` if unused.

---

## API contract

### 7. Phase 2 frontend and backend are out of sync — **High**

- **Evidence:** comparing `frontend/app/api/phase2/*/route.ts` targets with
  [`app/routes/models_routes.py`](backend/app/routes/models_routes.py):

  | Frontend calls — backend missing (4) | Backend exposes — frontend unused (5) |
  | --- | --- |
  | `models/get-categories` | `models/category_create` |
  | `models/save-categories` | `models/upload-gallery` |
  | `models/model-detail` | `models/gallery-list` |
  | `models/get-body-measurement-by-gender` | `models/gallery-delete` |
  | | `models/save-models` |

  Five endpoints do line up: `category-list`, `last-user-photo`, `models-list`, `user-photo`,
  `user-try-on`.
- **Impact:** Four Phase 2 screens cannot load their data.
- **Status:** Expected — Phase 2 is under active development. Recorded so the gap is explicit.
  See [docs/features/phase2-models.md](docs/features/phase2-models.md).

### 8. Phase 3 has no backend — **High**

- **Evidence:** eight handlers under `frontend/app/api/phase3/` target `cosmetics/*`. No router with a
  `/cosmetics` prefix exists — [`app/main.py`](backend/app/main.py) registers only `/photo`, `/user`,
  `/master`, `/gallery`, `/store`, `/product`, `/models` and `/model`.
- **Impact:** Three Phase 3 pages (`home`, `beauty-profile`, `look-detail`) cannot function.
- **Status:** Documented as frontend-only. See
  [docs/features/phase3-cosmetics.md](docs/features/phase3-cosmetics.md).

### 10. Two master endpoints the frontend calls do not exist — **Medium**

- **Evidence:** `frontend/app/api/master/pattern/route.ts` calls `master/pattern/list`;
  `frontend/app/api/master/sub-type/route.ts` calls `master/subtype/list`.
  [`master_routes.py`](backend/app/routes/master_routes.py) exposes neither — it has
  `subcategory/list`, and no pattern route at all, despite
  [`pattern_model.py`](backend/app/models/pattern_model.py) and
  [`subtype_model.py`](backend/app/models/subtype_model.py) both existing.
- **Impact:** Pattern and sub-type dropdowns cannot populate.
- **Recommendation:** Add the two routes, or repoint the frontend at `subcategory/list`.

### 12. Static mount collides with a router prefix — **Medium**

- **Evidence:** [`app/main.py:66`](backend/app/main.py) `app.mount("/models", StaticFiles(...))` versus
  `models_router` at `prefix="/models"`.
- **Impact:** Confusing routing surface, and it is the direct cause of issue 1.
- **Recommendation:** Rename the mount path.

---

## Dead and unreachable code

> Per project decision these subsystems are **not** given feature documentation. They are recorded here
> only so their presence is explained.

### 15. `user_db.py` — 599 lines of MariaDB code for an unrelated database — **Medium**

- **Evidence:** [`app/services/user_db.py`](backend/app/services/user_db.py) — docstring reads
  *"User storage using MariaDB (MySQL-compatible)"*; `DB_CONFIG` defaults to
  `database: "insurance_db"`, port `3306`. `grep -rn "user_db"` finds **no importer**.
- **Impact:** Pulls in an undeclared `pymysql` dependency and implies a second datastore that does not
  exist. It also reads `DB_USER`, a variable the project does not define (see issue 17).

### 16. Three further subsystems are unreachable — **Medium**

- **Evidence:** no registered route reaches
  [`kyc_document_service.py`](backend/app/services/kyc_document_service.py) (492 lines) with its separate
  Chroma `pdf_chunks` store, [`employee_service.py`](backend/app/services/employee_service.py)
  (396 lines), or [`auth_service.py`](backend/app/services/auth_service.py) (816 lines).
- **Impact:** ~1,700 lines of maintained-looking dead code; the auth stack in particular makes the
  project appear to have authentication that it does not.

### 11. `admin_routes.py` imports modules that do not exist — **Medium**

- **Evidence:** [`app/routes/admin_routes.py`](backend/app/routes/admin_routes.py) imports
  `app.schemas.signup_schema` and `app.schemas.login_schema`. Neither file is present in
  [`app/schemas/`](backend/app/schemas/).
- **Impact:** The router is commented out in `main.py`; uncommenting it raises `ImportError` at startup.

---

## Operations

### 17. `user_db.py` reads an undefined environment variable — **Medium**

- **Evidence:** `env("DB_USER", "root")` in `user_db.py`; `backend/.env` defines `DB_USERNAME`, not
  `DB_USER`.
- **Impact:** Latent only because nothing imports the module.

### 18. POSIX-only paths are hard-coded and mounted — **Medium**

- **Evidence:** [`decision_engine.py:13-14`](backend/app/services/decision_engine.py) sets
  `TMP_DIR = "/tmp/person_crops"` and `DEBUG_DIR = "/tmp/debug_boxes"`;
  [`main.py:61-62`](backend/app/main.py) mounts both.
- **Impact:** On Windows these resolve to the current drive root (`C:\tmp\...`). `os.makedirs` at import
  creates them, so startup succeeds, but debug artefacts land outside the project tree. **Exact
  resolution was not verified by execution.**
- **Recommendation:** Use a project-relative directory under `STORAGE_DIR`.

### 19. No database migrations — **Medium**

- **Evidence:** [`connection.py:85-88`](backend/app/database/connection.py) —
  `Base.metadata.create_all(bind=engine)`. No Alembic directory, `alembic.ini` or `versions/`.
- **Impact:** `create_all` creates missing tables but **never alters existing ones**. Any column added to
  a model after its table exists is silently absent, and queries fail at runtime.
- **Recommendation:** Introduce Alembic and baseline the current schema.

### 22. Debug crops accumulate indefinitely — **Low**

- **Evidence:** `draw_debug` writes a new `uuid4().jpg` per analysed image; `analyze_person_mode` writes
  `person_{idx}.jpg`. Nothing prunes either directory.
- **Impact:** Unbounded disk growth on a busy instance.

### 21. Column name typo in a live table — **Low**

- **Evidence:** [`app/models/tbl_models.py`](backend/app/models/tbl_models.py) — `modle_url`.
- **Impact:** Cosmetic, but renaming later requires a migration that does not currently exist (issue 19).

---

## Documentation

### 6. `backend/readme` names three technologies that are not in the codebase — **High**

- **Evidence:** [`backend/readme:5,13,21-22`](backend/readme) claims *"CLIP embeddings"*, *"Background
  Tasks: Celery with Redis for async job processing"*. Exhaustive search across `app/` and
  `requirements.txt` finds **no CLIP, no Celery, no Redis**. Embeddings are produced by
  SentenceTransformer `all-mpnet-base-v2` — a **text** model, not CLIP image embeddings — and there is no
  background processing of any kind.
- **Impact:** The first document a backend developer reads misdescribes the architecture.
- **Status:** Left unmodified by project decision. The accurate stack is documented in
  [docs/ai/image-analysis-pipeline.md](docs/ai/image-analysis-pipeline.md) and the root
  [README.md](README.md). Its install section **is** accurate and is the source for
  [docs/setup/backend-setup.md](docs/setup/backend-setup.md).

### 23. Root README was absent; frontend README has an invalid command — **Low**

- **Evidence:** no root `README.md` existed before this documentation effort.
  [`frontend/README.md`](frontend/README.md) instructs `npm -i`, which is not a valid npm command
  (`npm i`), and lists Maps keys without noting that `NEXT_PUBLIC_API_URL` must carry a trailing slash.
- **Status:** Root README **resolved** by this effort. The frontend README is unchanged.

---

## Verified as non-issues

- **No CORS middleware** is correct — the browser only calls same-origin Next.js handlers.
- **Try-on path traversal is defended.** [`photo_route.py`](backend/app/routes/photo_route.py) applies
  `os.path.normpath` and rejects any resolved path that escapes `CLOTH_STORAGE_DIR`.
- **Try-on applies safety gates** — `gemini_has_face` and `gemini_is_safe_tryon` run before generation,
  and `/product/search` also refuses unsafe images.
- **SQL injection** is not a concern in the live paths; all queries go through SQLAlchemy ORM
  constructs.
- **`API_TOKEN` is not exposed to the browser** — it is read only inside server-side route handlers and
  deliberately lacks a `NEXT_PUBLIC_` prefix.
