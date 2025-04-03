import chromadb
import ollama
import numpy as np
import os
import fitz
from utils.timer import timer

# new imports
from memory_profiler import profile
import string
import re
from sentence_transformers import SentenceTransformer


# Initialize chromadb connection
chroma_client = chromadb.HttpClient(host="localhost", port=8000)




CHUNK_SIZE = 500
OVERLAP = 100
EMBEDDING_MODEL = "all-minilm" # "nomic-embed-text", "mxbai-embed-large", "all-minilm"
TEXT_PROCESS = True


VECTOR_DIM = 768
INDEX_NAME = "embedding_index"
DOC_PREFIX = "doc:"
DISTANCE_METRIC = "COSINE"


# Global collection variable (to be initialized in `create_index`)
collection = None




# Clear the ChromaDB collection
def clear_chroma_store():
   print("Clearing existing ChromaDB store...")
   try:
       chroma_client.get_collection(INDEX_NAME)  # Check if the collection exists
       chroma_client.delete_collection(INDEX_NAME)
       print("Chroma store cleared.")
   except chromadb.errors.NotFoundError:
       pass




# Create a ChromaDB collection
def create_index():
   global collection  # Ensure `collection` is accessible throughout the script
   collection = chroma_client.get_or_create_collection(name=INDEX_NAME)
   print("Index created successfully.")




# Generate an embedding using nomic-embed-text
def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> list:
   response = ollama.embeddings(model=model, prompt=text)
   return response["embedding"]




# Store embeddings in ChromaDB
def store_embedding(file: str, page: str, chunk: str, embedding: list):
   """Stores an embedding in ChromaDB with metadata."""
   collection.add(
       embeddings=[embedding],  
       metadatas=[{"file": file, "page": page, "chunk": chunk}],  
       ids=[f"{file}_page_{page}_chunk_{chunk}"], 
   )
   print(f"Stored embedding for: {chunk}")




# Extract text from a PDF
def extract_text_from_pdf(pdf_path):
   """Extract text from a PDF file."""
   doc = fitz.open(pdf_path)
   text_by_page = []
   for page_num, page in enumerate(doc):
       text_by_page.append((page_num, page.get_text()))
   return text_by_page




# Split text into chunks with overlap
def split_text_into_chunks(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
   """Split text into chunks of approximately chunk_size words with overlap."""
   words = text.split()
   chunks = []
   for i in range(0, len(words), chunk_size - overlap):
       chunk = " ".join(words[i : i + chunk_size])
       chunks.append(chunk)
   return chunks


def clean_text(text):
    # Remove punctuation 
    text = text.translate(str.maketrans("", "", string.punctuation))
    # Remove any extra whitespace
    text = re.sub(r'\s+', ' ', text).strip() 
    return text


# Process PDFs and store embeddings with the ability to process text (remove white space and punctuation)
def process_pdfs(data_dir, text_process=TEXT_PROCESS):
   for file_name in os.listdir(data_dir):
       if file_name.endswith(".pdf"):
           pdf_path = os.path.join(data_dir, file_name)
           text_by_page = extract_text_from_pdf(pdf_path)
           for page_num, text in text_by_page:
                if text_process:
                    text = clean_text(text)
                chunks = split_text_into_chunks(text)
                for chunk_index, chunk in enumerate(chunks):
                   embedding = get_embedding(chunk)
                   store_embedding(
                       file=file_name,
                       page=str(page_num),
                       chunk=str(chunk),
                       embedding=embedding,
                   )
           print(f" -----> Processed {file_name}")




# Process text documentation files  with the ability to process text (remove white space and punctuation)
def process_documentation_folder(data_dir, text_process=TEXT_PROCESS):
   print(f"path = {data_dir}")
   doc_folder = f"{data_dir}/documentation"
   folder_contents = [f for f in os.listdir(doc_folder) if not f.startswith('.')]


   for doc_file in folder_contents:
       file_name = f'{doc_folder}/{doc_file}'
       with open(file_name, "r") as file:
           file_content = file.read()
           if text_process:
               file_content = clean_text(file_content)
           chunks = split_text_into_chunks(file_content)
           for chunk_index, chunk in enumerate(chunks):
               embedding = get_embedding(chunk)
               store_embedding(
                   file=file_name,
                   page="0",
                   chunk=str(chunk),
                   embedding=embedding,
               )
           print(f" -----> Processed {file_name}")




# Query ChromaDB for similar embeddings
def query_chroma(query_text: str, top_k=5):
   embedding = get_embedding(query_text) 
   results = collection.query(
       query_embeddings=[embedding],  
       n_results=top_k
   )


   # Extract and print results
   for i, (meta, distance) in enumerate(zip(results["metadatas"][0], results["distances"][0])):
       print(f"{i+1}. File: {meta['file']}, Page: {meta['page']}, Chunk: {meta['chunk']}")
       print(f"   Similarity Score: {distance:.4f}\n")


   return results


@timer
@profile
def main():
   data_folder = "data"


   clear_chroma_store()
   create_index()


   process_pdfs(data_folder)
   process_documentation_folder(data_folder)
   print("\n---Done processing PDFs---\n")





if __name__ == "__main__":
   main()