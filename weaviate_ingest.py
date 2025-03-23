import weaviate
import ollama
import os
import fitz
from utils.timer import timer

client = weaviate.Client("http://localhost:8080")

VECTOR_DIM = 768
CLASS_NAME = "DocumentChunk"

def clear_weaviate_store():
    print("Clearing existing Weaviate store...")
    try:
        client.schema.delete_class(CLASS_NAME)
        print("Weaviate store cleared.")
    except weaviate.exceptions.UnexpectedStatusCodeException:
        pass

def create_schema():
    schema = {
        "classes": [
            {
                "class": CLASS_NAME,
                "description": "A chunk of text from a document",
                "vectorizer": "none",
                "properties": [
                    {
                        "name": "file",
                        "dataType": ["string"],
                        "description": "The name of the file",
                    },
                    {
                        "name": "page",
                        "dataType": ["string"],
                        "description": "The page number of the chunk",
                    },
                    {
                        "name": "chunk",
                        "dataType": ["string"],
                        "description": "The text chunk",
                    },
                ],
            }
        ]
    }
    client.schema.create(schema)
    print("Schema created successfully.")

def get_embedding(text: str, model: str = "nomic-embed-text") -> list:
    response = ollama.embeddings(model=model, prompt=text)
    return response["embedding"]

def store_embedding(file: str, page: str, chunk: str, embedding: list):
    data_object = {
        "file": file,
        "page": page,
        "chunk": chunk,
    }
    client.data_object.create(
        data_object,
        CLASS_NAME,
        vector=embedding,
    )
    print(f"Stored embedding for: {chunk}")

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    doc = fitz.open(pdf_path)
    text_by_page = []
    for page_num, page in enumerate(doc):
        text_by_page.append((page_num, page.get_text()))
    return text_by_page

def split_text_into_chunks(text, chunk_size=300, overlap=50):
    """Split text into chunks of approximately chunk_size words with overlap."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
    return chunks

def process_pdfs(data_dir):
    for file_name in os.listdir(data_dir):
        if file_name.endswith(".pdf"):
            pdf_path = os.path.join(data_dir, file_name)
            text_by_page = extract_text_from_pdf(pdf_path)
            for page_num, text in text_by_page:
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

def process_documentation_folder(data_dir):
    print(f"path = {data_dir}")
    doc_folder = f"{data_dir}/documentation"
    folder_contents = [f for f in os.listdir(doc_folder) if not f.startswith('.')]

    for doc_file in folder_contents:
        file_name = f'{doc_folder}/{doc_file}'
        with open(file_name, "r") as file:
            file_content = file.read()
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

def main():
    data_folder = "data"

    clear_weaviate_store()
    create_schema()

    process_pdfs(data_folder)
    process_documentation_folder(data_folder)
    print("\n---Done processing PDFs---\n")

if __name__ == "__main__":
    main()