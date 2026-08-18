# Google Cloud Credentials — Creating `vision-key.json`

The backend needs **two separate Google credentials**:

| Credential | Used for | Form |
| ---------- | -------- | ----- |
| `GOOGLE_API_KEY` | Gemini (attribute extraction, virtual try-on, safety gates) | a string in `backend/.env` |
| `vision-key.json` | Google Cloud **Vision API** object localization | a service-account JSON key file |

This document covers the second one. Without it the backend **will not start** — the credentials file is
loaded at import time:

```python
# app/services/vision_service.py
KEY_PATH = env("GOOGLE_APPLICATION_CREDENTIALS", default="vision-key.json")
credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
vision_client = vision.ImageAnnotatorClient(credentials=credentials)
```

A missing or malformed file raises before the application finishes importing.

---

## ⚠️ Before you begin

`vision-key.json` is a **private key**. Anyone holding it can call the Vision API billed to your project.

- It is now listed in [`.gitignore`](../../.gitignore) — **never remove that entry.**
- Never paste its contents into chat, tickets, screenshots or documentation.
- Never place it inside `frontend/`, where a build could bundle it.
- If a key is ever exposed, **disable it in Google Cloud immediately** and generate a new one; rotating
  is cheap, and a leaked key remains valid until you revoke it.

---

## Step 1 — Create or select a Google Cloud project

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Use the project selector in the top bar → **New Project** (or pick an existing one).
3. Give it a name, then **Create**.
4. Note the **Project ID** — you will confirm it in Step 5.

## Step 2 — Enable the Cloud Vision API

1. Navigate to **APIs & Services → Library**.
2. Search for **Cloud Vision API**.
3. Open it and click **Enable**.

The API must be enabled on the *same* project the service account belongs to, or calls fail with a
`403 SERVICE_DISABLED` error.

## Step 3 — Enable billing

Cloud Vision requires a billing account even within the free tier. **Billing → Link a billing account.**
Object localization is billed per image; see
[Vision API pricing](https://cloud.google.com/vision/pricing).

## Step 4 — Create a service account

1. **IAM & Admin → Service Accounts → Create Service Account**.
2. **Name:** something identifiable, e.g. `fashion-discovery-vision`.
3. **Grant this service account access to project:** select the role
   **`Cloud Vision AI Service Agent`**, or the broader **`Project → Viewer`** if your organisation's
   policy prefers it.

   > Grant the narrowest role that works. This service account only needs to call
   > `object_localization`; it does not need Editor or Owner.
4. Skip the optional "grant users access" step → **Done**.

## Step 5 — Generate the JSON key

1. Open the service account you just created.
2. **Keys → Add Key → Create new key**.
3. Choose **JSON** → **Create**.
4. The browser downloads a file named something like
   `your-project-1a2b3c4d5e6f.json`. This is the only copy — Google does not let you download it again.

The file has this shape (values redacted):

```json
{
  "type": "service_account",
  "project_id": "<your-project-id>",
  "private_key_id": "<redacted>",
  "private_key": "-----BEGIN PRIVATE KEY-----\n<redacted>\n-----END PRIVATE KEY-----\n",
  "client_email": "fashion-discovery-vision@<project>.iam.gserviceaccount.com",
  "client_id": "<redacted>",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/...",
  "universe_domain": "googleapis.com"
}
```

Confirm `project_id` matches the project where you enabled the Vision API.

## Step 6 — Place the file

Rename it to `vision-key.json` and put it in the **backend root** — the same directory you run
`uvicorn` from:

```
AI-Powered-Fashion-Discovery/
└── backend/
    ├── app/
    ├── requirements.txt
    └── vision-key.json      ← here
```

The default path is **relative**, so it resolves against the working directory. Starting the backend
from anywhere other than `backend/` will fail to find it.

### Using a different path or filename

Set `GOOGLE_APPLICATION_CREDENTIALS` in `backend/.env`:

```ini
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/your-key.json
```

The variable is read with a fallback:

```python
KEY_PATH = env("GOOGLE_APPLICATION_CREDENTIALS", default="vision-key.json")
```

It is **not** currently present in `backend/.env`, so the default applies unless you add it. If you
choose a filename other than `vision-key.json`, confirm it is still covered by `.gitignore` — the
patterns there cover `service-account*.json`, `*-service-account.json`, `gcp-credentials*.json` and
`credentials.json` as well.

## Step 7 — Verify

```bash
# from backend/, with the venv active
python -c "from google.oauth2 import service_account; \
c=service_account.Credentials.from_service_account_file('vision-key.json'); \
print('OK — service account:', c.service_account_email)"
```

Then confirm git is not tracking it:

```bash
git check-ignore -v backend/vision-key.json
# expected: .gitignore:<line>:**/vision-key.json   backend/vision-key.json
```

Finally start the backend — a successful import means credentials loaded:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Troubleshooting

| Error | Cause | Fix |
| ----- | ----- | --- |
| `FileNotFoundError: vision-key.json` | File missing, misnamed, or uvicorn started from the wrong directory | Place it in `backend/`, run uvicorn from `backend/` |
| `ValueError: Service account info was not in the expected format` | Wrong key type downloaded (e.g. an OAuth client ID), or the file is truncated | Re-download a **service account** key of type **JSON** |
| `403 ... Cloud Vision API has not been used in project ...` | Vision API not enabled on that project | Step 2 |
| `403 PERMISSION_DENIED` | Service account lacks a Vision role | Step 4 |
| `400 ... billing account` | Billing not linked | Step 3 |
| Backend starts but localization always returns `[]` | Calls are failing and being swallowed — `localize_objects` is wrapped in a bare `except` by its callers in `decision_engine` | Check `logs/errors.log`; test the snippet in Step 7 |

## Related

- [environment-variables.md](environment-variables.md) — the full variable inventory
- [backend-setup.md](backend-setup.md) — where this fits in the install sequence
- [../integrations/google-cloud-vision.md](../integrations/google-cloud-vision.md) — how the API is used
- [../integrations/google-gemini.md](../integrations/google-gemini.md) — the separate `GOOGLE_API_KEY`
