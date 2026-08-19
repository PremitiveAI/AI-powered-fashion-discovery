# Feature — Nearby Stores

A map of clothing shops near the user, sourced live from the Ola Maps Places API.

**Status:** ✅ Complete. **Entirely frontend** — the backend is not involved.

## Business purpose

Closes the loop from discovery to purchase: having matched a product, show the shopper where clothing
retailers are around them.

## User flow

1. Open **`/ola-map`**.
2. The browser requests geolocation permission.
3. Nearby clothing stores render on an Ola Maps view.

## Frontend flow

This is the only feature in the application that **does not touch FastAPI**:

```
/ola-map page
  → browser geolocation → { lat, lng }
  → POST /api/nearby-stores  { lat, lng }
        ↓ (server-side route handler)
        GET https://api.olamaps.io/places/v1/nearbysearch
              ?location={lat},{lng}&radius=5000&types=clothing_store
              header: X-API-Key: NEXT_PUBLIC_OLA_MAPS_API_KEY
        ↓ for each prediction:
        GET https://api.olamaps.io/places/v1/details?place_id={place_id}
              header: X-API-Key
        ↓ Promise.all → stores[]
  → render markers
```

Two calls per result — `nearbysearch` returns predictions without precise coordinates, so `details` is
fetched per place to obtain lat/lng.

## API details

**No backend endpoint.** The `/api/nearby-stores` route handler calls Ola Maps directly.

| Parameter | Value | Source |
| --------- | ----- | ------ |
| `location` | `{lat},{lng}` | Browser geolocation |
| `radius` | `5000` (metres) | **Hard-coded** |
| `types` | `clothing_store` | **Hard-coded** |

## Request / Response

**Request to the handler:** `{ "lat": 19.076, "lng": 72.8777 }`

**Response:** `{ "places": [ … ] }`. On any upstream failure the handler returns
`{ "places": [] }` with HTTP 200 — a silent empty result rather than an error.

## Validation

**None.** `lat` and `lng` are passed through to Ola Maps without range or type checking.

## Business rules

- Radius fixed at 5 km.
- Only `clothing_store` results.
- No pagination — whatever `nearbysearch` returns in one page is what renders.

## Database interaction

**None.** Nothing is persisted; results are fetched fresh on every page load.

## Authentication

**None** — neither `PK-apiToken` nor a session. The handler is a thin proxy to Ola Maps.

## The disconnect from managed stores

Worth stating plainly, because the naming invites confusion:

| | Source | Shows |
| - | ------ | ----- |
| `/store-list` | `tbl_stores` via `/store/*` | **Your** stores |
| `/ola-map` | Ola Maps Places API | **Real-world** shops from Ola's index |

The map does **not** show the stores in your database, and there is no reconciliation between the two.
`tbl_stores` holds `latitude`, `longitude` and a `products_id` column that could support "which of my
stores near you stocks this product" — but no code joins those ideas. See [stores.md](stores.md).

## Error handling

| Situation | Result |
| --------- | ------ |
| `nearbysearch` fails | `console.error`, returns `{ places: [] }` |
| A `details` call fails | Caught per place; that store is dropped |
| Geolocation denied | **Not verified from the current implementation** — the page was not read line-by-line |
| Missing API key | Ola Maps returns 401; handler returns an empty list |

Every failure path produces an empty map rather than a message, so a missing key and "no shops nearby"
are indistinguishable to the user.

## Dependencies

`olamaps-web-sdk` (installed and used), `NEXT_PUBLIC_OLA_MAPS_API_KEY`.

## Known limitations

1. **The API key ships to the browser.** `NEXT_PUBLIC_OLA_MAPS_API_KEY` is `NEXT_PUBLIC_`-prefixed, so
   Next.js inlines it into the client bundle — even though `nearby-stores/route.ts` is **server-side**
   and could have used a private variable. Restrict the key by HTTP referrer in the Ola console.
   [AUDIT.md](../../AUDIT.md) security item S5.
2. **N+1 upstream calls** — one `details` request per result, all fired concurrently. A dense area
   means dozens of API calls per page load, with no caching.
3. **All failures are silent** — the user sees an empty map.
4. **Radius and type are hard-coded**; there is no way to widen the search or change the category.
5. **No connection to `tbl_stores`**, so the feature cannot answer the question it looks like it
   answers.
6. `add-store` calls Ola Maps **reverse-geocode directly from the page** with the key in the query
   string, a second exposure path.
