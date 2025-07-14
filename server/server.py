import os
import logging
import json
from typing import List, Union
from fastapi import FastAPI, HTTPException, status
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
    is_beato_meme: bool
    confidence: float
    reasoning: str

# Load LLM on startup event
@app.on_event("startup")
def load_llm():
    global llm, llm_loaded_successfully
    try:
        logger.info("Loading LLM model on startup...")
        llm = Llama.from_pretrained(
            repo_id=REPO_ID,
            filename=FILENAME,
            verbose=False
        )
        llm_loaded_successfully = True
        logger.info("LLM model loaded.")
    except Exception as e:
        llm_loaded_successfully = False
        logger.error(f"Failed to load LLM at startup: {e}")


def analyze_response(message: str) -> ChatResponse:
    global llm, llm_loaded_successfully

    if not llm_loaded_successfully or llm is None:
        logger.error("Attempted to analyze response, but LLM is not loaded or failed to load.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM model is not loaded. Please wait."
        )
    
    system_content="""
    You are an expert in internet meme culture and Reddit discourse. Your task is to analyze a Reddit comment and determine whether it is a reference to or joke about the ongoing meme feud between Pat Finnerty and Rick Beato.
    This meme often includes jokes or sarcastic comparisons between Pat Finnerty's irreverent, DIY musical humor and Rick Beato's technical, academic YouTube approach to music theory and production. It may reference:
    - Phrases like “What makes this good?”, “he’s not a theory guy,” “Rick would hate this,” etc.
    - Satirical or exaggerated praise/criticism of either person
    - Comments on music taste, tone, production quality, or theory from a comedic angle
    Given the Reddit comment below, decide if it fits this meme format.
    """

    try:
        response = llm.create_chat_completion(
            messages=[
                { "role": "system", "content": system_content },
                { "role": "user", "content": message }
            ],
            response_format={
                "type": "json_object",
                "schema": {
                    "type": "object",
                    "properties": {
                        "is_beato_meme": { "type": "boolean" },
                        "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
                        "reasoning": { "type": "string" }
                    },
                    "required": ["is_beato_meme", "confidence", "reasoning"],
                }
            }
        )

        response_text = response['choices'][0]['message']['content']
        response_json = json.loads(response_text)

        return ChatResponse(
            is_beato_meme = response_json['is_beato_meme'],
            confidence = response_json['confidence'],
            reasoning = response_json['reasoning']
        )

    except Exception as e:
        logger.error(f"Error during LLM analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze message due to an internal LLM error."
        )

@app.post("/llama", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    try:
        return analyze_response(request.message)
        
    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error(f"Unhandled error in llama endpoint")

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