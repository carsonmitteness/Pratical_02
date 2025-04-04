from utils.text_processing import generate_rag_response
from abc import ABC, abstractmethod

class AbstractRAG(ABC):
    def __init__(self, chunk_size, overlap, embedding, llm, preprocess, port, show_debug):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.embedding = embedding
        self.llm = llm
        self.preprocess = preprocess
        self.port = port
        self.show_debug = show_debug

    @abstractmethod
    def tear_down_and_repopuldate_database():
        pass

    @abstractmethod
    def search_embeddings(self, query, top_k=3):
        pass    

    # every class should have this same functionality
    def interactive_search(self):
        """Interactive search interface."""
        print("🔍 RAG Search Interface")
        print("Type 'exit' to quit")

        while True:
            query = input("\nEnter your search query: ")

            if query.lower() == "exit":
                break

            # Search for relevant embeddings
            context_results = self.search_embeddings(query)

            # Generate RAG response
            response = generate_rag_response(query, context_results, self.llm)

            print("\n--- Response ---")
            print(response)

    def evaluate_question(self, query):
        print(f'Query: {query} \n')

        context_results = self.search_embeddings(query)
        response = generate_rag_response(query, context_results, self.llm)

        print(response)
        print('\n')


