import os
import time
import requests
from pdf_reader import extract_and_chunk_text
from llm_utils import get_embeddings
import promptquality as pq
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Initialize Galileo
print("Logging in to Galileo...")
pq.login("https://console.dev.rungalileo.io/")

# Constants
PDF_PATH = "data/attention.pdf"
API_URL = "http://localhost:8000"
CHUNK_SIZE = 600
TOP_K = 10

# Questions to ask
QUESTIONS = [
    "What is the main contribution of the paper?",
    "How does the transformer architecture work?",
    "What is self-attention and how does it work?",
    "What are the advantages of transformers over RNNs?",
    "What is multi-head attention?",
    "How does positional encoding work in transformers?",
    "What are the key components of the transformer architecture?",
    "How does the transformer handle sequential data?",
    "What are the limitations of the transformer model?",
    "How does the transformer achieve parallelization?",
]

def process_pdf():
    """Process the PDF and generate embeddings"""
    print(f"Loading and chunking PDF: {PDF_PATH}...")
    text_chunks = extract_and_chunk_text(PDF_PATH, chunk_size=CHUNK_SIZE)
    
    if text_chunks:
        print(f"Generating embeddings for {len(text_chunks)} chunks...")
        embeddings_list = get_embeddings(text_chunks)
        if embeddings_list:
            chunk_embeddings = np.array(embeddings_list)
            print("Embeddings generated successfully.")
            return text_chunks, chunk_embeddings
    return None, None

def upload_pdf():
    """Upload the PDF to the API"""
    print("Uploading PDF to API...")
    with open(PDF_PATH, "rb") as f:
        files = {"file": ("attention.pdf", f, "application/pdf")}
        response = requests.post(f"{API_URL}/upload_pdf", files=files)
        if response.status_code == 200:
            print("PDF uploaded successfully")
            return True
        else:
            print(f"Failed to upload PDF: {response.text}")
            return False

def ask_question(question: str):
    try:
        response = requests.post(
            f"{API_URL}/ask_pdf",
            json={"question": question, "offline_evaluation": False}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"\nQ: {data['question']}")
            print(f"A: {data['answer']}\n")
        else:
            print(f"Error asking question: {response.text}")
    except Exception as e:
        print(f"Exception while asking question: {e}")

def main():
    # First, upload the PDF
    if not upload_pdf():
        print("Failed to upload PDF. Exiting...")
        return

    # Then, continuously ask questions
    question_index = 0
    while True:
        question = QUESTIONS[question_index]
        ask_question(question)
        
        # Move to next question
        question_index = (question_index + 1) % len(QUESTIONS)
        
        # Wait for 2 seconds
        time.sleep(2)

if __name__ == "__main__":
    main() 