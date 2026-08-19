# Feature — Product Catalogue

CRUD for products, with automatic synchronisation into the Qdrant vector index so every saved product
becomes searchable by image.

**Status:** ✅ Complete.

## Business purpose

The catalogue is what image search matches against. A product is not merely a database row — saving one
also writes its embedding, so the quality and coverage of this data directly determines whether image
search returns anything useful.

## User flow

1. **Collection → Add Product** (`/add-product`) — fill in the form, choosing category, brands, colours
   and gallery images from dropdowns.
2. **Product List** (`/product-list`) — browse, view details, delete.

## Frontend flow

```
/add-product
  → POST /api/master/category-list   → master/category/list     (dropdown)
  → POST /api/master/brand-list      → master/brand/list         (dropdown)
  → POST /api/master/color-list      → master/color/list         (dropdown)
  → POST /api/product-type           → master/product/list       (dropdown)
  → POST /api/image-upload           → gallery/upload            (image IDs)
  → POST /api/product-add            → product/save

/product-list
  → POST   /api/product-list          → product/list
  → GET    /api/product-details/[id]  → product/get/{id}
  → DELETE /api/product-delete/[id]   → product/delete/{id}
```

> Two dropdowns cannot populate: `/api/master/pattern` and `/api/master/sub-type` target
> `master/pattern/list` and `master/subtype/list`, neither of which exists in the backend.
> [AUDIT.md](../../AUDIT.md) issue 10.

## Backend flow

```
POST /product/save
  ↓ ProductController.save
      gender → str (Enum unwrapped)
      admin_id = getattr(request.state, "adminUserId", 1)
      validate category_id exists                    → Code 4000
      validate every brand_id  exists (IN query)     → Code 4000 listing missing ids
      validate every color_id  exists                → Code 4000
      validate every image id  exists in AdminGallery→ Code 4000
      brand_id / color_id / images → list_to_comma_string(...)
  ↓ ProductService.create_master  |  update_master   (id present → update)
  ↓ _master_response(db, obj, saveVector=True)
      build product dict, resolving category / brands / colours to names
      save_vector("products", product)               → Qdrant upsert
```

## API details

`POST /product/save` · `POST /product/list` · `GET /product/get/{product_Id}` ·
`DELETE /product/delete/{product_Id}`

Full reference: [../api/products-and-gallery.md](../api/products-and-gallery.md).

## Validation

Referential validation happens **before any write**, and names the offending IDs:

```json
{ "Success": null, "Code": 4000, "Error": { "message": "Brand IDs [7, 9] do not exist" } }
```

Variants: `"Category with id 3 does not exist"`, `"Color IDs [...] do not exist"`,
`"Image IDs [...] do not exist"`.

This is genuinely good — it prevents dangling references despite the absence of real foreign keys.

## Business rules

| Rule | Where |
| ---- | ----- |
| `id` present → update; absent → create | `ProductController.save` |
| `gender` is lower-cased before indexing | `save_vector` |
| Category, brand and colour **names** (not IDs) go into the embedding text | `save_vector` |
| The Qdrant point ID **is** the PostgreSQL product ID | `save_vector` |
| The full product dict is stored as the Qdrant payload | `save_vector` |

That last rule is why search results can return product fields without a second database query.

## Database interaction

| Table | Operation |
| ----- | --------- |
| `tbl_products` | INSERT / UPDATE / SELECT / soft delete |
| `tbl_master_categories`, `tbl_master_brands`, `tbl_master_colors`, `tbl_admin_gallery` | SELECT for validation and name resolution |
| Qdrant `products` | UPSERT on save |

### The comma-separated column problem

`pattern_id`, `subtype_id`, `category_id`, `subcategory_id`, `brand_id`, `color_id` and `images` are all
`String(255)` holding comma-joined IDs.

Consequences: no referential integrity at the database level, no usable index, and **silent truncation
at 255 characters** — a product with many brands, colours or images loses the overflow.
[AUDIT.md](../../AUDIT.md) issue 13.

## Authentication

`PK-apiToken` only. `createdBy`/`updatedBy` resolve to `1` in practice.

## Error handling

| Situation | Result |
| --------- | ------ |
| Missing category / brand / colour / image | `Code 4000`, IDs listed |
| Product not found on get/delete | `Code 4000` |
| Qdrant unreachable | Exception → HTTP 500 |

## Known limitations

1. **Deleting a product does not remove its vector.** The `delete_vector` call in
   `ProductService.delete` is commented out, so deleted products keep appearing in image-search results.
   [AUDIT.md](../../AUDIT.md) issue 20.
2. **All vectors are lost on backend restart** — `recreate_collection` runs at import. Every product
   must be re-saved before search works again. [AUDIT.md](../../AUDIT.md) issue 3.
3. **No bulk import** and **no re-index command** — repopulating means calling `POST /product/save` once
   per product.
4. **ID lists truncate at 255 characters.**
5. **Pattern and sub-type cannot be set from the UI** — the dropdowns have no backend.
6. **Category naming is load-bearing.** Image search filters on the detected `type` (`t-shirt`), not the
   coarse `category` (`clothing`), so master categories must be named for garment types or nothing
   matches. See [../ai/vector-search.md](../ai/vector-search.md).
