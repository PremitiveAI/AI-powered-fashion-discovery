# Prerequisites

## Runtimes

| Requirement | Version | Source of the requirement |
| ----------- | ------- | ------------------------- |
| Python | **3.10 or 3.11** | [`backend/readme:26`](../../backend/readme) |
| Node.js | **v24.12.0** | [`frontend/README.md`](../../frontend/README.md) links this installer |
| npm | bundled with Node | Only `package-lock.json` exists — no yarn/pnpm/bun lockfile |
| PostgreSQL | 12+ | Driver is `psycopg2`; URL is `postgresql+psycopg2://` |

```bash
python --version     # expect 3.10.x or 3.11.x
node -v              # expect v24.x
npm -v
psql --version
```

The Python bound is real: `requirements.txt` pins `sentence-transformers==2.7.0` and `scipy==1.13.1`, and
`backend/readme` pins `torch==2.9.1` — combinations that will not resolve cleanly on much newer or older
interpreters.

## Services

| Service | Required | Notes |
| ------- | -------- | ----- |
| PostgreSQL | **Yes** | Tables are auto-created on first start |
| Qdrant | **No separate server** | Runs embedded, in-process, against `VECTOR_DB_DIR` |
| Redis | No | Not used anywhere in the repository |
| Celery / any broker | No | No background processing exists |

## Credentials

Both are mandatory — the backend imports them at module load and will not start without either.

| Credential | Used for | How to obtain |
| ---------- | -------- | ------------- |
| **`GOOGLE_API_KEY`** | Gemini 2.0 Flash (attributes), Gemini 2.5 Flash Image (try-on), safety and face gates | [Google AI Studio](https://aistudio.google.com/) |
| **`vision-key.json`** | Google Cloud Vision object localization | [google-cloud-credentials.md](google-cloud-credentials.md) |

Failure modes if missing:

- `GOOGLE_API_KEY` absent → `RuntimeError: GOOGLE_API_KEY not found` from `photo_service`, or
  `AttributeError` on `None.strip()` from `vector_db`.
- `vision-key.json` absent → `FileNotFoundError` from `vision_service` at import.

Cloud Vision also requires the API to be **enabled** and **billing linked** on the same Google Cloud
project. Both are covered in the credentials guide.

## Machine learning assets

`detector.py` instantiates `YOLO("yolov8s.pt")` at import. If the weights file is not present in the
working directory, `ultralytics` **downloads it automatically on first run** (~22 MB), so the first
backend start needs internet access and will pause while it fetches.

`app/vector/vector_db.py` loads `sentence-transformers/all-mpnet-base-v2` at import — roughly 420 MB,
downloaded once to the HuggingFace cache. Expect a slow first start and meaningful RAM use thereafter.

## Disk

| Path | Grows with |
| ---- | ---------- |
| `backend/storage/` | Every uploaded search image + one analysis JSON each |
| `backend/uploads/` | Gallery uploads |
| `backend/try_on/` | Every generated try-on image |
| `backend/qdrant_storage/` | The vector index |
| `/tmp/person_crops`, `/tmp/debug_boxes` | One crop and one annotated image **per analysed photo** |

**Nothing prunes any of these.** The debug directories in particular grow with every request.

## Ports

| Port | Component | Configurable |
| ---: | --------- | ------------ |
| 5432 | PostgreSQL | `DB_PORT` |
| 8000 | FastAPI backend | uvicorn `--port` |
| **3002** | Next.js frontend | `package.json` → `next dev -p 3002` |

> `API_PORT` exists in `backend/.env` but **no code reads it**. The backend port comes solely from the
> uvicorn command line. Use **8000**, which is what `BASE_URL` and `backend/readme` assume.

## Platform notes

Development has been Windows-based. Two things to know on other platforms:

1. `decision_engine` hard-codes `/tmp/person_crops` and `/tmp/debug_boxes`, and `main.py` mounts them.
   These work on Linux/macOS naturally; on Windows they resolve to the current drive root.
2. All static mounts use **relative** paths, so the backend must be launched from `backend/` on every
   platform.

## Next steps

1. [database-setup.md](database-setup.md)
2. [google-cloud-credentials.md](google-cloud-credentials.md)
3. [backend-setup.md](backend-setup.md)
4. [frontend-setup.md](frontend-setup.md)
5. [local-development.md](local-development.md)
