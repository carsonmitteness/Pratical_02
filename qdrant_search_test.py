from qdrant_ingest import get_embedding
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
collection_name = "pdf_documents"


def search_qdrant(query: str, top_k: int = 3):
    query_embedding = get_embedding(query)

    search_result = client.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=top_k,
    )

    results = []
    for point in search_result:
        results.append({
            "id": point.id,
            "file": point.payload.get("file"),
            "page": point.payload.get("page"),
            "chunk": point.payload.get("chunk"),
            "score": point.score
        })
        print(f"File: {point.payload.get('file')}, Page: {point.payload.get('page')}, Score: {point.score}")

    return results

results = search_qdrant("How can I balance an AVL tree?")
