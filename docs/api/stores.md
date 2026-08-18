# Stores API

Router: `store_router` (`/store`), defined in
[`app/routes/store_routes.py`](../../backend/app/routes/store_routes.py), implemented in
[`store_controller.py`](../../backend/app/controllers/store_controller.py) (311 lines — it queries models
directly, with no service layer).

All require `PK-apiToken`.

## Summary

| Method | Path | Purpose |
| ------ | ---- | ------- |
| POST | `/store/save` | Create or update a store |
| POST | `/store/list` | Paginated list |
| GET | `/store/details/{store_id}` | Single store |
| DELETE | `/store/delete/{store_id}` | Soft delete |

## POST `/store/save`

**Schema:** `StoreCreate` in [`store_schema.py`](../../backend/app/schemas/store_schema.py).

Fields correspond to the `tbl_stores` columns:

| Field | Type | Notes |
| ----- | ---- | ----- |
| `id` | int, optional | Supplying it updates |
| `store_name` | string | **NOT NULL** in the model |
| `address` | string(500) | |
| `city`, `state`, `pincode` | string | |
| `phone`, `email` | string | |
| `latitude`, `longitude` | **Float** | Populated by the frontend from Ola Maps reverse geocoding |
| `store_type` | string(20) | **NOT NULL** |
| `website` | string(255) | |
| `products_id` | string(255) | Comma-separated product IDs — no foreign key |

> Exact per-field Pydantic constraints (required vs optional, lengths) were **not verified from the
> current implementation** — `store_schema.py` was not read line-by-line. The column types above are
> verified from [`stores_model.py`](../../backend/app/models/stores_model.py).

## POST `/store/list`

**Schema:** `StoreListRequest`. Standard list payload — `search`, `sort`, `order`, `limit`, `offset`.

```json
{ "Success": { "message": "List fetched successfully",
               "data": { "totalRecords": 7, "list": [ … ] } },
  "Code": 0, "Error": null }
```

## GET `/store/details/{store_id}` · DELETE `/store/delete/{store_id}`

Single fetch and soft delete (`status`, `deletedAt`). A missing record returns a not-found code.

---

## Relationship to the nearby-stores feature

There are **two independent notions of "store"** in this application, and they are not connected:

| | Source | Coordinates | Used by |
| - | ------ | ----------- | ------- |
| **Managed stores** | `tbl_stores` via `/store/*` | Entered at creation, geocoded through Ola Maps reverse-geocode on `/add-store` | `/store-list` |
| **Nearby stores** | **Ola Maps Places API**, live | From the user's browser geolocation | `/ola-map` |

`/api/nearby-stores` calls `https://api.olamaps.io/places/v1/nearbysearch` with
`types=clothing_store` and a 5 km radius, then fetches `places/v1/details` for each result. **It never
touches the backend or `tbl_stores`.**

So the map shows real-world clothing shops from Ola's index, not the stores in your database. Linking
the two — for example, resolving a nearby result to a managed store, or showing which managed stores
carry a matched product via `products_id` — is **not implemented**.

See [../features/nearby-stores.md](../features/nearby-stores.md) and
[../integrations/ola-maps.md](../integrations/ola-maps.md).

## Frontend usage

| Endpoint | BFF handler | Page |
| -------- | ----------- | ---- |
| `/store/save` | `/api/add-store` | `/add-store` |
| `/store/list` | `/api/store-list` | `/store-list` |
| `/store/details/{id}` | `/api/store-detail/[id]` | `/store-list` |
| `/store/delete/{id}` | `/api/store-delete/[id]` | `/store-list` |

`/api/store-list`, `/api/store-delete` and `/api/product-list` use `axios` and **unwrap the envelope**,
returning `{message, data}` rather than `{Success, Code, Error}` — those pages consume a different shape
from the rest of the application. See
[../architecture/frontend-architecture.md](../architecture/frontend-architecture.md).

## Known limitations

1. **`products_id` is a comma-separated string** with no foreign key, so store↔product links have no
   integrity and are truncated at 255 characters.
2. **No geospatial querying.** `latitude`/`longitude` are plain Floats with no index and no distance
   search — "stores near me" is delegated entirely to Ola Maps.
3. **No link between managed stores and matched products**, despite `products_id` existing.
4. **No service layer** — `store_controller.py` queries models directly, unlike products and masters.
