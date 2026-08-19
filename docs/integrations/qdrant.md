# Integration — Qdrant

The vector store behind product matching. Runs **embedded** — in-process against a local directory,
with no server to install or start.

`qdrant-client==1.9.1`, pinned in `requirements.txt`.

## Configuration

| Item | Value | Source |
| ---- | ----- | ------ |
| Client | `QdrantClient(path=VECTOR_DB_DIR)` | `app/vector/vector_db.py:8` |
| Directory | `VECTOR_DB_DIR` — `qdrant_storage` in `.env` | `backend/.env` |
| Collection | `products` | `init_collection("products")` |
| Vector size | **768** | `init_collection` default |
| Distance | **COSINE** | `models.VectorParams` |
| Embedding model | `sentence-transformers/all-mpnet-base-v2` | loaded at module import |

Embedded mode means Qdrant is a library, not a service. The directory `backend/qdrant_storage/` holds
the collection.

## 🔴 The collection is destroyed on every start

This is the single most disruptive behaviour in the system:

```python
def init_collection(collection_name="products", vector_size=768):
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
    )

init_collection("products")        # ← module scope: runs on EVERY import
```

`recreate_collection` **deletes** an existing collection and creates an empty one. Because the call sits
at module scope, it executes on every application start **and every `--reload` cycle**.

Consequences:

- The product index is empty after every restart.
- Image search returns items with empty `product_list` until every product is re-saved.
- It is **silent** — the following `client.count(...)` simply prints `Total points: 0`.
- Saving a single file during development wipes the index mid-session.

**Workaround until fixed:** after each restart, re-save every product (`POST /product/save`), or comment
out the module-scope `init_collection("products")` call once the collection exists.
[AUDIT.md](../../AUDIT.md) issue 3.

## Indexing

Triggered from `_master_response(db, obj, saveVector=True)` on every product create or update:

```python
product["gender"]        = product["gender"].lower()
product["category_name"] = product["category"]["name"].lower()
product["brand_names"]   = [b["name"].lower() for b in product["brands"]]
product["color_names"]   = [c["name"].lower() for c in product["colors"]]

text = (f"product name: {product['name']} / gender: … / category: … / brands: … / "
        f"colors: … / intro: … / description: … / specification: …")

client.upsert(collection_name, points=[
    models.PointStruct(id=product["id"], vector=embedder.encode(text).tolist(), payload=product)
])
```

Two design choices worth knowing:

- **The point ID is the PostgreSQL product ID**, so upsert is idempotent and updates replace cleanly.
- **The payload is the entire product dict**, including the lower-cased filter keys. Search results
  therefore carry full product data with no second database query.

## Querying

`filter_search_vector(query, brands, colors, gender, categories, limit=3)`:

```python
conditions = []
if brands:     conditions.append(FieldCondition(key="brand_names",   match=MatchAny(any=brands)))
if colors:     conditions.append(FieldCondition(key="color_names",   match=MatchAny(any=colors)))
if gender:     conditions.append(FieldCondition(key="gender",        match=MatchValue(value=gender)))
if categories: conditions.append(FieldCondition(key="category_name", match=MatchValue(value=categories)))

query_filter = Filter(must=conditions) if conditions else None
results = client.search(collection_name, query_vector, query_filter=query_filter, limit=limit)
```

> **All conditions are `must` — a logical AND.** Brand and colour use `MatchAny`, but gender and category
> require an exact match. An unrecognised brand or a colour that is not a master colour yields **zero**
> results rather than degraded ones, and there is no fallback to an unfiltered search.
>
> This is the most common cause of "search found nothing" when the index is populated.

Full retrieval semantics: [../ai/vector-search.md](../ai/vector-search.md).

## Available operations

| Function | Status |
| -------- | ------ |
| `save_vector` / `update_vector` | ✅ used on product create/update |
| `filter_search_vector` | ✅ the live search path |
| `search_vector` | Defined — unfiltered search, not used |
| `delete_vector` | Defined — but the call in `ProductService.delete` is **commented out** |
| `init_collection` | ⚠️ destructive, runs at import |

## Diagnosing

The module prints its state at import and the search path prints every query:

```
✅ Qdrant client initialized with storage at: qdrant_storage
Total points: 0                         ← 0 after every restart is expected, and is the bug
query_text ===== = = ===>  product name: male t-shirt puma black / gender: male / …
<product name> <brands> <colors> <gender> <score>
```

All console-only — none of it reaches `logs/`.

## Operations

| Concern | Reality |
| ------- | ------- |
| Startup | Nothing to start — embedded |
| Persistence | `backend/qdrant_storage/` — **but wiped at every boot** |
| Rebuild | No re-index command; re-save each product via the API |
| Deletion | `delete_vector` exists; the call site is commented out |
| Scaling | Embedded mode does not support concurrent writer processes — two backend instances against one directory is unsupported |
| Backup | Pointless while `recreate_collection` runs at import |

## Known limitations

1. **Index wiped on every start** — fix this before anything else.
2. **AND-only filtering** returns nothing rather than approximate matches.
3. **No score threshold** — the top 3 are returned however poor the similarity.
4. **Deleted products stay searchable** — vector deletion is commented out.
5. **No re-index path** from PostgreSQL.
6. **Text embeddings, not image embeddings** — `all-mpnet-base-v2` is a sentence encoder. Images are
   never embedded; matching compares a *textual description* of the detected item against a *textual
   description* of each product. The `backend/readme` claim of CLIP image embeddings is not implemented.
7. **The embedding model loads at import** (~420 MB), adding startup time and memory to every reload.
