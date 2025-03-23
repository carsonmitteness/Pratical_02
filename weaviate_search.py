import weaviate
import ollama

client = weaviate.Client("http://localhost:8080")

CLASS_NAME = "DocumentChunk"

def get_embedding(text: str, model: str = "nomic-embed-text") -> list:
    response = ollama.embeddings(model=model, prompt=text)
    return response["embedding"]

def search_embeddings(query, top_k=3):
    query_embedding = get_embedding(query)

    near_vector = {
        "vector": query_embedding,
        "certainty": 0.7  # Adjust certainty as needed
    }

    results = client.query\
        .get(CLASS_NAME, ["file", "page", "chunk"])\
        .with_near_vector(near_vector)\
        .with_limit(top_k)\
        .do()

    top_results = []
    for result in results["data"]["Get"][CLASS_NAME]:
        top_results.append({
            "file": result["file"],
            "page": result["page"],
            "chunk": result["chunk"],
            "similarity": result["_additional"]["certainty"]
        })

    return top_results

def generate_rag_response(query, context_results):
    context_str = "\n".join(
        [
            f"From {result.get('file', 'Unknown file')} (page {result.get('page', 'Unknown page')}, chunk {result.get('chunk', 'Unknown chunk')}) "
            f"with similarity {float(result.get('similarity', 0)):.2f}"
            for result in context_results
        ]
    )

    print(f"context_str: {context_str}")

    prompt = f"""You are a helpful AI assistant. 
    Use the following context to answer the query as accurately as possible. If the context is 
    not relevant to the query, say 'I don't know'.

Context:
{context_str}

Query: {query}

Answer:"""

    response = ollama.chat(
        model="mistral:latest", messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]

def interactive_search():
    print("🔍 RAG Search Interface")
    print("Type 'exit' to quit")

    while True:
        query = input("\nEnter your search query: ")

        if query.lower() == "exit":
            break

        context_results = search_embeddings(query)
        response = generate_rag_response(query, context_results)

        print("\n--- Response ---")
        print(response)

if __name__ == "__main__":
    interactive_search()