# AI — Prompts and Schemas

The contracts between the application and the LLM. These are undocumented in the codebase, and changing
them silently changes the shape of every downstream consumer.

**Prompt files:** [`app/core/prompts.py`](../../backend/app/core/prompts.py) (image analysis),
`models_prompt.py` and `photo_prompts.py` (Phase 2), `prompts copy.py` (an unused duplicate).

## `PERSON_PROMPT`

Used by `analyze_person_mode` against a cropped person region.

**Instructions given to the model:**

- Return **only** valid JSON.
- Analyse only the person in the crop; ignore background, furniture, distant people, reflections.
- Identify all clothing worn, all accessories/footwear/jewellery, and anything held or carried.
- Return **all** fields for every item; use `null` rather than omitting a key.
- `bbox_relative` must be `[ymin, xmin, ymax, xmax]`, integers 0–1000, **relative to the crop**, tight to
  the visible pixels.

**Expected output:**

```json
{
  "wearing": [{
    "category": "clothing | accessory | footwear | jewelry",
    "type": "specific item name",
    "color": "dominant color",
    "pattern": "solid | striped | checked | printed | null",
    "brand": null,
    "gender": "male | female | unisex | null",
    "bbox_relative": [0, 0, 1000, 1000]
  }],
  "carrying": [{
    "category": "bag | accessory | object",
    "type": "specific item name",
    "color": "dominant color",
    "pattern": null,
    "brand": null,
    "gender": null,
    "bbox_relative": [0, 0, 1000, 1000]
  }]
}
```

Rules the prompt states: held items → `carrying`; worn items → `wearing`; never invent brands; never
include background objects; always include `bbox_relative`; return a best guess rather than dropping an
item.

## `OBJECT_PROMPT`

Used by `analyze_object_mode` when no person is detected. Returns a **single object**, not a list:

```json
{
  "category": "bag | accessory | footwear | clothing | object",
  "type": "specific object name",
  "color": "dominant color",
  "pattern": "solid | striped | checked | printed | null",
  "brand": null,
  "gender": "male | female | unisex | null"
}
```

`category` is required and must never be null. Note there is **no `bbox_relative`** here — object mode
takes its box from Cloud Vision or falls back to a fixed centre rectangle.

`analyze_object_mode` normalises a dict response to a single-element list before processing.

## Fields the code consumes

`choose_best_bbox` extracts a fixed key set from every Gemini item:

```python
{k: obj.get(k) for k in ("category","type","subtype","color","shade","brand","gender","pattern")}
```

> **`subtype` and `shade` are read but neither prompt asks for them.** They will be `None` unless the
> model volunteers them. Both are then used by product matching — `shade` is merged into the colour
> filter list. This is a latent mismatch between prompt and consumer.

The final item object adds three computed fields:

| Field | Source |
| ----- | ------ |
| `bbox` | `choose_best_bbox` — may be `null` |
| `relation` | `"wearing"` or `"carrying"` (person mode) |
| `confidence` | `"precise"` / `"approximate"` / `"none"` |

## Response cleaning

Gemini output is not reliably bare JSON, so [`vision_service.clean_json`](../../backend/app/services/vision_service.py)
normalises it:

```python
text = re.sub(r"```(?:json)?|```", "", text).strip()   # strip markdown fences
text = re.sub(r",\s*([\]\}])", r"\1", text)            # remove trailing commas
match = re.search(r"(\{.*\}|\[.*\])", text, flags=re.DOTALL)
return match.group(1).strip() if match else "{}"
```

Greedy matching takes the outermost braces or brackets, discarding prose before and after. If
`json.loads` still fails, `describe` prints the parse error and the raw response, then returns `{}` — a
**successful** call that yields no items.

## Cloud Vision output

```python
{ "label": "<lowercased name>",
  "bbox_norm": { "x1": min_x, "y1": min_y, "x2": max_x, "y2": max_y },   # 0.0–1.0
  "score": 0.87 }
```

Entries whose label contains `"person"` are filtered out — the person box comes from YOLO.

## Coordinate conversions

Three spaces are in play: normalised (Vision, 0–1), relative (Gemini, 0–1000), and resized pixels.

```python
# Vision → resized pixels
x1 = person_bbox["x1"] + int(norm["x1"] * crop_width)

# Gemini → resized pixels
x1 = person_bbox["x1"] + int(xmin * crop_width / 1000)
```

Both are then clamped with `clamp_box_to_image` and validated by `valid_bbox`, which requires
`0 <= x1 < x2 <= w`.

## `describe_with_vision_fallback` — defined but unused

`vision_service` also defines a combined helper returning
`{vision_detection, gemini_attributes, localization_source, confidence}`. **No caller exists** —
`decision_engine` calls `describe` and `localize_objects` separately and arbitrates itself. Documented
only so it is not mistaken for the live path.

## Phase 2 prompts

`app/core/models_prompt.py` and `photo_prompts.py` support the Phase 2 model/look flow. That feature is
under active development, and its prompt contracts are **not verified from the current implementation**.
See [../features/phase2-models.md](../features/phase2-models.md).

## Changing a prompt safely

The prompt output shape is load-bearing. If you edit `PERSON_PROMPT` or `OBJECT_PROMPT`:

1. Keep the `wearing` / `carrying` top-level keys — `analyze_person_mode` iterates them by name.
2. Keep `bbox_relative` as `[ymin, xmin, ymax, xmax]` on 0–1000 — `gemini_relative_to_resized` assumes it.
3. Keep the eight consumed attribute keys, or update `choose_best_bbox`.
4. Remember that `type` (not `category`) is the value used as the product-search category filter — see
   [vector-search.md](vector-search.md).
5. There is no schema validation and no test suite, so a breaking change surfaces only as empty results.

## Known limitations

1. **No structured-output enforcement** — correctness relies on prompt discipline plus regex cleanup.
2. **A parse failure is indistinguishable from "nothing detected"** — both yield an empty item list with
   `Code 0`.
3. **`subtype` and `shade` are consumed but never requested.**
4. **The `"makeup"` synonym entry is malformed** — one comma-joined string instead of three members, so it
   cannot match. See [image-analysis-pipeline.md](image-analysis-pipeline.md).
5. **No prompt versioning** — prompts are module constants with no history or A/B capability, and
   `prompts copy.py` sits alongside the live file as an unused duplicate.
