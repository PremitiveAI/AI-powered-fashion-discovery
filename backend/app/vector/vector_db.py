from typing import List
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from app.config.env import env

from importlib.metadata import version
print("Qdrant client version:", version("qdrant-client"))
# Initialize Qdrant in embedded mode (local folder storage)
VECTOR_DB_DIR = env("VECTOR_DB_DIR")
client = QdrantClient(path=VECTOR_DB_DIR)

print("✅ Qdrant client initialized with storage at:", VECTOR_DB_DIR)

# Load embedding model (adjust if you use another)
embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

# Ensure collection exists
def init_collection(collection_name="products", vector_size=768):
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE
        )
    )


# 1. Initialize collection
init_collection("products")


# info = client.get_collection("products") 
# print("Total vectors in collection:", info.vectors_count)
count = client.count(collection_name="products", exact=True) 
print("Total points:", count.count)

# Save a new product vector
def save_vector(collection_name, product: dict):

    # Normalize values 
    product["gender"] = product["gender"].lower() 
    product["category_name"] = product["category"]["name"].lower() 
    product["pattern_name"] = product["pattern"]["name"].lower() if product.get("pattern") else ""
    product["subtype_name"] = product["subtype"]["name"].lower() if product.get("subtype") else ""
    product["brand_names"] = [b["name"].lower() for b in product["brands"]] 
    product["color_names"] = [c["name"].lower() for c in product["colors"]]
    
    # Build searchable text
    text = (         
        f"product name: {product['name']} / " 
        f"gender: {product['gender']} / " 
        f"category: {product['category']['name']} / " 
        f"pattern: {product['pattern_name']} / "
        f"subtype: {product['subtype_name']} / " f"brands: {', '.join([b['name'] for b in product['brands']])} / " 
        f"colors: {', '.join([c['name'] for c in product['colors']])} / " 
        f"intro: {product['product_intro']} / " 
        f"description: {product['description']} / " 
        f"specification: {product['specification']}" 
    )

    vector = embedder.encode(text).tolist()

    print("save product =============================> ", product)
    # Save product
    client.upsert(
        collection_name=collection_name,
        points=[
            models.PointStruct(
                id=product["id"],
                vector=vector,
                payload=product # keep full metadata
            )
        ]
    )
    return f"✅ Saved product {product['id']}"


# Update an existing product vector
def update_vector(collection_name, product: dict):
    return save_vector(collection_name, product)


# Search for similar products
def search_vector(collection_name, query: str, limit: int = 10 ):
    query_vector = embedder.encode(query).tolist()
    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit
    )
    return results


# Delete a product vector
def delete_vector(collection_name: str, product_id: int):
    client.delete(
        collection_name=collection_name,
        points_selector=models.PointIdsList(
            points=[product_id]
        )
    )
    return f"🗑️ Deleted product {product_id}"


# Search With products Filter
def filter_search_vector(
    query: str,
    limit: int = 10,
    brands: list[str] = None,
    colors: list[str] = None,
    gender: str = None,
    categories: list[str] = None,
    patterns: list[str] = None,
    subtypes:list [str] = None,
    collection_name: str="products", 
):
    
    # print("query =====> ", query)
    # print("brands =====> ", brands)
    # print("colors =====> ", colors)
    # print("gender =====> ", gender)
    # print("categories =====> ", categories)

    query_vector = embedder.encode(query).tolist()
    conditions = []

    if brands:
        conditions.append(models.FieldCondition(
            key="brand_names",
            match=models.MatchAny(any=[b.lower() for b in brands])
        ))

    if colors:
        conditions.append(models.FieldCondition(
            key="color_names",
            match=models.MatchAny(any=[c.lower() for c in colors])
        ))

    if gender:
        conditions.append(models.FieldCondition(
            key="gender",
            match=models.MatchValue(value=gender.lower())
        ))

    if categories:
        # conditions.append(models.FieldCondition(
        #     key="category_name",
        #     match=models.MatchAny(any=[c.lower() for c in categories])
        # ))
        conditions.append(models.FieldCondition(
            key="category_name",
            match=models.MatchValue(value=categories.lower())
        ))
        
    # if patterns:
    #     conditions.append(models.FieldCondition(
    #         key="pattern_name",
    #         match=models.MatchValue(value=patterns.lower())
    #     ))
        
    # if subtypes:
    #     conditions.append(models.FieldCondition(
    #         key="subtype_name",
    #         match=models.MatchValue(value=subtypes.lower())
    #     ))

    query_filter = models.Filter(must=conditions) if conditions else None

    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        query_filter=query_filter,
        limit=limit
    )

    return results








# # 1. Initialize collection
# init_collection("products")

# 2. Save product
# product = {
#     "id": 10,
#     "name": "Adidas Dryfit Puma T-Shirt",
#     "description": "Black Puma with Dryfit technology",
#     "price": 1299.00,
#     "mrp": 1599.00,
#     "gender": "male",
#     "category": {"id":2,"name":"T-Shirt"},
#     "brand": [{"id":1,"name":"Puma"}],
#     "color": [{"id":1,"name":"Black"}, {"id":2,"name":"red"}],
#     "status": 1
# }
# print(save_vector("products", product))

# # 3. Search
# results = search_vector("products", "black color polo t-shirt")
# print("results =========> ", results)
# for r in results:
#     print(f"Found: =====================> {r.payload['id']} (score={r.score:.4f})")

# # 4. Update
# product["price"] = 1199.00
# print(update_vector("products", product))

# # 5. Delete
# print(delete_vector("products", 10))


