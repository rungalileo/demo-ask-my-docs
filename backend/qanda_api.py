import os
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import uvicorn
import promptquality as pq
from promptquality import EvaluateRun, Document, Message, MessageRole, Models
from galileo_observe import ObserveWorkflows
import threading
import shutil
from typing import Optional, Tuple

# Import functions from other modules
from pdf_reader import extract_and_chunk_text
from llm_utils import ask_openai, get_embeddings

# Initialize promptquality and observe
print("Logging in to Galileo...")
pq.login("https://console.dev.rungalileo.io/")
GALILEO_PROJECT_NAME = 'pdf_qa_evaluations'
GALILEO_OBSERVE_PROJECT = 'pdf_qa_observe'

# Set Galileo Observe configuration
os.environ['GALILEO_CONSOLE_URL'] = 'https://console.dev.rungalileo.io/'

# Initialize observe workflows
observe_workflows = ObserveWorkflows(project_name=GALILEO_OBSERVE_PROJECT)

app = FastAPI(
    title="PDF Q&A API",
    description="API to ask questions about a specific PDF document."
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration ---
UPLOAD_DIR = "data"
CHUNK_SIZE = 600
TOP_K = 10

# Global variables to store the current PDF data
current_pdf_path: Optional[str] = None
text_chunks: list = []
chunk_embeddings: np.ndarray = np.array([])

def process_pdf(pdf_path: str):
    """Process a PDF file and generate embeddings"""
    global text_chunks, chunk_embeddings
    
    print(f"Loading and chunking PDF: {pdf_path}...")
    text_chunks = extract_and_chunk_text(pdf_path, chunk_size=CHUNK_SIZE)
    
    if text_chunks:
        print(f"Generating embeddings for {len(text_chunks)} chunks...")
        embeddings_list = get_embeddings(text_chunks)
        if embeddings_list:
            chunk_embeddings = np.array(embeddings_list)
            print("Embeddings generated successfully.")
            return True
    return False

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file"""
    global current_pdf_path
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Save the uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process the PDF
    if process_pdf(file_path):
        current_pdf_path = file_path
        return {"message": "PDF processed successfully", "filename": file.filename}
    else:
        raise HTTPException(status_code=500, detail="Failed to process PDF")

# --- API Request Model ---
class QuestionRequest(BaseModel):
    question: str
    offline_evaluation: bool = False
    metrics: list[str] = []

def finish_evaluation(evaluate_run):
    """Helper function to finish evaluation in a separate thread"""
    try:
        print("Evaluating using Galileo 🔭...")
        evaluate_run.finish()
        print("Galileo evaluation run completed successfully.")
    except Exception as e:
        print(f"Error in evaluation thread: {e}")

def create_evaluation_workflow(question: str, answer: str, prompt: str, relevant_chunks: list, metrics: list[str]) -> EvaluateRun:
    """Create and configure an evaluation workflow"""
    # Map metric names to their corresponding scorers
    metric_to_scorer = {
        'correctness': pq.Scorers.correctness,
        'context_adherence': pq.Scorers.context_adherence_plus,
        'instruction_adherence': pq.Scorers.instruction_adherence,
        'chunk_attribution': pq.Scorers.chunk_attribution_utilization_luna,
        'toxic_content': pq.Scorers.toxicity,
        'tone': pq.Scorers.tone,
        'completeness': pq.Scorers.completeness_plus
    }
    
    # Convert metrics to scorers, defaulting to all if none specified
    scorers = [metric_to_scorer[metric] for metric in metrics] if metrics else list(metric_to_scorer.values())
    
    evaluate_run = EvaluateRun(
        scorers=scorers,
        project_name=GALILEO_PROJECT_NAME
    )

    # Create workflow for evaluation
    wf = evaluate_run.add_workflow(
        input=question,
        output=answer,
        duration_ns=2000
    )

    # Log the retriever step
    wf.add_retriever(
        input=question,
        documents=[Document(content=chunk, metadata={"length": len(chunk)}) for chunk in relevant_chunks],
        duration_ns=1000
    )

    # Log the LLM step
    wf.add_llm(
        input=Message(content=prompt, role=MessageRole.user),
        output=Message(content=answer, role=MessageRole.assistant),
        model=Models.chat_gpt,
        input_tokens=len(prompt.split()),
        output_tokens=len(answer.split()),
        total_tokens=len(prompt.split()) + len(answer.split()),
        duration_ns=1000
    )

    return evaluate_run

def create_observe_workflow(question: str, answer: str, prompt: str, relevant_chunks: list):
    """Create and configure an observe workflow"""
    # Log to Observe
    observe_wf = observe_workflows.add_workflow(
        input=question,
        output=answer,
        duration_ns=2000
    )
    
    # Log the retriever step to Observe
    observe_wf.add_retriever(
        input=question,
        documents=[Document(content=chunk, metadata={"length": len(chunk)}) for chunk in relevant_chunks],
        duration_ns=1000
    )
    
    # Log the LLM step to Observe
    observe_wf.add_llm(
        input=Message(content=prompt, role=MessageRole.user),
        output=Message(content=answer, role=MessageRole.assistant),
        model=Models.chat_gpt,
        input_tokens=len(prompt.split()),
        output_tokens=len(answer.split()),
        total_tokens=len(prompt.split()) + len(answer.split()),
        duration_ns=1000
    )
    
    # Upload the observation
    observe_workflows.upload_workflows()

# --- API Endpoint ---
@app.post("/ask_pdf", summary="Ask a question about the PDF")
async def ask_pdf_endpoint(request: QuestionRequest):
    """
    Receives a question, finds relevant context from the PDF using embeddings,
    and asks OpenAI to answer the question based on the context.
    """
    question = request.question
    offline_evaluation = request.offline_evaluation
    metrics = request.metrics
    print(f"Received question: {question}")

    if not current_pdf_path:
        raise HTTPException(status_code=400, detail="No PDF file uploaded yet")
    
    if not text_chunks or chunk_embeddings.size == 0:
        raise HTTPException(status_code=500, detail="PDF data or embeddings not loaded correctly.")

    try:
        # 1. Get embedding for the question
        print("Generating embedding for the question...")
        question_embedding_list = get_embeddings([question])
        if not question_embedding_list:
            raise HTTPException(status_code=500, detail="Failed to generate embedding for the question.")
        question_embedding = np.array(question_embedding_list[0]).reshape(1, -1)

        # 2. Calculate cosine similarity
        print("Calculating similarities...")
        similarities = cosine_similarity(question_embedding, chunk_embeddings)[0]

        # 3. Get top K chunk indices
        top_k_indices = np.argsort(-similarities)[:TOP_K]
        print(f"Top {TOP_K} relevant chunk indices: {top_k_indices}")

        # 4. Construct context from top K chunks
        relevant_chunks = [text_chunks[i] for i in top_k_indices]
        context = "\n\n".join(relevant_chunks)

        # 5. Construct the prompt for OpenAI
        prompt = f"""
            Given the context, answer the following question:
            question: {question}
            context: {context}
        """
        print("Sending prompt to LLM...")

        # 6. Call OpenAI
        answer = ask_openai(prompt)
        print("Received answer from LLM.")

        # Create and run evaluation workflow only if offline_evaluation is True
        if offline_evaluation:
            evaluate_run = create_evaluation_workflow(question, answer, prompt, relevant_chunks, metrics)
            evaluation_thread = threading.Thread(
                target=finish_evaluation,
                args=(evaluate_run,)
            )
            evaluation_thread.start()

        # Create observe workflow
        create_observe_workflow(question, answer, prompt, relevant_chunks)

        return {"question": question, "answer": answer}

    except Exception as e:
        print(f"An error occurred during API call: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

# --- Run the API (for local development) ---
if __name__ == "__main__":
    print("Starting FastAPI server...")
    if not os.getenv("OPENAI_API_KEY"):
        print("\n*** WARNING: OPENAI_API_KEY environment variable not found. ***")
        print("Please create a .env file with OPENAI_API_KEY=your_key or set the environment variable.\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8000) 