# Feature — Phase 2: Models & Looks

Browse fashion models, save a user photo, and generate a try-on against a chosen look.

**Status:** ⚠️ **In development.** The backend exists and is registered; the frontend and backend are
partially out of sync.

> This module was being actively edited during the review — `backend/app/main.py` changed mid-analysis
> to register its routers. Treat the endpoint list below as a snapshot and re-verify before relying on
> it.

## Business purpose

Extends try-on from "this garment on my photo" to "this complete look on my photo" — a curated model
wearing a full outfit, browsable by category and gender.

## User flow

| Page | Path | Purpose |
| ---- | ---- | ------- |
| Home | `/phase2/home` | Browse categories and models |
| Style profile | `/phase2/style-profile` | Capture preferences, sizes and a user photo |
| Loading | `/phase2/loading` | `GeneratingLook.tsx` — progress state during generation |
| Look detail | `/phase2/look-detail` | View a generated look |

## Frontend → backend alignment

Nine distinct targets are called; **five exist, four do not.**

| Frontend handler | Target | Status |
| ---------------- | ------ | :----: |
| `/api/phase2/save-user-photo` | `models/user-photo` | ✅ |
| `/api/phase2/get-user-photo` | `models/last-user-photo` | ✅ |
| `/api/phase2/categories` | `models/category-list` | ✅ |
| `/api/phase2/model-list` | `models/models-list` | ✅ |
| `/api/phase2/user-try-on` | `models/user-try-on` | ✅ |
| `/api/phase2/get-categories` | `models/get-categories` | ❌ **missing** |
| `/api/phase2/save-categories` | `models/save-categories` | ❌ **missing** |
| `/api/phase2/look-detail` | `models/model-detail` | ❌ **missing** |
| `/api/phase2/get-sizes` | `models/get-body-measurement-by-gender` | ❌ **missing** |

Conversely, **five backend endpoints have no caller**: `models/category_create`,
`models/upload-gallery`, `models/gallery-list`, `models/gallery-delete`, `models/save-models`.

The four missing endpoints all serve the **style-profile** and **look-detail** screens, so those are the
parts that cannot function. [AUDIT.md](../../AUDIT.md) issue 7.

## 🔴 `/models/*` requires no authentication

The auth middleware skips any path beginning `/models` so the `/models` **static mount** can serve
files — but that test also matches the `/models` **router**:

```python
if request.url.path.startswith("/models"):
    return await call_next(request)          # auth_middleware.py:31
```

```python
models_router = APIRouter(prefix="/models", ...)   # models_routes.py:14
```

**All ten Phase 2 endpoints are callable with no `PK-apiToken`** — including those that accept uploads,
write to the database and invoke paid Gemini calls.

Fix direction: rename the static mount (e.g. `/model-assets`) and remove the `/models` skip. No code
change has been made. [AUDIT.md](../../AUDIT.md) issue 1.

## Backend endpoints

| Method | Path | Called by UI |
| ------ | ---- | :----------: |
| POST | `/models/user-photo` | ✅ |
| GET | `/models/last-user-photo` | ✅ |
| POST | `/models/upload-gallery` | ❌ |
| POST | `/models/gallery-list` | ❌ |
| POST | `/models/gallery-delete` | ❌ |
| POST | `/models/category_create` | ❌ |
| POST | `/models/category-list` | ✅ |
| POST | `/models/save-models` | ❌ |
| POST | `/models/user-try-on` | ✅ |
| POST | `/models/models-list` | ✅ |

Plus `/model` (3 endpoints — `upload`, `fetchData`, `uploadUserImage`) from
`model_analysis_routes.py`, none of which the UI calls. `/model/*` **is** token-protected.

Full reference: [../api/models-phase2.md](../api/models-phase2.md).

## Database interaction

Six tables — see [../database/schema.md](../database/schema.md):

| Table | Purpose |
| ----- | ------- |
| `tbl_models` | A model/look — `model_name`, **`modle_url`** (typo), `prompt`, `category_id` FK, `gender` |
| `tbl_models_type` | Outfit attributes — `category`, `type`, `subtype`, `color`, `pattern`, `brand`, `gender` |
| `tbl_models_try_on` | Generated results — `user_url` |
| `tbl_category_models` | Categories — `name`, `type`, `gallery_id` (no FK), `gender` |
| `tbl_models_gallery` | Images — `image_url`, `type` Enum(`category`\|`models`) |
| `tbl_model_analysis` | Analysis records — `model_name`, `model_url`, `user_url`, `prompt` |

`tbl_models` cascades deletes to `tbl_models_type` and `tbl_models_try_on`.

## Supporting modules

| Layer | Files |
| ----- | ----- |
| Controllers | `models_controller`, `models_category_controller`, `model_gallery_controller`, `model_analysis_controller` |
| Services | `models_service`, `model_analysis_service`, **`decision_models_engine`** |
| Schemas | `model_gallery_schema` |
| Prompts | `app/core/models_prompt.py`, `app/core/photo_prompts.py` |

`decision_models_engine.py` is the Phase 2 counterpart to the main
[image-analysis pipeline](../ai/image-analysis-pipeline.md).

## What is not documented here

**Request and response shapes are not verified from the current implementation.** The Phase 2 service
and controller internals were not read line-by-line, deliberately: the feature was mid-edit during the
review, and documenting shapes that are actively changing would mislead.

Verified and stated above: endpoint paths, router membership, frontend call alignment, the auth-bypass
condition, and the tables involved.

## Known limitations

1. **No authentication on `/models/*`** — the most serious issue in the module.
2. **Four endpoints the UI needs do not exist**, so style-profile and look-detail cannot load.
3. **Five backend endpoints are unused** — gallery management and model creation have no UI.
4. **`app.mount("/models")` collides with the router prefix**, which is the direct cause of item 1.
5. **`tbl_models.modle_url` is misspelled** in a live column; renaming needs a migration, and no
   migration tooling exists.
6. **`tbl_category_models.gallery_id` has no foreign key.**

## When this stabilises

Extend [../api/models-phase2.md](../api/models-phase2.md) with request schemas, response envelopes,
validation rules and the `decision_models_engine` pipeline — mirroring
[../api/products-and-gallery.md](../api/products-and-gallery.md).
