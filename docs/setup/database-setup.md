# Database Setup

PostgreSQL is the only relational datastore. Qdrant runs embedded and needs no setup of its own.

## Step 1 — Start PostgreSQL and create the database

```bash
createdb fashion_discovery
```

or

```sql
CREATE DATABASE fashion_discovery;
```

The name is arbitrary — it only has to match `DB_NAME` in `backend/.env`. **Do not create any tables**;
the application does that.

## Step 2 — Configure the connection

```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fashion_discovery
DB_USERNAME=postgres
DB_PASSWORD=<your-password>
```

The URL is assembled in [`app/database/connection.py`](../../backend/app/database/connection.py):

```python
password = urllib.parse.quote_plus(DB_PASSWORD)
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{DB_USERNAME}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
```

`quote_plus` URL-encodes the password, so `@`, `:`, `/` and `#` are handled correctly.

`CONNECT_TIMEOUT` and `SSLMODE` exist in `.env` but are **not read** — they are never passed to
`create_engine`, and no `connect_args` are configured. To require SSL you would add
`connect_args={"sslmode": "require"}` to the `create_engine` call.

> **`DB_USER` vs `DB_USERNAME`.** `app/services/user_db.py` reads `DB_USER`, which the project does not
> define. That module is a MariaDB layer that nothing imports, so the mismatch is latent — but do not be
> misled into adding a MySQL database. [AUDIT.md](../../AUDIT.md) issue 17.

## Step 3 — Let the application create the tables

On the first `uvicorn` start:

```python
@app.on_event("startup")
def startup_event():
    create_all_tables()
```

```python
def create_all_tables():
    auto_import_models()                 # pkgutil-walks app/models/
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")
```

`auto_import_models()` imports every module under `app/models/` dynamically, so all models register on
`Base` without an explicit import list — adding a new model file is enough.

## Step 4 — Verify

```sql
\c fashion_discovery
\dt
```

24 tables should exist:

| Group | Tables |
| ----- | ------ |
| Admin | `tbl_admin`, `tbl_admin_gallery` |
| Catalogue | `tbl_products` |
| Masters | `tbl_master_categories`, `tbl_master_sub_categories`, `tbl_master_colors`, `tbl_master_brands`, `tbl_master_product_types`, `tbl_master_patterns`, `tbl_master_subtypes` |
| Stores | `tbl_stores` |
| Search | `tbl_search_history` |
| Users (unused by any route) | `tbl_users`, `tbl_users_otps`, `tbl_users_sessions`, `tbl_otps`, `tbl_profiles`, `tbl_user_profiles` |
| Phase 2 | `tbl_models`, `tbl_models_type`, `tbl_models_try_on`, `tbl_category_models`, `tbl_models_gallery`, `tbl_model_analysis` |

Column-level detail: [../database/schema.md](../database/schema.md).

## Step 5 — Populate reference data

Image search cannot return products until the catalogue exists. There is **no seed script**, so create
data through the API or UI in this order:

```
1. Masters   POST /master/category/save, /master/brand/save, /master/color/save
2. Gallery   POST /gallery/upload                (products reference gallery image IDs)
3. Products  POST /product/save                  (also writes the Qdrant vector)
```

`POST /product/save` validates that every referenced category, brand, colour and image ID exists, and
returns `Code 4000` listing the missing ones.

## Migrations

**There is no migration tooling.** No Alembic directory, `alembic.ini` or `versions/`.

> `Base.metadata.create_all()` creates **tables that do not exist**. It never alters a table that does.
> If you add, rename, remove or retype a column on a model whose table is already present, the database
> is silently left unchanged and queries fail at runtime.

Until Alembic is introduced ([AUDIT.md](../../AUDIT.md) issue 19), apply schema changes by hand:

```sql
ALTER TABLE tbl_products ADD COLUMN my_new_column TEXT;
```

In local development the alternative is to drop the affected table and let `create_all` rebuild it.

Two known schema problems worth fixing while you are in there:

- `tbl_search_history.search_result` is `String(2048)`, smaller than the payloads written to it — inserts
  fail with `StringDataRightTruncation`. Change to `TEXT` or `JSONB`.
- `tbl_products` stores ID lists as comma-separated `String(255)`, which silently truncates.

[AUDIT.md](../../AUDIT.md) issues 13 and 14.

## Qdrant

No setup required. `QdrantClient(path=VECTOR_DB_DIR)` runs embedded, creating the directory on demand.

> **The `products` collection is dropped and recreated on every backend start** —
> `init_collection("products")` runs at module import and calls `recreate_collection`. Products must be
> re-saved after each restart before image search returns results.
> [AUDIT.md](../../AUDIT.md) issue 3.

## Backups

State is split three ways, and a database-only backup is incomplete:

| Location | Contents |
| -------- | -------- |
| PostgreSQL | Products, masters, stores, gallery rows, search history, Phase 2 records |
| `backend/qdrant_storage/` | Product embeddings (rebuildable from PostgreSQL by re-saving products) |
| `backend/storage/`, `uploads/`, `try_on/` | **Uploaded and generated images — not reproducible** |

Back up PostgreSQL and the image directories together.

## Connection pooling and slow queries

`create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)` — default pool sizing with pre-ping so stale
connections are recycled rather than surfacing as errors.

Two event listeners time every statement and log anything over **300 ms** to `logs/slow_queries.log`,
including bound parameters — so that file can contain sensitive values.
