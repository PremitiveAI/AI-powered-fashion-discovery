# Integration — Google Gemini

Two distinct Gemini models do three jobs: attribute extraction, safety gating, and image generation.

## Configuration

| Variable | Required | Default | Purpose |
| -------- | -------- | ------- | ------- |
| `GOOGLE_API_KEY` | **Yes** | — | API key for both models |
| `GOOGLE_AI_MODEL` | No | `gemini-2.0-flash` | Text/vision model id |

Two modules construct clients, and they do it differently:

```python
# app/services/vision_service.py — uses the project's env helper
genai_client = genai.Client(api_key=env("GOOGLE_API_KEY"))
GEMINI_MODEL = "gemini-2.0-flash"          # ← hard-coded here, not from GOOGLE_AI_MODEL

# app/services/photo_service.py — bypasses the helper
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("GOOGLE_API_KEY not found")
client = genai.Client(api_key=api_key)
```

Both run at **import time**, so a missing key prevents the backend from starting — even for endpoints
that never call the model.

> Note the inconsistency: `vision_service` hard-codes `"gemini-2.0-flash"` and ignores
> `GOOGLE_AI_MODEL`, while other modules read the variable. Changing `GOOGLE_AI_MODEL` does **not**
> change the model used for attribute extraction.

SDK: `google-genai` (the new `from google import genai` interface). Note `requirements.txt` declares the
**old** `google-generativeai` package instead — see [AUDIT.md](../../AUDIT.md) issue 5.

## Usage 1 — Attribute extraction

`vision_service.describe(image, prompt)` — the heart of image search.

| Property | Value |
| -------- | ----- |
| Model | `gemini-2.0-flash` |
| Input | A JPEG-encoded crop (person) or the full image (object), plus `PERSON_PROMPT` or `OBJECT_PROMPT` |
| Output | JSON — clothing/accessory attributes with `bbox_relative` on a 0–1000 scale |
| Concurrency | Wrapped in `loop.run_in_executor` so the blocking SDK call does not stall the event loop |

Response cleanup via `clean_json`: strips markdown fences, removes trailing commas, extracts the first
`{...}` or `[...]`. On parse failure `describe` prints the error **and the raw response** to the console,
then returns `{}` — a successful call yielding no items.

Prompt contracts: [../ai/prompts-and-schemas.md](../ai/prompts-and-schemas.md).

## Usage 2 — Safety and face gates

`photo_service.gemini_has_face(bytes)` and `gemini_is_safe_tryon(bytes)`.

Both are used by try-on; `gemini_is_safe_tryon` is **also** called by `ProductController.search`, so
every image search costs a safety call before any analysis begins.

Failures return `{"status": "Fail", "message": …}` with **HTTP 200** on the try-on path, or `Code 4002`
on the search path.

## Usage 3 — Image generation

`photo_service.generate_final_image_bytes(user_bytes, cloth_bytes, output_path)`.

| Property | Value |
| -------- | ----- |
| Model | **`gemini-2.5-flash-image`** |
| Config | `GenerateContentConfig(response_modalities=["IMAGE"])` |
| Input | Three parts — identity instruction, user image, task instruction + garment image |
| Output | First inline-data part, opened with Pillow and saved as PNG |

If no part carries `inline_data`, the function raises `RuntimeError("Gemini did not return an image")`.

Prompt and behaviour: [../ai/virtual-try-on.md](../ai/virtual-try-on.md).

## Cost per operation

Nothing meters, caches, throttles or logs usage.

| Operation | Gemini calls |
| --------- | -----------: |
| Image search | 1 safety + 1 attribute extraction = **2** |
| Virtual try-on | 1 face + 1 safety + 1 generation = **3** |
| Phase 2 try-on | **Not verified from the current implementation** |

Image generation is materially more expensive than text/vision calls, so try-on dominates spend.

Because authentication is a single shared token, **any holder of that token can consume your quota**.

## Failure modes

| Failure | Behaviour |
| ------- | --------- |
| Key missing | **Backend fails to start** — clients build at import |
| Key invalid / quota exceeded | Exception at call time → HTTP 500 |
| Network failure | Same — **no retry, no timeout, no circuit breaker** |
| Model returns non-JSON | `clean_json` salvages what it can; on failure `describe` returns `{}` and the item list is empty |
| Generation returns no image | `RuntimeError` → HTTP 500 |

The fourth is the one to watch: an empty result is indistinguishable from "nothing detected". The raw
response is printed to the **console only** — not to `logs/errors.log`.

## Data sent to Google

Every image search transmits the uploaded photograph — which, by the nature of this product, is
frequently a photograph of a person. Every try-on transmits the user's face plus the garment image.

Nothing is redacted and there is no flag to disable it. If you have data-residency or biometric-data
obligations, this is the integration that triggers them.

## Changing the model

| Setting | Effect |
| ------- | ------ |
| `GOOGLE_AI_MODEL` | Read by some modules; **ignored** by `vision_service`, which hard-codes `gemini-2.0-flash` |
| Generation model | Hard-coded `gemini-2.5-flash-image` in `photo_service` — code edit required |

To genuinely change the extraction model you must edit `vision_service.GEMINI_MODEL`.

## Known limitations

1. **`GOOGLE_AI_MODEL` does not control the extraction model** despite appearing to.
2. **Two client-construction styles** — one via `app.config.env`, one via raw `os.getenv`.
3. **No timeout and no retry** anywhere.
4. **Malformed output is silent** — empty results look like clean "no detections".
5. **No caching**, so re-analysing the same image costs the same again.
6. **`GoogleGenerativeAIEmbeddings` is constructed but never used** in `services/vector_db.py` — a dead
   client on an orphaned module.
7. **Fails closed at startup** — no key means no backend at all.
