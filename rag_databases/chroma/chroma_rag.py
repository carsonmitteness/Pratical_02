import numpy as np
import chromadb
import os
import ollama
from utils.timer import timer
from memory_profiler import profile
from utils.constants import INDEX_NAME, DOC_PREFIX, DISTANCE_METRIC, EMBEDDING_DICTIONARY
from utils.text_processing import clean_text, extract_text_from_pdf, split_text_into_chunks, get_embedding
from rag_databases.abstract_rag import AbstractRAG

class ChromaRAG(AbstractRAG):
    def __init__(self, chunk_size, overlap, embedding, llm, preprocess, port, show_debug):
        super().__init__(chunk_size, overlap, embedding, llm, preprocess, port, show_debug)
        self.chroma_client = chromadb.HttpClient(host="localhost", port=self.port)
        # TODO: this was previously global but I've moved it to a class variable, if this breaks just change it back
        self.collection = None

    def clear_chroma_store(self):
        print("Clearing existing ChromaDB store...")
        try:
            self.chroma_client.get_collection(INDEX_NAME)  # Check if the collection exists
            self.chroma_client.delete_collection(INDEX_NAME)
            print("Chroma store cleared.")
        except chromadb.errors.NotFoundError:
            pass

    def create_index(self):
        self.collection = self.chroma_client.get_or_create_collection(name=INDEX_NAME)
        print("Index created successfully.")


    def store_embedding(self, file: str, page: str, chunk: str, embedding: list):
        """Stores an embedding in ChromaDB with metadata."""
        self.collection.add(
            embeddings=[embedding],  # Store the vector
            metadatas=[{"file": file, "page": page, "chunk": chunk}],  # Metadata
            ids=[f"{file}_page_{page}_chunk_{chunk}"],  # Unique ID
        )
        print(f"Stored embedding for: {chunk}")

    def process_pdfs(self, data_dir):
        for file_name in os.listdir(data_dir):
            if file_name.endswith(".pdf"):
                pdf_path = os.path.join(data_dir, file_name)
                text_by_page = extract_text_from_pdf(pdf_path)
                for page_num, text in text_by_page:
                        if self.preprocess:
                            text = clean_text(text)
                        chunks = split_text_into_chunks(text, self.chunk_size, self.overlap)
                        for chunk_index, chunk in enumerate(chunks):
                            embedding = get_embedding(chunk, self.embedding)
                            self.store_embedding(
                                file=file_name,
                                page=str(page_num),
                                chunk=str(chunk),
                                embedding=embedding,
                        )
                print(f" -----> Processed {file_name}")

    def process_documentation_folder(self, data_dir):
        print(f"path = {data_dir}")
        doc_folder = f"{data_dir}/documentation"
        folder_contents = [f for f in os.listdir(doc_folder) if not f.startswith('.')]

        for doc_file in folder_contents:
            file_name = f'{doc_folder}/{doc_file}'
            with open(file_name, "r") as file:
                file_content = file.read()
                chunks = split_text_into_chunks(file_content, self.chunk_size, self.overlap)
                for chunk_index, chunk in enumerate(chunks):
                    embedding = get_embedding(chunk, self.embedding)
                    self.store_embedding(
                        file=file_name,
                        page="0",
                        chunk=str(chunk),
                        embedding=embedding,
                    )
                print(f" -----> Processed {file_name}")

    def get_embedding(self, text: str) -> list:

        response = ollama.embeddings(model=self.embedding, prompt=text)
        return response["embedding"]

    def search_embeddings(self, query, top_k=3):

        query_embedding = self.get_embedding(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],  
            n_results=top_k
            )

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

    @timer
    @profile   
    def tear_down_and_repopuldate_database(self):
        data_folder = "data"

        self.clear_chroma_store()
        self.create_index()

        self.process_pdfs(data_folder)
        self.process_documentation_folder(data_folder)

