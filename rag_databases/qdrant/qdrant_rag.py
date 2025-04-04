from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
import os
from utils.timer import timer
from memory_profiler import profile
from utils.constants import EMBEDDING_DICTIONARY
from utils.text_processing import clean_text, extract_text_from_pdf, split_text_into_chunks, get_embedding
from rag_databases.abstract_rag import AbstractRAG


class QDrantRAG(AbstractRAG):
    def __init__(self, chunk_size, overlap, embedding, llm, preprocess, port, show_debug):
        super().__init__(chunk_size, overlap, embedding, llm, preprocess, port, show_debug)
        self.collection_name = "pdf_documents"
        self.client = QdrantClient(host="localhost", port=self.port)


    def create_collection(self):
        vector_size = EMBEDDING_DICTIONARY[self.embedding]
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )

    def ingest_pdf_to_qdrant(self,data_dir):
        point_id = 0
        for file_name in os.listdir(data_dir):
            if file_name.endswith(".pdf"):
                pdf_path = os.path.join(data_dir, file_name)
                text_by_page = extract_text_from_pdf(pdf_path)
                for page_num, text in text_by_page:
                    if self.preprocess:
                        text = clean_text(text)
                    chunks = split_text_into_chunks(text, self.chunk_size, self.overlap)
                    for chunk in chunks:
                        embedding = get_embedding(chunk, self.embedding)
                        self.client.upsert(
                            collection_name=self.collection_name,
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


    def ingest_documentation_to_qdrant(self, data_dir):
        doc_folder = f"{data_dir}/documentation"
        folder_contents = [f for f in os.listdir(doc_folder) if not f.startswith('.')]

        for doc_file in folder_contents:
            file_name = f'{doc_folder}/{doc_file}'
            with open(file_name, "r") as file:
                file_content = file.read()
                if self.preprocess:
                    text = clean_text(text)
                chunks = split_text_into_chunks(text, self.chunk_size, self.overlap)
                for chunk in chunks:
                    embedding = get_embedding(chunk, self.embedding)
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=[{
                            "id": point_id,
                            "vector": embedding,
                            "payload": {
                                "file": file_name,
                                "page": 0,
                                "chunk": chunk
                            }
                        }]
                    )
                    point_id += 1
                print(f"Processed {file_name}")



    def search_embeddings(self,query: str, top_k: int = 3):
        """Search the Qdrant collection for the closest matches to the query embedding."""
        query_embedding = get_embedding(query)

        search_result = self.client.query_points(
            collection_name=self.collection_name,
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


    @timer
    @profile
    def tear_down_and_repopuldate_database(self):
        data_dir = "data"

        self.create_collection()
        self.ingest_pdf_to_qdrant(data_dir)
        self.ingest_documentation_to_qdrant(data_dir)

        # any methods to clear index?

    
