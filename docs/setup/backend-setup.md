# Backend Setup

Every command is taken from [`backend/readme`](../../backend/readme) or derived from the source, and is
labelled with its origin. Where the repository's own command does not work as written, the documented
command is shown first and the workaround immediately after.

## Step 1 — Navigate to the backend

```bash
cd backend
```

## Step 2 — Check the Python version

```bash
python --version        # must be 3.10.x or 3.11.x  (backend/readme:26)
```

## Step 3 — Create and activate a virtual environment

```bash
python -m venv venv
```

```bash
.\venv\Scripts\activate       # Windows        (backend/readme:49)
source venv/bin/activate      # macOS / Linux  (backend/readme:55)
```

## Step 4 — Upgrade pip and install PyTorch

```bash
python -m pip install --upgrade pip
pip install torch==2.9.1 torchaudio==2.9.1 --index-url https://download.pytorch.org/whl/cpu
```

PyTorch is installed **before** the requirements file, from the CPU-only index
(`backend/readme:61,69`). For GPU builds use the command from
[pytorch.org](https://pytorch.org/get-started/locally/).

PyTorch is genuinely needed here — both `ultralytics` (YOLOv8) and `sentence-transformers` depend on it.

## Step 5 — Install dependencies

The command documented in the repository:

```bash
pip install -r requirements.txt        # backend/readme:77
```

### ⚠️ This currently fails — two problems

**Problem 1 — the file is UTF-16 encoded.** It begins with a `ff fe` byte-order mark and pip cannot parse
it. Convert it first:

```powershell
# Windows PowerShell, from backend/
Get-Content requirements.txt | Set-Content -Encoding utf8 requirements.utf8.txt
pip install -r requirements.utf8.txt
```

```bash
# macOS / Linux, from backend/
iconv -f UTF-16 -t UTF-8 requirements.txt > requirements.utf8.txt
pip install -r requirements.utf8.txt
```

**Problem 2 — eight imported packages are undeclared:**

```bash
pip install google-genai langchain-google-genai langchain-chroma langchain-core \
            pymupdf python-docx pymysql rapidfuzz
```

| Package | Imported as | Needed by |
| ------- | ----------- | --------- |
| `google-genai` | `from google import genai` | `vision_service`, `photo_service` — **the new SDK**; requirements pins the old `google-generativeai` |
| `langchain-google-genai` | `langchain_google_genai` | `services/vector_db.py` |
| `langchain-chroma` | `langchain_chroma` | `services/vector_db.py` |
| `langchain-core` | `langchain_core` | `services/vector_db.py` |
| `pymupdf` | `fitz` | `utils/kyc_document_parser.py` |
| `python-docx` | `docx` | `utils/kyc_document_parser.py` |
| `pymysql` | `pymysql` | `services/user_db.py` |
| `rapidfuzz` | `rapidfuzz` | product / master services |

Without these the backend raises `ModuleNotFoundError` on startup. Both problems are
[AUDIT.md](../../AUDIT.md) issues 4 and 5; fixing `requirements.txt` resolves them permanently.

### What the file declares

| Group | Packages |
| ----- | -------- |
| API | `fastapi`, `uvicorn`, `python-multipart`, `python-dotenv` |
| Vision / ML | `ultralytics`, `opencv-python`, `pillow`, `numpy`, `torch`, `torchvision`, `transformers`, `sentence-transformers==2.7.0`, `scipy==1.13.1` |
| Vector | `qdrant-client==1.9.1` |
| Database | `sqlalchemy==2.0.31`, `psycopg2-binary==2.9.9` |
| Google | `google-generativeai`, `google-cloud-vision` |
| Documents | `pypdf==4.2.0` |
| Security | `cryptography`, `python-jose`, `passlib[bcrypt]` |
| Utilities | `tqdm==4.66.4` |

## Step 6 — Configure environment variables

Create `backend/.env` (not committed — `.gitignore` excludes `.env*`):

```ini
# ---- Database ----
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fashion_discovery
DB_USERNAME=postgres
DB_PASSWORD=<your-password>

# ---- Security ----
API_TOKEN=<choose-a-long-random-string>
TOKEN_SECRET=<choose-a-long-random-string>

# ---- AI ----
GOOGLE_API_KEY=<your-gemini-key>
GOOGLE_AI_MODEL=gemini-2.0-flash

# ---- Storage ----
STORAGE_DIR=storage
VECTOR_DB_DIR=qdrant_storage
BASE_URL=http://127.0.0.1:8000/
```

`API_TOKEN` must match `frontend/.env.local`. `BASE_URL` **must end with a slash** — it is concatenated
directly when building returned image URLs.

Full inventory, including variables present but never read:
[environment-variables.md](environment-variables.md).

## Step 7 — Add the Google Cloud Vision key

Place `vision-key.json` in `backend/`. See
[google-cloud-credentials.md](google-cloud-credentials.md) for how to generate it.

Without this file the backend raises `FileNotFoundError` at import.

## Step 8 — Configure the database

```bash
createdb fashion_discovery      # must match DB_NAME
```

The application creates its own tables at startup. See [database-setup.md](database-setup.md).

## Step 9 — Migrations

**None required, and none available.** There is no Alembic configuration. `create_all()` creates missing
tables but never alters existing ones — schema changes need manual DDL.
[AUDIT.md](../../AUDIT.md) issue 19.

## Step 10 — Seed data

**Not verified from the current implementation.** No seed scripts, fixtures or bootstrap data exist.

To use image search you must first populate masters (category, brand, colour) and then products, so that
the Qdrant collection has something to match against. See [local-development.md](local-development.md).

## Step 11 — Start the server

**Development** (`backend/readme:87`):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production** (`backend/readme:95`):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Run from `backend/` — all static mounts use relative paths.

Expected first-start output:

```
Final DB URL =======>  postgresql+psycopg2://...
✅ Qdrant client initialized with storage at: qdrant_storage
Total points: 0
✅ All tables created successfully!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

> Two things to note. The first line prints your **database password** to the console
> ([AUDIT.md](../../AUDIT.md) issue 4 in the security list). And `Total points: 0` is expected — the
> Qdrant collection is recreated empty on every start ([AUDIT.md](../../AUDIT.md) issue 3).

First start also downloads `yolov8s.pt` (~22 MB) and the sentence-transformer model (~420 MB) if they are
not cached, which takes several minutes.

## Step 12 — Background workers

**None to start.** No Celery, Redis or worker process exists.

## Step 13 — Tests, lint, format, type-check

**Not verified from the current implementation.** No test suite, no pytest configuration, and no `ruff`,
`flake8`, `black`, `isort` or `mypy` config. See [../testing/testing-status.md](../testing/testing-status.md).

## Step 14 — Verify

```bash
curl http://localhost:8000/
# {"message":"FastAPI MVC Running"}
```

```bash
curl -H "PK-apiToken: <your-token>" -H "Content-Type: application/json" \
     -d '{"search":"","limit":10,"offset":0}' \
     http://localhost:8000/master/category/list
```

Swagger UI: <http://localhost:8000/docs>

## Command reference

| Purpose | Command | Required | Verified from |
| ------- | ------- | -------- | ------------- |
| Python version | `python --version` | Yes | `backend/readme:26` |
| Create venv | `python -m venv venv` | Yes | `backend/readme:41` |
| Activate (Windows) | `.\venv\Scripts\activate` | Yes | `backend/readme:49` |
| Activate (macOS/Linux) | `source venv/bin/activate` | Yes | `backend/readme:55` |
| Upgrade pip | `python -m pip install --upgrade pip` | Yes | `backend/readme:61` |
| Install PyTorch | `pip install torch==2.9.1 torchaudio==2.9.1 --index-url https://download.pytorch.org/whl/cpu` | Yes | `backend/readme:69` |
| Install dependencies | `pip install -r requirements.txt` | Yes | `backend/readme:77` — **needs the UTF-8 workaround** |
| Install missing packages | `pip install google-genai langchain-google-genai langchain-chroma langchain-core pymupdf python-docx pymysql rapidfuzz` | Yes | Derived from import analysis |
| Migrations | — | — | None exist |
| Seed | — | — | Not verified from the current implementation |
| Run (dev) | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` | Yes | `backend/readme:87` |
| Run (prod) | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | Yes | `backend/readme:95` |
| Worker | — | — | Not applicable |
| Tests / lint / format / type-check | — | — | Not verified from the current implementation |
| Freeze dependencies | `pip freeze > requirements.txt` | Optional | `backend/readme:127` |
| Deactivate venv | `deactivate` | Optional | `backend/readme:135` |
