# Integration — Ola Maps

Location services for the store features: finding nearby clothing shops, and turning a map pin into an
address.

**This is a frontend-only integration.** The backend never calls Ola Maps and holds no Ola credentials.

## Configuration

| Variable | Where used | Prefix |
| -------- | ---------- | ------ |
| `NEXT_PUBLIC_OLA_MAPS_API_KEY` | `app/api/nearby-stores/route.ts`, `app/(auth)/add-store/page.tsx` | `NEXT_PUBLIC_` |

Package: `olamaps-web-sdk` `^1.1.0 <1.2.0` (resolved 1.1.4) — used for map rendering in
`add-store/page.tsx`.

> `frontend/README.md` also lists a non-prefixed `OLA_MAPS_API_KEY`. **Nothing reads it.** Only the
> `NEXT_PUBLIC_` form is used — see [../setup/frontend-setup.md](../setup/frontend-setup.md).

## 🔴 The API key is exposed to the browser

Next.js inlines every `NEXT_PUBLIC_*` variable into the **client JavaScript bundle at build time**. The
key is readable by anyone who loads the site — no authentication, no devtools skill required.

This matters twice over:

1. **`add-store/page.tsx` genuinely needs a client-side key.** The reverse-geocode call and the map SDK
   both run in the browser, so the key *must* be public there.
2. **`api/nearby-stores/route.ts` does not.** It is a server-side Route Handler that could read a
   private, unprefixed variable — but it reads the `NEXT_PUBLIC_` one, publishing a key that had no
   reason to leave the server.

Ola Maps keys are billed per request, so an exposed key is a spend liability, not just an information
leak.

**Mitigation** (no code change has been made):

- Restrict the key by HTTP referrer in the Ola console.
- Introduce a separate server-only `OLA_MAPS_API_KEY` for `nearby-stores`, keeping the public key
  scoped to the map SDK alone.

See [../setup/environment-variables.md](../setup/environment-variables.md).

## Usage 1 — Nearby search (server-side)

`frontend/app/api/nearby-stores/route.ts`

```
GET https://api.olamaps.io/places/v1/nearbysearch
      ?location={lat},{lng}&radius=5000&types=clothing_store
      header: X-API-Key: <key>
```

Then, **for each prediction**:

```
GET https://api.olamaps.io/places/v1/details?place_id={place_id}
      header: X-API-Key: <key>
```

The second call exists because `nearbysearch` returns predictions without precise coordinates; `details`
supplies them so pins can be placed.

**This is an N+1 pattern**: one search plus one call per result. Twenty results means twenty-one billed
requests for a single map view. Nothing caches, batches or deduplicates them.

| Parameter | Value | Configurable |
| --------- | ----- | ------------ |
| `radius` | `5000` (metres) | ❌ hard-coded |
| `types` | `clothing_store` | ❌ hard-coded |
| Pagination | none | — |

Because `types` is fixed, the feature can only ever find clothing shops — a deliberate scope, but one
that cannot be changed without editing the handler.

Feature detail: [../features/nearby-stores.md](../features/nearby-stores.md).

## Usage 2 — Reverse geocoding (client-side)

`frontend/app/(auth)/add-store/page.tsx`

```
GET https://api.olamaps.io/places/v1/reverse-geocode?latlng={lat},{lng}&api_key=<key>
```

Note the different authentication style: this call passes the key as a **query parameter**, while
`nearby-stores` uses the **`X-API-Key` header**. Both are valid for Ola Maps, but the inconsistency is
worth knowing when debugging a 401 — the two call sites fail differently.

Used when the operator drops a pin while creating a store, to prefill the address fields.

## Usage 3 — Map rendering

`olamaps-web-sdk` renders the interactive map in `add-store`. It authenticates with the same public key.

## Failure modes

| Failure | Behaviour |
| ------- | --------- |
| Key missing | `undefined` is cast with `as string` and sent — Ola returns 401 |
| Key invalid / quota exceeded | `nearbysearch` non-OK → `console.error`, handler returns `{ places: [] }` |
| A single `details` call fails | That one result is dropped; the rest still render |
| Network failure | Same as above — empty list |
| Browser denies geolocation | No search is attempted at all |

Every failure produces **an empty map with no message**. The user cannot distinguish "no shops nearby"
from "the integration is broken". There is no error toast, no retry and no logging beyond
`console.error`.

The `as string` cast is worth calling out: TypeScript is being told the variable exists rather than being
asked to check, so a missing key produces a runtime 401 instead of a build-time or startup error.

## Cost

| Action | Ola Maps requests |
| ------ | ----------------: |
| One nearby-stores view | 1 + N (one per result) |
| One pin drop in add-store | 1 |
| Map load | SDK tile requests |

With the key public and unrestricted, third parties can drive this bill.

## Known limitations

1. **The key ships to the browser** and is used even where it need not be.
2. **N+1 request pattern** on every nearby search.
3. **`radius` and `types` are hard-coded.**
4. **No caching** — revisiting the page re-runs every call.
5. **Two different auth styles** across two call sites.
6. **Silent failure** — broken and empty look identical.
7. **No pagination**, so results are capped at whatever one page returns.
8. **The backend has its own unrelated store feature** (`tbl_store`, `/store/*`) which never touches Ola
   Maps. The two notions of "store" do not interact — see [../features/stores.md](../features/stores.md).
