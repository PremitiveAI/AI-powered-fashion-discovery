# Feature — Phase 3: Cosmetics & Beauty

Beauty-product browsing and virtual try-on for cosmetics.

**Status:** ❌ **Frontend only — no backend exists.**

## What is built

| Layer | Files | Status |
| ----- | ----- | ------ |
| Pages | `/phase3/home`, `/phase3/beauty-profile`, `/phase3/look-detail` | ✅ built |
| Route handlers | 8 under `frontend/app/api/phase3/` | ✅ built |
| **Backend router** | — | ❌ **does not exist** |
| Database tables | — | ❌ none |

## Why it cannot work

All eight handlers target a `cosmetics/*` router. The backend registers only:

```
/photo   /user   /master   /gallery   /store   /product   /models   /model
```

There is no `/cosmetics` prefix in `backend/app/routes/`, no cosmetics controller, no cosmetics service
and no cosmetics model. Verified by exhaustive search — `grep -rn "cosmetics" backend/` returns nothing
outside the frontend.

Every call 404s.

## The eight orphaned handlers

| Frontend handler | Target |
| ---------------- | ------ |
| `/api/phase3/categories` | `cosmetics/category-list` |
| `/api/phase3/get-categories` | `cosmetics/get-categories` |
| `/api/phase3/save-categories` | `cosmetics/save-categories` |
| `/api/phase3/cosmetic-list` | `cosmetics/cosmetics-list` |
| `/api/phase3/cosmetic-detail` | `cosmetics/cosmetics-detail` |
| `/api/phase3/get-user-photo` | `cosmetics/cosmetics-last-user-photo` |
| `/api/phase3/save-user-photo` | `cosmetics/cosmetics_user-photo` |
| `/api/phase3/user-try-on` | `cosmetics/user-try-on` |

Note the inconsistent naming in the intended contract — `cosmetics-last-user-photo` uses hyphens while
`cosmetics_user-photo` mixes an underscore and a hyphen. Worth settling before implementing.

## Intended shape

The handler names mirror Phase 2 almost exactly, which makes the intent legible:

| Phase 2 | Phase 3 | Purpose |
| ------- | ------- | ------- |
| `models/category-list` | `cosmetics/category-list` | Browse categories |
| `models/models-list` | `cosmetics/cosmetics-list` | List items |
| — | `cosmetics/cosmetics-detail` | Item detail |
| `models/user-photo` | `cosmetics/cosmetics_user-photo` | Save a user photo |
| `models/last-user-photo` | `cosmetics/cosmetics-last-user-photo` | Retrieve it |
| `models/user-try-on` | `cosmetics/user-try-on` | Generate a try-on |
| `models/get-categories` | `cosmetics/get-categories` | Saved preferences |
| `models/save-categories` | `cosmetics/save-categories` | Save preferences |

Phase 3 is Phase 2 applied to makeup rather than clothing. That symmetry is the strongest available
evidence of what the backend should do — but it is **inference, not verified behaviour**, and no
requirement or specification exists in the repository to confirm it.

## API details

**None.** There is no backend API to document.

## Database interaction

**None.** No cosmetics tables exist. Note that the main pipeline's `SYNONYMS` map in
`decision_engine.py` does contain a `"makeup"` entry:

```python
"makeup": {"lipstick, eyeliner, eyeshadow"}
```

That entry is **malformed** — a single comma-joined string rather than three separate set members — so
it can never match a single-word label. It is the only trace of cosmetics anywhere in the backend, and
it does not work. See [../ai/image-analysis-pipeline.md](../ai/image-analysis-pipeline.md).

## Authentication

Not applicable — no request reaches a real endpoint.

## Error handling

Each handler forwards to a URL that returns FastAPI's 404 `{"detail": "Not Found"}`. The pages find no
`Success.data` and render empty — **no crash, no error toast, just permanently blank screens.**

## What implementing it would require

1. **Decide the data model** — a cosmetics catalogue analogous to `tbl_products`, or a distinct shape
   with shade/finish/skin-tone attributes.
2. **Create the router** at `/cosmetics` with the eight endpoints above, settling the naming
   inconsistency first.
3. **Decide the try-on approach.** Garment try-on uses Gemini 2.5 Flash Image with a prompt that
   explicitly restricts input to shirt, t-shirt, pants, jeans or sunglasses. Makeup application is a
   different problem — the existing prompt would need replacing, not extending.
4. **Fix the `makeup` synonym entry** if cosmetics are to be detected by the image pipeline.
5. **Add cosmetics masters** — shade, finish, product type.

## Recommendation

Document as roadmap rather than as a feature, and either implement the router or retire the three pages
and eight handlers. Leaving them in place means three sidebar-reachable screens that silently do
nothing — the worst of both outcomes for anyone evaluating the product.

[AUDIT.md](../../AUDIT.md) issue 8.
