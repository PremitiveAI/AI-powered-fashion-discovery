# Phase 2 API — Models and Analysis

> ⚠️ **In active development.** These routers changed during the review — `main.py` was edited to
> register them mid-analysis. Endpoint names and shapes below are a snapshot; re-verify before relying
> on them.

Routers: `models_router` (`/models`) in
[`app/routes/models_routes.py`](../../backend/app/routes/models_routes.py) and `model_router` (`/model`)
in [`app/routes/model_analysis_routes.py`](../../backend/app/routes/model_analysis_routes.py).

## 🔴 `/models/*` requires no authentication

The auth middleware skips any path starting `/models` so the `/models` **static mount** can serve files.
That test also matches the `/models` **router**, so **all 10 endpoints below are callable with no
`PK-apiToken`** — including uploads, database writes and paid Gemini calls.

`/model/*` (analysis) is **not** affected and does require the token.

See [../security/authentication-and-authorization.md](../security/authentication-and-authorization.md)
and [AUDIT.md](../../AUDIT.md) issue 1.

---

## `/models` — 10 endpoints

| Method | Path | Called by frontend |
| ------ | ---- | :----------------: |
| POST | `/models/user-photo` | ✅ `/api/phase2/save-user-photo` |
| GET | `/models/last-user-photo` | ✅ `/api/phase2/get-user-photo` |
| POST | `/models/upload-gallery` | ❌ |
| POST | `/models/gallery-list` | ❌ |
| POST | `/models/gallery-delete` | ❌ |
| POST | `/models/category_create` | ❌ |
| POST | `/models/category-list` | ✅ `/api/phase2/categories` |
| POST | `/models/save-models` | ❌ |
| POST | `/models/user-try-on` | ✅ `/api/phase2/user-try-on` |
| POST | `/models/models-list` | ✅ `/api/phase2/model-list` |

## `/model` — 3 endpoints

| Method | Path | Called by frontend |
| ------ | ---- | :----------------: |
| POST | `/model/upload` | ❌ |
| POST | `/model/fetchData` | ❌ |
| POST | `/model/uploadUserImage` | ❌ |

None of the three are wired to the UI.

---

## Frontend calls with no backend endpoint

Four Phase 2 BFF handlers target endpoints that do not exist:

| Frontend handler | Target | Status |
| ---------------- | ------ | ------ |
| `/api/phase2/get-categories` | `models/get-categories` | ❌ missing |
| `/api/phase2/save-categories` | `models/save-categories` | ❌ missing |
| `/api/phase2/look-detail` | `models/model-detail` | ❌ missing |
| `/api/phase2/get-sizes` | `models/get-body-measurement-by-gender` | ❌ missing |

So of nine distinct targets the frontend calls, **five exist and four do not**. Conversely five backend
endpoints have no caller. [AUDIT.md](../../AUDIT.md) issue 7.

---

## Data model

Phase 2 owns six tables — see [../database/schema.md](../database/schema.md):

| Table | Purpose |
| ----- | ------- |
| `tbl_models` | A model/look — `model_name`, **`modle_url`** (typo), `prompt`, `category_id`, `gender` |
| `tbl_models_type` | Outfit attributes per model — `category`, `type`, `subtype`, `color`, `pattern`, `brand`, `gender` |
| `tbl_models_try_on` | Try-on results — `user_url` |
| `tbl_category_models` | Categories — `name`, `type`, `gallery_id`, `gender` |
| `tbl_models_gallery` | Images — `image_url`, `type` Enum(`category`\|`models`) |
| `tbl_model_analysis` | Analysis records — `model_name`, `model_url`, `user_url`, `prompt` |

`tbl_models` cascades deletes to `tbl_models_type` and `tbl_models_try_on`.

## Supporting modules

| Layer | Files |
| ----- | ----- |
| Controllers | `models_controller`, `models_category_controller`, `model_gallery_controller`, `model_analysis_controller` |
| Services | `models_service`, `model_analysis_service`, `decision_models_engine` |
| Schemas | `model_gallery_schema` |
| Prompts | `app/core/models_prompt.py`, `app/core/photo_prompts.py` |

`decision_models_engine.py` is a Phase 2 counterpart to the main
[`decision_engine`](../ai/image-analysis-pipeline.md), and `models_prompt.py` / `photo_prompts.py` hold
its prompt contracts.

---

## What is not documented here

**Request and response shapes are not verified from the current implementation.** The Phase 2 service and
controller internals were not read line-by-line, for two reasons: the feature is mid-development and
changed during the review, and documenting shapes that are actively being edited would be misleading.

What *is* verified: the endpoint paths, which router they belong to, whether the frontend calls them, the
auth-bypass condition, and the table structures they operate on.

Once Phase 2 stabilises, this document should be extended with request schemas, response envelopes,
validation rules and the `decision_models_engine` pipeline — mirroring
[products-and-gallery.md](products-and-gallery.md).

## Related

- [../features/phase2-models.md](../features/phase2-models.md) — feature-level view and UI flow
- [../security/authentication-and-authorization.md](../security/authentication-and-authorization.md) — the bypass
- [../database/schema.md](../database/schema.md) — the six Phase 2 tables
