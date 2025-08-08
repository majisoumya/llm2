# backend/main.py
import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from core.schemas import QueryRequest, QueryResponse
from core.processing import DocumentProcessor

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
API_BEARER_TOKEN = "b8171a8cdbd8010a1ac308defcbcc5210fbba7412f60ef99cd428ffb3a412be7"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables.")

# --- Authentication ---
auth_scheme = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    """Dependency to verify the bearer token."""
    if credentials.scheme != "Bearer" or credentials.credentials != API_BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication token",
        )
    return credentials

# --- FastAPI App ---
app = FastAPI(
    title="Intelligent Query–Retrieval System API",
    version="1.0"
)

# Initialize the document processor once
doc_processor = DocumentProcessor(groq_api_key=GROQ_API_KEY)

@app.post(
    "/api/v1/hackrx/run",
    response_model=QueryResponse,
    dependencies=[Depends(verify_token)]
)
async def run_submission(request_data: QueryRequest):
    """
    Processes documents and questions to provide intelligent answers.
    - **documents**: URL to the PDF document.
    - **questions**: A list of questions to ask about the document.
    """
    try:
        # 1. Create a vector store from the document for this request
        # This is done per-request to handle different documents
        doc_processor.create_vector_store(str(request_data.documents))

        # 2. Answer the questions using the created vector store
        answers = doc_processor.answer_questions(request_data.questions)
        
        # 3. Return the structured JSON response
        return QueryResponse(answers=answers)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Catch-all for other potential errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

# Optional: Add a root endpoint for health checks
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Intelligent Query–Retrieval System is running."}