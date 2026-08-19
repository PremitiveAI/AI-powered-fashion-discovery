# Feature — Stores

CRUD for physical store locations, with coordinates captured via Ola Maps reverse geocoding.

**Status:** ✅ Complete.

## Business purpose

Bridges online discovery and physical retail: once a shopper has matched a product, stores are where
they could go and buy it. The `products_id` column exists to express that link.

## User flow

1. **Add Store** (`/add-store`) — fill in the form. The page calls Ola Maps reverse-geocode to resolve
   coordinates into an address.
2. **Store List** (`/store-list`) — browse, view details, delete.

## Frontend flow

```
/add-store
  → browser geolocation → lat/lng
  → GET https://api.olamaps.io/places/v1/reverse-geocode?latlng=…&api_key=…   (direct, client-side)
  → POST /api/add-store          → store/save

/store-list
  → POST   /api/store-list        → store/list
  → GET    /api/store-detail/[id] → store/details/{id}
  → DELETE /api/store-delete/[id] → store/delete/{id}
```

> `/api/store-list`, `/api/store-delete` and `/api/product-list` use `axios` and **unwrap the envelope**,
> returning `{message, data}` rather than `{Success, Code, Error}`. Those pages therefore consume a
> different response shape from the rest of the application. See
> [../architecture/frontend-architecture.md](../architecture/frontend-architecture.md).

## Backend flow

`store_routes.py` → `StoreController` (311 lines, queries models directly — **no service layer**, unlike
products and masters).

## API details

| Method | Path | Purpose |
| ------ | ---- | ------- |
| POST | `/store/save` | Create or update |
| POST | `/store/list` | Paginated list |
| GET | `/store/details/{store_id}` | Single store |
| DELETE | `/store/delete/{store_id}` | Soft delete |

Full reference: [../api/stores.md](../api/stores.md).

## Request

`StoreCreate` — fields map to the `tbl_stores` columns:

| Field | Type | Notes |
| ----- | ---- | ----- |
| `id` | int, optional | Present → update |
| `store_name` | string | **NOT NULL** in the model |
| `address` | string(500) | |
| `city`, `state`, `pincode`, `phone`, `email`, `website` | string | |
| `latitude`, `longitude` | **Float** | From Ola Maps reverse geocoding |
| `store_type` | string(20) | **NOT NULL** |
| `products_id` | string(255) | Comma-separated product IDs — **no foreign key** |

> Exact per-field Pydantic constraints are **not verified from the current implementation** —
> `store_schema.py` was not read line-by-line. Column types above are verified from `stores_model.py`.

## Response

```json
{ "Success": { "message": "List fetched successfully",
               "data": { "totalRecords": 7, "list": [ … ] } },
  "Code": 0, "Error": null }
```

## Database interaction

| Table | Operation |
| ----- | --------- |
| `tbl_stores` | INSERT / UPDATE / SELECT / soft delete |

`latitude` and `longitude` are plain `Float` columns with **no spatial index** and no distance query
anywhere in the backend.

## Authentication

`PK-apiToken` only.

## Two unrelated notions of "store"

This is the most important thing to understand about the feature, and it is easy to miss:

| | Source | Coordinates | Surfaced on |
| - | ------ | ----------- | ----------- |
| **Managed stores** | `tbl_stores` via `/store/*` | Entered at creation | `/store-list` |
| **Nearby stores** | **Ola Maps Places API, live** | Browser geolocation | `/ola-map` |

`/api/nearby-stores` queries `https://api.olamaps.io/places/v1/nearbysearch` with
`types=clothing_store` and never touches the backend or `tbl_stores`. The map therefore shows
real-world shops from Ola's index — **not the stores in your database**.

See [nearby-stores.md](nearby-stores.md).

## Known limitations

1. **`products_id` is a comma-separated string** with no foreign key — no integrity, and truncation at
   255 characters.
2. **No geospatial querying.** Despite storing coordinates, there is no "stores near me" over
   `tbl_stores`; that is delegated entirely to Ola Maps against a different dataset.
3. **Managed stores and matched products are never connected**, despite `products_id` existing for
   exactly that purpose. A shopper cannot go from a matched product to a store that stocks it.
4. **No service layer** — `store_controller.py` queries models directly, inconsistent with the rest of
   the backend.
5. **Two frontend handlers unwrap the envelope**, so store pages parse responses differently from
   everything else.
