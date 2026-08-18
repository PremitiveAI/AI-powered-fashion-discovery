# Masters API

Router: `master_router` (`/master`), defined in
[`app/routes/master_routes.py`](../../backend/app/routes/master_routes.py), implemented in
[`master_controller.py`](../../backend/app/controllers/master_controller.py) and
[`master_service.py`](../../backend/app/services/master_service.py).

All require `PK-apiToken`. **17 endpoints.**

## Summary

Four master types follow the same four-endpoint shape, plus one product-type list:

| Master | Save | List | Delete | Details |
| ------ | ---- | ---- | ------ | ------- |
| Category | `POST /master/category/save` | `POST /master/category/list` | `DELETE /master/category/delete/{id}` | `GET /master/category/details/{id}` |
| Sub-category | `POST /master/subcategory/save` | `POST /master/subcategory/list` | `DELETE /master/subcategory/delete/{id}` | `GET /master/subcategory/details/{id}` |
| Colour | `POST /master/color/save` | `POST /master/color/list` | `DELETE /master/color/delete/{id}` | `GET /master/color/details/{id}` |
| Brand | `POST /master/brand/save` | `POST /master/brand/list` | `DELETE /master/brand/delete/{id}` | `GET /master/brand/details/{id}` |
| Product type | — | `POST /master/product/list` | — | — |

## Request shapes

**Save** — `Category` schema (also used for colour and brand):

```json
{ "id": null, "name": "T-Shirt", "description": "Short-sleeved upper garment" }
```

Supplying `id` updates; omitting it creates.

**Sub-category save** — `SubCategory` schema adds the parent:

```json
{ "id": null, "name": "Polo", "description": "…", "category_id": 2 }
```

**List** — `UserListReq`, all fields optional:

```json
{ "search": "", "filter": "", "startDate": null, "endDate": null,
  "sort": "createdAt", "order": "DESC", "limit": 10, "offset": 0 }
```

`search` performs a case-insensitive `ILIKE %value%` on `name`.

## Response shapes

**List:**

```json
{ "Success": { "message": "List fetched successfully",
    "data": { "total": 12,
      "list": [{ "id": 2, "name": "T-Shirt", "description": "…",
                 "status": 1,
                 "createdAt": "18-Aug-2026 07:05:52",
                 "updatedAt": "18-Aug-2026 07:05:52" }] } },
  "Code": 0, "Error": null }
```

**Details / Save:** a single object of the same shape. Sub-category responses additionally carry the
parent `category` via the model's `selectin` relationship.

**Delete:**

```json
{ "Success": { "message": "Deleted successfully" }, "Code": 0, "Error": null }
```

Deletion is soft — `status` and `deletedAt` are set; rows are never removed.

## Validation

| Rule | Failure |
| ---- | ------- |
| `name` required and non-blank | `Code 4030`-style "Name is required" from the service |
| Record must exist on update, delete and details | "Record not found" |
| `category_id` on sub-category | **Not verified from the current implementation** — the controller was not read line-by-line for this check |

## Why masters matter for image search

Master data is not merely reference data here — it directly determines whether image search returns
anything.

`filter_search_vector` applies `must` (AND) conditions on `brand_names`, `color_names`, `gender` and
`category_name`, matching against the **lower-cased master names** stored in each product's Qdrant
payload. If Gemini reports a colour or brand that has no corresponding master record on the product, the
query returns zero results.

Two practical consequences:

1. **Name categories after garment types.** The category filter uses the detected `type`
   (`t-shirt`, `jeans`), not the coarse `category` (`clothing`). A master category called "Clothing"
   will never match.
2. **Cover the colour and brand vocabulary** your users will photograph, since brand and colour filters
   use `MatchAny` over the values Gemini returns.

See [../ai/vector-search.md](../ai/vector-search.md).

## Two masters with no API

| Table | Model file | Status |
| ----- | ---------- | ------ |
| `tbl_master_patterns` | [`pattern_model.py`](../../backend/app/models/pattern_model.py) | **No route exposes it.** The frontend calls `master/pattern/list`, which does not exist |
| `tbl_master_subtypes` | [`subtype_model.py`](../../backend/app/models/subtype_model.py) | **No route exposes it.** The frontend calls `master/subtype/list`; the backend has `master/subcategory/list` |

Both tables are created at startup and both are referenced by `tbl_products` (`pattern_id`,
`subtype_id`), but neither can be managed through the API. The pattern and sub-type dropdowns in the UI
therefore never populate. [AUDIT.md](../../AUDIT.md) issue 10.

`tbl_master_product_types` is read-only through `POST /master/product/list` — there is no save or delete.

## Frontend usage

| Endpoint | BFF handler | Used by |
| -------- | ----------- | ------- |
| `/master/category/list` | `/api/master/category-list` | `/add-product`, `/uploade` |
| `/master/brand/list` | `/api/master/brand-list` | `/add-product` |
| `/master/color/list` | `/api/master/color-list` | `/add-product` |
| `/master/product/list` | `/api/product-type` | `/add-product` |
| `master/pattern/list` | `/api/master/pattern` | ❌ backend route missing |
| `master/subtype/list` | `/api/master/sub-type` | ❌ backend route missing |

The save, delete and details endpoints are **not called by the frontend** — master data is currently
created through Swagger or direct API calls.
