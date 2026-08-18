# services/vector_db.py - UPDATED VERSION
import os
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from app.config.env import env
import hashlib

GOOGLE_API_KEY = env("GOOGLE_API_KEY").strip().removeprefix('"').removesuffix('"')

# Create embeddings model
embedder = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    api_key=GOOGLE_API_KEY
)

# Ensure storage folder exists
PERSIST_DIR = "./chroma_store"
os.makedirs(PERSIST_DIR, exist_ok=True)

# Create Chroma DB instance
chroma_db = Chroma(
    collection_name="pdf_chunks",
    embedding_function=embedder,
    persist_directory=PERSIST_DIR
)

def store_document(text: str, file_hash: str = None, metadata: dict = None):
    """
    Stores a chunk into vector DB with source information.
    
    Args:
        text: The text content
        file_hash: PDF file hash (to track source)
        metadata: Additional metadata about the document
    """
    try:
        # Create document with metadata
        doc_metadata = metadata or {}
        if file_hash:
            doc_metadata["file_hash"] = file_hash
            doc_metadata["source"] = f"pdf_{file_hash}"
        
        # Create document object
        document = Document(
            page_content=text,
            metadata=doc_metadata
        )
        
        # Store in vector DB
        ids = chroma_db.add_documents([document])
        # chroma_db.persist()
        return ids
    except Exception as e:
        print(f"❗ Warning: failed to store document: {e}")
        return None

def search_vectors(query: str):
    """
    Performs similarity search for the query.
    Returns documents with metadata including file_hash.
    """
    try:
        results = chroma_db.similarity_search_with_score(query, k=3)
        
        # Extract documents with metadata
        documents = []
        for doc, score in results:
            documents.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            })
        
        return {"documents": documents}
    except Exception as e:
        print(f"❗ Warning: vector search failed: {e}")
        return {"documents": []}

def get_file_hash_from_text(text: str):
    """
    Try to extract file_hash from vector search results.
    Returns the most common file_hash in search results.
    """
    results = search_vectors(text)
    file_hashes = {}
    
    for doc in results["documents"]:
        file_hash = doc["metadata"].get("file_hash")
        if file_hash:
            file_hashes[file_hash] = file_hashes.get(file_hash, 0) + 1
    
    # Return the most frequent file_hash
    if file_hashes:
        return max(file_hashes, key=file_hashes.get)
    return None