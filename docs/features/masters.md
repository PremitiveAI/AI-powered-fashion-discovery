# Feature — Masters

Reference data: categories, sub-categories, colours and brands. **17 endpoints** — the largest router in
the application.

**Status:** ✅ Complete (API); partially wired to the UI.

## Business purpose

Master data is not decoration here — it is the vocabulary image search matches against. Each product's
Qdrant payload stores the **lower-cased master names** (`brand_names`, `color_names`, `category_name`),
and `filter_search_vector` filters on exactly those. If Gemini reports a colour or brand that has no
corresponding master record, the query returns **zero** results.

## User flow

Master records are created through Swagger or direct API calls — **the frontend calls only the four
list endpoints**, to populate dropdowns on `/add-product`. There is no master-management screen.

## Frontend flow

```
/add-product
  → POST /api/master/category-list      → master/category/list
  → POST /api/master/brand-list         → master/brand/list
  → POST /api/master/color-list         → master/color/list
  → POST /api/product-type              → master/product/list
  → POST /api/master/pattern            → master/pattern/list   ❌ no backend route
  → POST /api/master/sub-type           → master/subtype/list   ❌ no backend route
```

## Backend flow

`master_routes.py` → `MasterController` → `master_service.py` → model.

## API details

Four master types with an identical four-endpoint shape, plus one product-type list:

| Master | Save | List | Delete | Details |
| ------ | ---- | ---- | ------ | ------- |
| Category | `POST /master/category/save` | `POST /master/category/list` | `DELETE /master/category/delete/{id}` | `GET /master/category/details/{id}` |
| Sub-category | `POST /master/subcategory/save` | `POST /master/subcategory/list` | `DELETE /master/subcategory/delete/{id}` | `GET /master/subcategory/details/{id}` |
| Colour | `POST /master/color/save` | `POST /master/color/list` | `DELETE /master/color/delete/{id}` | `GET /master/color/details/{id}` |
| Brand | `POST /master/brand/save` | `POST /master/brand/list` | `DELETE /master/brand/delete/{id}` | `GET /master/brand/details/{id}` |
| Product type | — | `POST /master/product/list` | — | — |

Full reference: [../api/masters.md](../api/masters.md).

## Request

**Save** — `Category` schema, shared by category, colour and brand:

```json
{ "id": null, "name": "T-Shirt", "description": "Short-sleeved upper garment" }
```

Sub-category uses `SubCategory`, which adds `category_id`.

**List** — the standard `UserListReq` payload.

## Validation

| Rule | Failure |
| ---- | ------- |
| `name` required and non-blank | "Name is required" |
| Record must exist on update / delete / details | "Record not found" |

## Business rules

- `id` present → update; absent → create.
- Deletion is **soft** — `status` and `deletedAt` are set; rows are never removed.
- Master names are lower-cased when written into a product's Qdrant payload.

## Database interaction

| Table | Notes |
| ----- | ----- |
| `tbl_master_categories` | `subcategories` relationship (back_populates) |
| `tbl_master_sub_categories` | `category_id` FK → categories; `category` relationship |
| `tbl_master_colors`, `tbl_master_brands`, `tbl_master_product_types` | Identical shape |
| `tbl_master_patterns`, `tbl_master_subtypes` | **Tables exist; no route exposes them** |

All carry `created_by_user` / `updated_by_user` `selectin` relationships to `AdminUsers`.

## Authentication

`PK-apiToken` only. No session, no role check — anyone with the token can create or delete master data.

## Error handling

Standard envelope with `Code: 4030` for validation and `Code: 4040` for not-found, returned with
HTTP 200.

## Known limitations

1. **Two masters have no API.** `tbl_master_patterns` and `tbl_master_subtypes` are created at startup
   and referenced by `tbl_products` (`pattern_id`, `subtype_id`), but no route can manage them — so the
   pattern and sub-type dropdowns never populate. [AUDIT.md](../../AUDIT.md) issue 10.
2. **`tbl_master_product_types` is read-only** — a list endpoint with no save or delete.
3. **No master-management UI.** Save, delete and details have no frontend caller.
4. **Category naming is load-bearing.** Because image search filters on the detected garment `type`,
   categories must be named for specific types (`T-Shirt`, `Jeans`) rather than broad buckets
   (`Clothing`), or matching silently fails. This constraint is invisible from the API and is the most
   common cause of empty search results.
5. **Soft deletes leave stale vectors.** Deleting a brand or colour does not update the products that
   reference it, nor their Qdrant payloads.
