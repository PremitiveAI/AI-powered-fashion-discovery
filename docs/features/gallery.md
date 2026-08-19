# Feature — Image Gallery

Multi-file image upload and listing. Gallery rows are what products reference for their imagery.

**Status:** ✅ Complete.

## Business purpose

Products need pictures, and those pictures need stable IDs. The gallery is the intermediate step: upload
once, get an ID, reference that ID from any number of products. It is also the source of the garment
images used by [virtual try-on](virtual-try-on.md).

## User flow

Reached from `/uploade` and `/add-product` — select one or more images, upload, then pick from the
resulting list when creating a product.

## Frontend flow

```
→ POST /api/image-upload      (multipart, repeatable field: files)
→ POST /gallery/upload
→ response: { uploaded, failed, results[], errors[] }
```

## Backend flow

```
POST /gallery/upload   (files: List[UploadFile])
  ↓ ProductController.upload
      guard: if not files → Code 4000
      admin_id = getattr(request.state, "adminUserId", 1)
      for each file:
          try:  process_single_file(db, admin_id, file)   → results[]
          except: failed.append({filename, ercategoryror})  ← note the typo
  ↓ success_response("Files uploaded successfully",
        { uploaded, failed, results, errors })

POST /gallery/list
  ↓ galleryList(db, payload)  →  { total, records }
  ↓ success_response(..., { totalRecords, list: [gallery_response(db, r) …] })
```

## API details

`POST /gallery/upload` · `POST /gallery/list` — full reference:
[../api/products-and-gallery.md](../api/products-and-gallery.md#post-galleryupload).

## Request

**Upload** — `multipart/form-data`, field `files`, repeatable.

**List** — `galleryList` schema: the standard `search` / `sort` / `order` / `limit` / `offset` payload.

## Response

```json
{
  "Success": { "message": "Files uploaded successfully",
    "data": { "uploaded": 2, "failed": 0, "results": [ … ], "errors": [] } },
  "Code": 0, "Error": null
}
```

List responses wrap in `{ totalRecords, list }`, and each row exposes `image_url` built as
`BASE_URL + imagePath.lstrip("/")` — so `BASE_URL` must end with a slash or the URLs are malformed.

## Validation

| Rule | Failure |
| ---- | ------- |
| At least one file | `Code 4000` |

**No file type, size or dimension validation.** Any file is accepted and written to disk.

## Business rules

- A **partial success is still `Code 0`** — per-file exceptions are collected into `errors[]` and the
  batch continues. Clients must inspect `failed` and `errors`, not just the response code.
- Gallery IDs returned here are exactly what `POST /product/save` expects in its `images` array, and
  they are validated there against `tbl_admin_gallery`.

## Database interaction

| Table | Operation |
| ----- | --------- |
| `tbl_admin_gallery` | INSERT per file; SELECT for listing |

Columns: `imagePath` (String 1024), `title`, `type`, `mimeType`, `fileSizeMB`, `status`, plus audit
columns and `created_by_user` / `updated_by_user` relationships to `AdminUsers`.

Files are written under `uploads/`, which is served by `app.mount("/uploads", StaticFiles(...))`.

## Authentication

`PK-apiToken` only. `admin_id` resolves to `1`.

## Error handling

| Situation | Result |
| --------- | ------ |
| No files | `Code 4000` |
| Per-file failure | Collected in `errors[]`; batch continues; response is still `Code 0` |
| Disk write failure | Caught per file |

> The failure branch builds `{"filename": …, "ercategoryror": str(e)}` — a typo'd key. A client reading
> `error` finds nothing. Worth fixing when that file is next touched.

## Dependencies

`python-multipart`, `gallery_service.process_single_file`, `STORAGE_DIR`.

## Known limitations

1. **Uploaded images are publicly downloadable** — `/uploads` is exempt from token verification in the
   auth middleware. [AUDIT.md](../../AUDIT.md) issue 9.
2. **No file validation** of any kind — type, size or content.
3. **The error key is misspelled** (`ercategoryror`), so client-side error display silently shows
   nothing.
4. **No delete endpoint.** `tbl_admin_gallery` has `status`, `deletedBy` and `deletedAt` columns but no
   route sets them — images cannot be removed through the API.
5. **No deduplication** — uploading the same file twice creates two rows and two files.
6. **Nothing prunes `uploads/`.**
