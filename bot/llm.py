import os
import requests
from logger import setup_logger

logger = setup_logger("llm-bot")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000/llama")

def is_pattern_matched(message: str):
    try:
        response = requests.post(FASTAPI_URL, json={"message": message})

        if response.status_code == 200:
            return response.json()
    except requests.RequestException as e:
        logger.info(f"Error querying LLM server: {e}")
        return None