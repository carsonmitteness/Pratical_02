from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
import ollama
import numpy as np

collection_name = "pdf_documents"
client = QdrantClient(host="localhost", port=6333)


def get_embedding(text: str, model: str = "nomic-embed-text") -> list:
    """Generate an embedding for the given text using Ollama."""
    response = ollama.embeddings(model=model, prompt=text)
    return response["embedding"]


def search_qdrant(query: str, top_k: int = 3):
    """Search the Qdrant collection for the closest matches to the query embedding."""
    query_embedding = get_embedding(query)

    search_result = client.query_points(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=top_k,
    )

    results = []
    for point in search_result:
        results.append({
            "id": point.id,
            "file": point.payload.get("file", "Unknown file"),
            "page": point.payload.get("page", "Unknown page"),
            "chunk": point.payload.get("chunk", "Unknown chunk"),
            "score": point.score,
        })
        print(f"File: {point.payload.get('file')}, Page: {point.payload.get('page')}, Score: {point.score}")

    return results


def generate_rag_response(query: str, context_results):
    """Generate a response using the retrieved context results."""
    # Context String
    context_str = "\n".join([
        f"From {result.get('file')} (page {result.get('page')}, chunk {result.get('chunk')}) with similarity {result.get('score', 0):.2f}"
        for result in context_results
    ])

    print(f"\nContext for prompt:\n{context_str}\n")

    prompt = f"""You are a helpful AI assistant.
Use the following context to answer the query as accurately as possible. If the context is not relevant to the query, say 'I don't know'.

Context:
{context_str}

Query: {query}

Answer:"""

    # Ollama used but could easily be changed to other LLM for later testing
    response = ollama.chat(
        model="mistral:latest",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]


def interactive_search():
    """Interactive search interface for the Qdrant-backed RAG pipeline."""
    print("🔍 RAG Search Interface (Qdrant)")
    print("Type 'exit' to quit")

    while True:
        query = input("\nEnter your search query: ")
        if query.lower() == "exit":
            break

        context_results = search_qdrant(query)
        response = generate_rag_response(query, context_results)
        print("\n--- Response ---")
        print(response)


def main():
    interactive_search()


if __name__ == "__main__":
    main()
