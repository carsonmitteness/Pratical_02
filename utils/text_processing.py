import ollama
import fitz
import string
import re

def clean_text(text):
     # Remove punctuation 
     text = text.translate(str.maketrans("", "", string.punctuation))
     # Remove any extra whitespace
     text = re.sub(r'\s+', ' ', text).strip() 
     return text

# extract the text from a PDF by page
def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    doc = fitz.open(pdf_path)
    text_by_page = []
    for page_num, page in enumerate(doc):
        text_by_page.append((page_num, page.get_text()))
    return text_by_page

def get_embedding(text: str, model) -> list:

    response = ollama.embeddings(model=model, prompt=text)
    return response["embedding"]

def split_text_into_chunks(text, chunk_size, overlap):
    """Split text into chunks of approximately chunk_size words with overlap."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
    return chunks

def generate_rag_response(query, context_results, llm_model):

    # Prepare context string
    context_str = "\n".join(
        [
            f"From {result.get('file', 'Unknown file')} (page {result.get('page', 'Unknown page')}, chunk {result.get('chunk', 'Unknown chunk')}) "
            f"with similarity {float(result.get('similarity', 0)):.2f}"
            for result in context_results
        ]
    )

    # Construct prompt with context
    prompt = f"""You are a helpful AI assistant. 
    Use the following context to answer the query as accurately as possible. If the context doesn't entirely match with the given query
    make an educated guess using the given information you have.

Context:
{context_str}

Query: {query}

Answer:"""

    # Generate response using Ollama
    response = ollama.chat(
        model=llm_model, messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]