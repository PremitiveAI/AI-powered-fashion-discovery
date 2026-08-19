# Feature — Image Search

Upload a photograph; get back every fashion item detected in it, each with extracted attributes and up
to three matching products from the catalogue.

**Status:** ✅ Complete. This is the product's core feature.

## Business purpose

The shortest path from "I like that outfit" to "here is where you buy it". A shopper photographs a
person or a garment and the system identifies each item and surfaces comparable inventory — no search
terms, no filters, no category browsing.

## User flow

1. Navigate to **Collection → Upload Collection**… no — **`/uploade`** via the sidebar.
2. Drop or select a photograph.
3. The image is analysed; detected items appear with their attributes and matched products.
4. A Google Map renders on the same page for store context.

## Frontend flow

```
/uploade page
  → POST /api/search              (multipart, field: file)
  → POST /product/search
  → response: Success.data[] — one entry per detected person or object
  → render items, each with its product_list
```

The page also loads the Google Maps JS SDK via
`https://maps.googleapis.com/maps/api/js?key=${NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&libraries=marker`.

## Backend flow

```
POST /product/search   (file: UploadFile)
  ↓ ProductController.search
  guard: if not file → Code 4000
  contents = await file.read()
  ↓ gemini_is_safe_tryon(contents)         NSFW gate → Code 4002 on failure
  ↓ analyze_image(contents)                YOLO → Gemini → Vision → bbox arbitration
  ↓ for each detected group:
        ProductService.search_products_for_items(items)   → attaches product_list
  ↓ save_local_file2(admin_id, filename, contents)        → storage/{admin_id}/
  ↓ ProductService.save_history(db, image_path, enriched_data, admin_id)
  ↓ success_response("Files uploaded successfully", enriched_data)
```

Pipeline internals: [../ai/image-analysis-pipeline.md](../ai/image-analysis-pipeline.md) and
[../ai/vector-search.md](../ai/vector-search.md).

## API details

`POST /product/search` — **Content-Type:** `multipart/form-data`, **field:** `file`.

Full request/response documentation:
[../api/products-and-gallery.md](../api/products-and-gallery.md#post-productsearch).

## Response

```json
{
  "Success": { "message": "Files uploaded successfully",
    "data": [{
      "person_id": "person_1",
      "input_type": "person",
      "bbox": { "x1": 120, "y1": 40, "x2": 480, "y2": 900 },
      "crop_ref": "/crops/person_1.jpg",
      "debug_url": "http://127.0.0.1:8000/debug/<uuid>.jpg",
      "items": [{
        "category": "clothing", "type": "t-shirt", "subtype": null,
        "color": "black", "shade": null, "brand": null,
        "gender": "male", "pattern": "solid",
        "bbox": { "x1": 150, "y1": 200, "x2": 420, "y2": 520 },
        "relation": "wearing", "confidence": "precise",
        "product_list": [ /* up to 3 products */ ]
      }]
    }] },
  "Code": 0, "Error": null
}
```

Object mode (no person detected) returns `object_id` / `input_type: "object"` and omits the group-level
`bbox`, `crop_ref` and `debug_url`.

## Validation

| Layer | Rule | Failure |
| ----- | ---- | ------- |
| Controller | A file must be present | `Code 4000` |
| Controller | `gemini_is_safe_tryon` must pass | `Code 4002` |
| `decode_image` | Bytes must decode as an image | `ValueError` → HTTP 500 |

**File type and size are not validated.** Any upload reaching `cv2.imdecode` either decodes or raises.

## Database interaction

| Table | Operation |
| ----- | --------- |
| `tbl_search_history` | INSERT — `imagePath` and the serialised enriched result |
| Qdrant `products` | SELECT (filtered vector search), once per unique detected item |

> `search_result` is `String(2048)`. Realistic enriched payloads exceed it, so the history insert can
> fail with `StringDataRightTruncation`. [AUDIT.md](../../AUDIT.md) issue 14.

## Authentication

`PK-apiToken` only. `admin_id` comes from `getattr(request.state, "adminUserId", 1)` — effectively
always `1`, so all searches are attributed to the same user and stored under `storage/1/`.

## Error handling

| Situation | Result |
| --------- | ------ |
| No file | `Code 4000` |
| Unsafe image | `Code 4002` |
| Undecodable bytes | HTTP 500 |
| Cloud Vision failure | Silently caught — pipeline degrades to Gemini-only boxes |
| Gemini failure | HTTP 500 |
| No products match | `product_list: []` — a **successful** response |

## Dependencies

`ultralytics` (YOLOv8s), `opencv-python`, `langchain-google-genai`, `google-cloud-vision`,
`sentence-transformers`, `qdrant-client`, `requests`.

## Known limitations

1. **Empty results are common and silent.** Vector filters are AND-only, so an unrecognised brand or
   colour yields zero matches rather than approximate ones. See
   [../ai/vector-search.md](../ai/vector-search.md).
2. **The index is wiped on every backend restart**, so search returns nothing until products are
   re-saved. [AUDIT.md](../../AUDIT.md) issue 3.
3. **Only the largest person is analysed** — `persons[:1]`.
4. **Earrings and rings always return `bbox: null`** — the small-item landmark gate can never pass.
5. **Search history may fail to save** on long results.
6. **No pagination or ranking control** — `limit=3` per item is hard-coded.
7. **Latency is unbounded** — two Google API calls plus one embedding and one Qdrant query per unique
   item, with no timeout or retry.
