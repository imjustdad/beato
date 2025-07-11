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

# Lazy LLM Initialization
llm = None

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
    global llm
    try:
        logger.info("Loading LLM model on startup...")
        llm = Llama.from_pretrained(
            repo_id=REPO_ID,
            filename=FILENAME
        )
        logger.info("LLM model loaded.")
    except Exception as e:
        logger.error(f"Failed to load LLM at startup: {e}")


def analyze_response(message: str) -> List[str]:
    global llm

    if llm is None:
        try:
            logger.info("Loading LLM model on-demand...")
            llm = Llama.from_pretrained(
                repo_id="hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF",
                filename="llama-3.2-1b-instruct-q4_k_m.gguf"
            )
            logger.info("LLM model loaded on-demand.")
        except Exception as e:
            logger.error(f"Failed to load LLM: {e}")
            raise HTTPException(status_code=500, detail="LLM failed to load.")

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

        print("LLM raw response:", repr(response_text))
        print("User submitted message:", repr(message))

        if "no matches" in response_text.lower():
            return []
        
        matches = [m.strip() for m in response_text.split(',') if m.strip()]
        return matches


    except Exception as e:
        logger.error(f"Error during LLM analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze message.")

@app.post("/llama", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    matches = analyze_response(request.message)

    if matches:
        return {
            "status": "success",
            "matches": matches,
            "message": "Matches found and returned"
        }
    else:
        return {
            "status": "success",
            "matches": [],
            "message": "No matches detected"
        }

@app.get("/health")
async def health_check():
    return {"status": "ok"}