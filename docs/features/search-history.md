# Feature — Search History

A record of every image search: the uploaded photograph and the enriched analysis result.

**Status:** ✅ Complete (read and write), with a schema constraint that can break writes.

## Business purpose

Lets a user revisit past searches rather than re-uploading, and gives the operator a record of what
shoppers photographed — useful signal for catalogue gaps.

## User flow

**Report → History** … more precisely, the **`/history`** page in the sidebar. It lists past searches;
each row shows the uploaded image and the matched results.

## Frontend flow

```
/history page
  → POST /api/history
  → axios POST `${API_URL.replace(/\/$/, "")}/product/historylist`
  → response consumed as { message, data } (envelope unwrapped by the handler)
```

## Backend flow

Two distinct paths — one writes, one reads.

**Write** — a side effect of every image search:

```
POST /product/search
  … analysis and product matching …
  ↓ image_path = save_local_file2(admin_id, file.filename, contents, False)
        → storage/{admin_id}/
  ↓ ProductService.save_history(db, image_path, enriched_data, admin_id)
        → INSERT tbl_search_history
```

**Read**:

```
POST /product/historylist
  ↓ ProductService.list_search_history(db, payload)     ← called directly from the route,
                                                          bypassing ProductController
```

## API details

`POST /product/historylist` — request is `productListReq` (`search`, `sort`, `order`, `limit`,
`offset`). Full reference:
[../api/products-and-gallery.md](../api/products-and-gallery.md#post-producthistorylist).

## Database interaction

| Table | Operation |
| ----- | --------- |
| `tbl_search_history` | INSERT on every search; SELECT for listing |

| Column | Type | Notes |
| ------ | ---- | ----- |
| `id` | Integer PK, indexed | |
| `imagePath` | String(1024) | Path under `storage/{admin_id}/` |
| `search_result` | **String(2048)** | ⚠️ the serialised enriched result |
| `status` | Integer, default 1 | |

Plus the six audit columns and `created_by_user` / `updated_by_user` relationships.

## ⚠️ The 2048-character problem

`search_result` stores the **entire enriched analysis** — every detected item with its attributes and
bounding box, plus up to three matched products each, and every product carries `id`, `hsn_code`,
`product_code`, `name`, `mrp`, `price`, `gender`, `category`, `brands` and `colors`.

A single detected item with three matches routinely exceeds 2,048 characters on its own. A photograph
with four or five detected items will exceed it several times over.

PostgreSQL **rejects** an over-length value rather than truncating it, so the insert raises
`StringDataRightTruncation`. Because `save_history` runs after the response data is already assembled,
the practical symptom is a search that appears to work but whose history row never lands — or, if the
exception propagates, a 500 on an otherwise successful search.

**Fix:** change the column to `TEXT` or `JSONB`. [AUDIT.md](../../AUDIT.md) issue 14.

## Validation

None specific to this feature. The list payload is the standard shape; the write path performs no
length check before inserting.

## Authentication

`PK-apiToken` only. `createdBy` is `getattr(request.state, "adminUserId", 1)` — always `1` — so history
is global rather than per-user, and every uploaded image lands in `storage/1/`.

## Error handling

| Situation | Result |
| --------- | ------ |
| Result exceeds 2048 chars | `StringDataRightTruncation` from PostgreSQL |
| Image write failure | Propagates from `save_local_file2` |
| Empty history | Standard empty list response |

## Known limitations

1. **Writes fail on realistic payloads** — the `String(2048)` ceiling.
2. **No per-user scoping** — `createdBy` is always `1`, so all history is shared.
3. **No delete endpoint.** `status`, `deletedBy` and `deletedAt` exist on the model but no route sets
   them; history cannot be cleared through the API.
4. **The stored image is never cleaned up** — deleting history (if it existed) would orphan the file,
   and nothing prunes `storage/`.
5. **The result is stored as an opaque string**, not `JSONB`, so it cannot be queried — you cannot ask
   "which products were matched most often".
6. **The route bypasses the controller**, calling `ProductService` directly — inconsistent with the rest
   of the product module.
