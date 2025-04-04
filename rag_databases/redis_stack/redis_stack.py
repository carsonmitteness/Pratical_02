import redis
import numpy as np
from redis.commands.search.query import Query
import os
from utils.timer import timer
from memory_profiler import profile
from utils.constants import INDEX_NAME, DOC_PREFIX, DISTANCE_METRIC, EMBEDDING_DICTIONARY
from utils.text_processing import clean_text, extract_text_from_pdf, split_text_into_chunks, get_embedding
from rag_databases.abstract_rag import AbstractRAG


class RedisRAG(AbstractRAG):
    def __init__(self, chunk_size, overlap, embedding, llm, preprocess, port, show_debug):
        super().__init__(chunk_size, overlap, embedding, llm, preprocess, port, show_debug)
        self.redis_client = redis.Redis(host="localhost", port=port, db=0, decode_responses=True)
    
    # used to clear the redis vector store
    def clear_redis_store(self):
        print("Clearing existing Redis store...")
        self.redis_client.flushdb()
        print("Redis store cleared.")

    # Create an HNSW index in Redis
    def create_hnsw_index(self):
        try:
            self.redis_client.execute_command(f"FT.DROPINDEX {INDEX_NAME} DD")
        except redis.exceptions.ResponseError:
            pass

        print(EMBEDDING_DICTIONARY[self.embedding])

        self.redis_client.execute_command(
            f"""
            FT.CREATE {INDEX_NAME} ON HASH PREFIX 1 {DOC_PREFIX}
            SCHEMA text TEXT
            embedding VECTOR HNSW 6 DIM {EMBEDDING_DICTIONARY[self.embedding]} TYPE FLOAT32 DISTANCE_METRIC {DISTANCE_METRIC}
            """
        )
        print("Index created successfully.")



    # store the embedding in Redis
    def store_embedding(self, file: str, page: str, chunk: str, embedding: list):
        key = f"{DOC_PREFIX}:{file}_page_{page}_chunk_{chunk}"
        self.redis_client.hset(
            key,
            mapping={
                "file": file,
                "page": page,
                "chunk": chunk,
                "embedding": np.array(
                    embedding, dtype=np.float32
                ).tobytes(),  # Store as byte array
            },
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
        doc_folder = f"{data_dir}/documentation"
        folder_contents = [f for f in os.listdir(doc_folder) if not f.startswith('.')]

        for doc_file in folder_contents:
            file_name = f'{doc_folder}/{doc_file}'
            with open(file_name, "r") as file:
                file_content = file.read()
                chunks = split_text_into_chunks(file_content, self.chunk_size, self.overlap)
                if self.preprocess:
                    file_content = clean_text(file_content)

                for chunk_index, chunk in enumerate(chunks):
                        embedding = get_embedding(chunk, self.embedding)
                        self.store_embedding(
                            file=file_name,
                            page="0",
                            chunk=str(chunk),
                            embedding=embedding,
                        )
                print(f" -----> Processed {file_name}")


    def search_embeddings(self, query, top_k=3):

        query_embedding = get_embedding(query, self.embedding)

        # Convert embedding to bytes for Redis search
        query_vector = np.array(query_embedding, dtype=np.float32).tobytes()

        try:
            q = (
                Query("*=>[KNN 5 @embedding $vec AS vector_distance]")
                .sort_by("vector_distance")
                .return_fields("id", "file", "page", "chunk", "vector_distance")
                .dialect(2)
            )

            # Perform the search
            results = self.redis_client.ft(INDEX_NAME).search(
                q, query_params={"vec": query_vector}
            )

            # # Transform results into the expected format
            top_results = [
                {
                    "file": result.file,
                    "page": result.page,
                    "chunk": result.chunk,
                    "similarity": result.vector_distance,
                }
                for result in results.docs
            ][:top_k]


            if(self.show_debug):
                for result in top_results:
                    print('HERE!')
                    print(
                        f"---> File: {result['file']}, Page: {result['page']}, Chunk: {result['chunk']}"
                    )
            
            return top_results

        except Exception as e:
            print(f"Search error: {e}")
            return []

 
    @timer
    @profile   
    def tear_down_and_repopuldate_database(self):
        data_folder = "data"

        self.clear_redis_store()
        self.create_hnsw_index()

        self.process_pdfs(data_folder)
        self.process_documentation_folder(data_folder)



    

    
