import argparse
from rag_databases.redis_stack.redis_stack import RedisRAG
from rag_databases.qdrant.qdrant_rag import QDrantRAG
from rag_databases.chroma.chroma_rag import ChromaRAG

def open_questions_file(file_name):
    with open(file_name, "r") as file:
        file_content = file.read()
        return file_content.split('\n')

if __name__ == "__main__":
    # Driver File all the optional arguments/ things that can be changed
    # You can update the default settings or change command line arguments
    question_file = open_questions_file('questions.txt')

    parser = argparse.ArgumentParser(description= "Additional arguments for file loading")
    parser.add_argument('-p', type=int, help='Port number to connect rag databse to', default=6379)
    parser.add_argument('-chunk', type=int, help='Port number to connect rag databse to', default=300)
    parser.add_argument('-o', type=int, help='Port number to connect rag databse to', default=50)
    parser.add_argument('-test', action='store_true', help='Run through the test question or interactive search')
    parser.add_argument('-pre', action='store_true', help='Optional argument to Preprocess files')
    parser.add_argument('-debug', action='store_true', help='Optional argument to Preprocess files')
    # TODO: readMe instructions on this b/c you need it just out there as a string which is weird... (defualts do not exist on these)
    parser.add_argument('database', type=str, help='Choose which RAG db you prefer', choices=['Redis', 'Chroma', 'Qdrant'])
    parser.add_argument('llm', type=str, help='Change the given LLM for the model', choices=['mistral:latest', 'qwen2.5:latest'])
    parser.add_argument('embed', type=str, help='Change the embedding model', choices=['mxbai-embed-large:latest', 'nomic-embed-text:latest', 'all-minilm:latest'])


    args = parser.parse_args()
    db = args.database
    if(db == 'Redis'):
        Redis_RAG = RedisRAG(chunk_size=args.chunk, overlap=args.o, embedding=args.embed, llm=args.llm, preprocess=args.pre, port=args.p, show_debug=args.debug)
        Redis_RAG.tear_down_and_repopuldate_database()
        if(args.test):
            for question in question_file:
                Redis_RAG.evaluate_question(question)
        else:
            Redis_RAG.interactive_search()
    elif(db == 'Qdrant'):
        Qdrant_RAG = QDrantRAG(chunk_size=args.chunk, overlap=args.o, embedding=args.embed, llm=args.llm, preprocess=args.pre, port=args.p, show_debug=args.debug)
        Qdrant_RAG.tear_down_and_repopuldate_database()
        if(args.test):
            for question in question_file:
                Qdrant_RAG.evaluate_question(question)
        else:
            Qdrant_RAG.interactive_search()
    else:
        # db is Chroma:
        Chroma_RAG = ChromaRAG(chunk_size=args.chunk, overlap=args.o, embedding=args.embed, llm=args.llm, preprocess=args.pre, port=args.p, show_debug=args.debug)
        Chroma_RAG.tear_down_and_repopuldate_database()
        if(args.test):
            for question in question_file:
                Chroma_RAG.evaluate_question(question)
        else:
            Chroma_RAG.interactive_search()





