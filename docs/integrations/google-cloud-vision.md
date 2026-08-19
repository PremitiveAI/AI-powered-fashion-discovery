# Integration — Google Cloud Vision

Provides precise bounding boxes for detected items. Gemini says *what* an item is; Cloud Vision says
*where* it is — and where the two disagree, Vision wins.

## Configuration

| Item | Value |
| ---- | ----- |
| Package | `google-cloud-vision` (declared in `requirements.txt`) |
| Credential | A **service-account JSON key file** |
| Env variable | `GOOGLE_APPLICATION_CREDENTIALS`, default `vision-key.json` |
| Client | `vision.ImageAnnotatorClient(credentials=…)` |

```python
# app/services/vision_service.py
KEY_PATH = env("GOOGLE_APPLICATION_CREDENTIALS", default="vision-key.json")
credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
vision_client = vision.ImageAnnotatorClient(credentials=credentials)
```

This runs at **import time**. A missing or malformed key file raises before the application finishes
loading — the backend will not start.

`GOOGLE_APPLICATION_CREDENTIALS` is **not present in `backend/.env`**, so the default path applies and
the file must sit in `backend/` alongside `app/`. Because the path is relative, uvicorn must be started
from `backend/`.

Setup instructions — creating the project, enabling the API, linking billing, generating and placing the
key: [../setup/google-cloud-credentials.md](../setup/google-cloud-credentials.md).

> ⚠️ `vision-key.json` is a **private key**. It is covered by `.gitignore`; never remove that entry, and
> never place it inside `frontend/`.

## Usage — object localization

One function, called once per analysed crop:

```python
def localize_objects(image):
    ok, buffer = cv2.imencode(".jpg", image)
    if not ok:
        return []

    vision_image = vision.Image(content=buffer.tobytes())
    response = vision_client.object_localization(image=vision_image)

    for obj in response.localized_object_annotations:
        label = obj.name.lower()
        if "person" in label:
            continue                      # the person box comes from YOLO
        …
```

Returns a list of:

```python
{ "label": "<lowercased name>",
  "bbox_norm": { "x1": min_x, "y1": min_y, "x2": max_x, "y2": max_y },   # 0.0–1.0
  "score": 0.87 }
```

Coordinates are **normalised** (0–1) relative to the submitted crop, and are converted to resized-image
pixels by `vision_norm_to_resized` in `decision_engine`.

## Where it sits in the pipeline

```
YOLOv8s  →  person box
            ↓
       crop the person
            ↓
   ┌────────┴────────┐
Gemini            Cloud Vision
attributes        bounding boxes
   └────────┬────────┘
    choose_best_bbox
    Vision "precise" > Gemini "approximate" > none
```

A Vision box is only used when its label **matches** the Gemini item type, via the `SYNONYMS` map plus
substring fallback. See [../ai/image-analysis-pipeline.md](../ai/image-analysis-pipeline.md).

## Failure handling — silent degradation

Both call sites wrap it in a bare `except`:

```python
try:
    vision_items = localize_objects(person_crop) or []
except Exception:
    vision_items = []
```

So **any** Vision failure — expired credentials, disabled API, unlinked billing, quota exhaustion,
network error — produces an empty list and the pipeline continues using Gemini boxes only.

The practical symptom is not an error but a **quality regression**: every item's `confidence` drops from
`"precise"` to `"approximate"`, and boxes become noticeably looser. Nothing is logged.

If bounding boxes suddenly degrade, check Cloud Vision first — it is failing silently by design.

## Cost

One `object_localization` call per analysed crop — so **one per image search**, since only the largest
person is processed. Object mode also makes one call.

Billed per image; see [Vision API pricing](https://cloud.google.com/vision/pricing). Requires an active
billing account even within the free tier.

## Failure modes

| Failure | Behaviour |
| ------- | --------- |
| Key file missing / malformed | **Backend fails to start** (`FileNotFoundError` / `ValueError` at import) |
| API not enabled on the project | `403 SERVICE_DISABLED` → caught → empty list |
| Billing not linked | `400` → caught → empty list |
| Service account lacks a Vision role | `403 PERMISSION_DENIED` → caught → empty list |
| Quota exceeded / network error | Caught → empty list |
| `cv2.imencode` fails | Returns `[]` before any API call |

Only the first is visible. Everything else degrades quietly.

## Diagnosing

```bash
# from backend/, with the venv active — confirms the credential loads
python -c "from google.oauth2 import service_account; \
c=service_account.Credentials.from_service_account_file('vision-key.json'); \
print('OK —', c.service_account_email)"
```

Then confirm the API is enabled and billing is linked on the **same project** as the key's `project_id`.

## Known limitations

1. **All failures are swallowed** — no logging, no metric, no user-visible signal.
2. **Person labels are discarded** by design, so Vision contributes nothing to the person box.
3. **No timeout and no retry.**
4. **Credentials load at import**, so the key must exist even to run endpoints that never use Vision.
5. **The relative default path** ties the working directory to `backend/`.
6. **`describe_with_vision_fallback`** in the same module combines Vision and Gemini into one result —
   but **no caller exists**; `decision_engine` calls the two separately and arbitrates itself.
