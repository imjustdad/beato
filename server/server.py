import os
import logging
import json
from typing import List, Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

app = FastAPI()

llm = None
llm_loaded_successfully = False

REPO_ID = os.getenv("LLAMA_REPO_ID", "hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF")
FILENAME = os.getenv("LLAMA_FILENAME", "llama-3.2-1b-instruct-q4_k_m.gguf")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    status: str
    matches: Union[List[str], None]
    message: str

# Load LLM on startup event
@app.on_event("startup")
def load_llm():
    global llm, llm_loaded_successfully
    try:
        logger.info("Loading LLM model on startup...")
        llm = Llama.from_pretrained(
            repo_id=REPO_ID,
            filename=FILENAME
        )
        llm_loaded_successfully = True
        logger.info("LLM model loaded.")
    except Exception as e:
        llm_loaded_successfully = False
        logger.error(f"Failed to load LLM at startup: {e}")


def analyze_response(message: str) -> List[str]:
    global llm, llm_loaded_successfully

    if not llm_loaded_successfully or llm is None:
        logger.error("Attempted to analyze response, but LLM is not loaded or failed to load.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM model is not loaded. Please wait."
        )
            

    try:
        response = llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "Please analyze the following message for musical chords or progressions. Progressions may also be listed as numbers rather than roman numerals. If you find any chords or progressions, just list them, separated by commas. If no chords or progressions are found, say 'no matches.' Do not provide any additional explanation."
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        response_text = response['choices'][0]['message']['content'].strip()

        if "no matches" in response_text.lower():
            return []
        
        matches = [m.strip() for m in response_text.split(',') if m.strip()]
        return matches


    except Exception as e:
        logger.error(f"Error during LLM analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze message due to an internal LLM error."
        )

@app.post("/llama", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    try:
        matches = analyze_response(request.message)
        
        if matches:
            return ChatResponse(
                status="success",
                matches=matches,
                message="Matches found and returned"
            )
        else:
            return ChatResponse(
                status="success",
                matches=[],
                message="No matches detected"
            )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("fUnhandled error in llama endpoint")

@app.get("/health")
async def health_check():
    global llm_loaded_successfully
    if llm_loaded_successfully:
        return {
            "status": "healthy",
            "model_loaded": True,
            "message": "LLM model is loaded and ready."
        }
    else:
        logger.warning("Health check failed: LLM model is not yet loaded or failed to load.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM model is still loading or failed to load."
        )