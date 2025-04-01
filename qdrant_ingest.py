from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
import fitz
import os
import numpy as np
import ollama

client = QdrantClient(host="localhost", port=6333)
collection_name = "pdf_documents"

client.recreate_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
)

def get_embedding(text: str, model: str = "nomic-embed-text") -> list:
    response = ollama.embeddings(model=model, prompt=text)
    return response["embedding"]

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text_by_page = []
    for page_num, page in enumerate(doc):
        text_by_page.append((page_num, page.get_text()))
    return text_by_page

def split_text_into_chunks(text, chunk_size=300, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
    return chunks

def ingest_pdf_to_qdrant(data_dir):
    point_id = 0
    for file_name in os.listdir(data_dir):
        if file_name.endswith(".pdf"):
            pdf_path = os.path.join(data_dir, file_name)
            text_by_page = extract_text_from_pdf(pdf_path)
            for page_num, text in text_by_page:
                chunks = split_text_into_chunks(text)
                for chunk in chunks:
                    embedding = get_embedding(chunk)
                    client.upsert(
                        collection_name=collection_name,
                        points=[{
                            "id": point_id,
                            "vector": embedding,
                            "payload": {
                                "file": file_name,
                                "page": page_num,
                                "chunk": chunk
                            }
                        }]
                    )
                    point_id += 1
            print(f"Processed {file_name}")

ingest_pdf_to_qdrant("data")
