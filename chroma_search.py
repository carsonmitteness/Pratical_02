import redis
import chromadb
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import ollama


# all-MiniLM-L6-v2
# embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_or_create_collection(name="embedding_index")


VECTOR_DIM = 768
INDEX_NAME = "embedding_index"
DOC_PREFIX = "doc:"
DISTANCE_METRIC = "COSINE"


LLM = "deepseek-r1" # "mistral:latest", "deepseek-r1"
EMBEDDING_MODEL = "nomic-embed-text" # "nomic-embed-text", "mxbai-embed-large"


# def cosine_similarity(vec1, vec2):
#     """Calculate cosine similarity between two vectors."""
#     return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))




def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> list:


   response = ollama.embeddings(model=model, prompt=text)
   return response["embedding"]




def search_embeddings(query, top_k=5):


   query_embedding = get_embedding(query)


   results = collection.query(
       query_embeddings=[query_embedding], 
       n_results=top_k
       )


   # Transform results into the expected format
   top_results = [
       {
           "file": meta["file"],
           "page": meta["page"],
           "chunk": meta["chunk"],
           "similarity": distance
       }
       for meta, distance in zip(results["metadatas"][0], results["distances"][0])
   ]


   return top_results






def generate_rag_response(query, context_results):


   # Prepare context string
   context_str = "\n".join(
       [
           f"From {result.get('file', 'Unknown file')} (page {result.get('page', 'Unknown page')}, chunk {result.get('chunk', 'Unknown chunk')}) "
           f"with similarity {float(result.get('similarity', 0)):.2f}"
           for result in context_results
       ]
   )


   print(f"context_str: {context_str}")


   # Construct prompt with context
   prompt = f"""You are a helpful AI assistant.
   Use the following context to answer the query as accurately as possible. If the context is
   not relevant to the query, say 'I don't know'.


Context:
{context_str}


Query: {query}


Answer:"""


   # Generate response using Ollama
   response = ollama.chat(
       model=LLM, messages=[{"role": "user", "content": prompt}]
   )


   return response["message"]["content"]




def interactive_search():
   """Interactive search interface."""
   print("🔍 RAG Search Interface")
   print("Type 'exit' to quit")


   while True:
       query = input("\nEnter your search query: ")


       if query.lower() == "exit":
           break


       # Search for relevant embeddings
       context_results = search_embeddings(query)


       # Generate RAG response
       response = generate_rag_response(query, context_results)


       print("\n--- Response ---")
       print(response)




# def store_embedding(file, page, chunk, embedding):
#     """
#     Store an embedding in Redis using a hash with vector field.


#     Args:
#         file (str): Source file name
#         page (str): Page number
#         chunk (str): Chunk index
#         embedding (list): Embedding vector
#     """
#     key = f"{file}_page_{page}_chunk_{chunk}"
#     redis_client.hset(
#         key,
#         mapping={
#             "embedding": np.array(embedding, dtype=np.float32).tobytes(),
#             "file": file,
#             "page": page,
#             "chunk": chunk,
#         },
#     )




if __name__ == "__main__":
   interactive_search()
