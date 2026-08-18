# Products and Gallery API

Routers: `product_route` (`/product`) and `gallery_router` (`/gallery`), defined in
[`app/routes/product_routes.py`](../../backend/app/routes/product_routes.py), plus
`/product/analyze` from [`app/routes/routes.py`](../../backend/app/routes/routes.py).

All require `PK-apiToken`.

## Summary

| Method | Path | Purpose |
| ------ | ---- | ------- |
| POST | `/product/save` | Create or update a product (also writes the vector) |
| POST | `/product/list` | Paginated list |
| GET | `/product/get/{product_Id}` | Single product |
| DELETE | `/product/delete/{product_Id}` | Soft delete |
| POST | `/product/search` | **Image search — the core AI endpoint** |
| POST | `/product/historylist` | Past searches |
| POST | `/product/analyze` | Raw analysis, no product matching |
| POST | `/gallery/upload` | Multi-file image upload |
| POST | `/gallery/list` | Paginated gallery |

---

## POST `/product/search`

Upload a photograph; receive detected fashion items, each enriched with matching products.

**Content-Type:** `multipart/form-data` · **Field:** `file`

### Behaviour

1. Read the file; reject if absent (`Code 4000`).
2. `gemini_is_safe_tryon(contents)` — NSFW gate; failure returns `Code 4002`.
3. `analyze_image(contents)` — YOLO → Gemini → Cloud Vision → bbox arbitration.
4. For each detected group, `ProductService.search_products_for_items(items)` attaches `product_list`.
5. Save the upload to `storage/{admin_id}/` and insert a `tbl_search_history` row.

### Response

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
        "product_list": [{
          "id": 12, "hsn_code": "…", "product_code": "…", "name": "…",
          "mrp": 1599.0, "price": 1299.0, "gender": "male",
          "category": { "id": 2, "name": "T-Shirt" },
          "brands": ["puma"], "colors": ["black"]
        }]
      }]
    }] },
  "Code": 0, "Error": null
}
```

Object mode (no person detected) returns `object_id` / `input_type: "object"` instead, with no `bbox`,
`crop_ref` or `debug_url` at the group level.

### Notes

- `product_list` is capped at **3** results per item and can be empty — see
  [../ai/vector-search.md](../ai/vector-search.md).
- Items are deduplicated on `(category, type, color, shade, brand, gender)` before matching.
- Earrings and rings always return `bbox: null`.
- Latency is dominated by two Google API calls plus one embedding + Qdrant query per unique item. There
  is no timeout or retry.

Pipeline detail: [../ai/image-analysis-pipeline.md](../ai/image-analysis-pipeline.md).

---

## POST `/product/analyze`

Same analysis, **without** product matching, safety gating, history or file storage. Takes an
`UploadFile` and returns the raw `analyze_image` result.

Registered via `routes.py`, and **not used by the frontend**. Useful for debugging the pipeline in
isolation.

---

## POST `/product/save`

Create (omit `id`) or update (supply `id`).

### Validation — server-side, before any write

```python
category = db.query(MasterCategories).filter(id == payload.category_id).first()
if not category: return error_response(f"Category with id {…} does not exist", code=4000)
# then brand_id, color_id and images are each checked with an IN query
```

Failures name the missing IDs:

```json
{ "Success": null, "Code": 4000, "Error": { "message": "Brand IDs [7, 9] do not exist" } }
```

`gender` is coerced from its Enum to a string. `brand_id`, `color_id` and `images` arrive as arrays and
are stored as **comma-separated strings** ([AUDIT.md](../../AUDIT.md) issue 13).

`createdBy`/`updatedBy` are set to `getattr(request.state, "adminUserId", 1)` — effectively always `1`.

### Side effect — vector indexing

On success `_master_response(..., saveVector=True)` builds the product dict and calls
`save_vector("products", product)`, upserting into Qdrant with the product ID as the point ID and the
full product as the payload. See [../ai/vector-search.md](../ai/vector-search.md).

---

## POST `/product/list`

Standard list payload (`search`, `sort`, `order`, `limit`, `offset`).

```json
{ "Success": { "message": "List fetched successfully",
               "data": { "totalRecords": 42, "list": [ … ] } },
  "Code": 0, "Error": null }
```

## GET `/product/get/{product_Id}` · DELETE `/product/delete/{product_Id}`

Single fetch and soft delete (`status`, `deletedAt`, `updatedBy`).

> **Delete does not remove the vector.** The `delete_vector` call in `ProductService.delete` is
> commented out, so deleted products keep appearing in image-search results until the collection is
> next recreated. [AUDIT.md](../../AUDIT.md) issue 20.

---

## POST `/product/historylist`

Paginated search history from `tbl_search_history`. Called directly from the route on `ProductService`,
bypassing the controller.

Used by `/api/history` → the `/history` page.

---

## POST `/gallery/upload`

**Content-Type:** `multipart/form-data` · **Field:** `files` (repeatable)

Each file goes through `process_single_file`; per-file exceptions are collected rather than aborting the
batch.

```json
{ "Success": { "message": "Files uploaded successfully",
    "data": { "uploaded": 2, "failed": 0, "results": [ … ], "errors": [] } },
  "Code": 0, "Error": null }
```

> The failure branch builds `{"filename": …, "ercategoryror": str(e)}` — a typo'd key. Clients reading
> `error` will find nothing.

Gallery IDs returned here are what `POST /product/save` expects in its `images` array.

## POST `/gallery/list`

```json
{ "Success": { "message": "List fetched successfully",
               "data": { "totalRecords": 18, "list": [ … ] } },
  "Code": 0, "Error": null }
```

Each row exposes `image_url`, built as `BASE_URL + imagePath.lstrip("/")` — so `BASE_URL` must end with
a slash.

---

## Frontend usage

| Endpoint | BFF handler | Page |
| -------- | ----------- | ---- |
| `/product/search` | `/api/search` | `/uploade` |
| `/product/save` | `/api/product-add` | `/add-product` |
| `/product/list` | `/api/product-list` | `/product-list` |
| `/product/get/{id}` | `/api/product-details/[id]` | `/product-list` |
| `/product/delete/{id}` | `/api/product-delete/[id]` | `/product-list` |
| `/product/historylist` | `/api/history` | `/history` |
| `/gallery/upload` | `/api/image-upload` | `/uploade`, `/add-product` |
| `/product/analyze` | — | not used |
