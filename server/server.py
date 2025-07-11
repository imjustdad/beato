from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama
from typing import List, Union
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

llm = Llama.from_pretrained(
    repo_id="hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF",
    filename="llama-3.2-1b-instruct-q4_k_m.gguf"
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    status: str
    matches: Union[List[str], None]
    message: str


def analyze_response(message: str) -> List[str]:
    try:
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "Please analyze the following message for musical chords or progressions. Progressions may also be listed as numbers rather than roman numerals. If you find any chords or progressions, just list them, separated by commas. If no chords or progressions are found, say 'no matches detected.' Do not provide any additional explanation."},
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        response_text = response['choices'][0]['message']['content']

        if "no matches detected" in response_text:
            return []

        matches = [match.strip()
                   for match in response_text.split(',') if match.strip()]

        return matches

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/llama", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
