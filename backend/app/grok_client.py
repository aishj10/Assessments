 # backend/app/grok_client.py
import os
import requests
import logging
from typing import Any, Dict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_API_URL = os.getenv("GROK_API_URL", "https://api.x.ai/v1/chat/completions")

class GrokError(Exception):
    pass

def call_grok(prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> Dict[str, Any]:
    """
    Call to xAI Grok API using the chat completions endpoint.
    """
    if not GROK_API_KEY:
        raise GrokError("GROK_API_KEY environment variable is required")
    
    # Log the input prompt for debugging
    logger.info(f"Grok API Call - Prompt Length: {len(prompt)} characters")
    logger.info(f"Grok API Call - Prompt Preview: {prompt[:200]}...")
    logger.info(f"Grok API Call - Max Tokens: {max_tokens}, Temperature: {temperature}")
    
    headers = {"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"}
    
    # xAI API uses OpenAI-compatible chat completions format
    payload = {
        "model": "grok-3",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    # Log the payload being sent (excluding sensitive API key)
    logger.info(f"Grok API Call - Payload: {payload}")
    
    try:
        resp = requests.post(GROK_API_URL, json=payload, headers=headers, timeout=30)
    except requests.RequestException as e:
        logger.error(f"Grok API Network Error: {e}")
        raise GrokError(f"Network error contacting Grok: {e}")

    if resp.status_code != 200:
        logger.error(f"Grok API Error - Status: {resp.status_code}, Response: {resp.text}")
        raise GrokError(f"Grok API returned {resp.status_code}: {resp.text}")

    data = resp.json()
    
    # Log the response for debugging
    logger.info(f"Grok API Response - Status: {resp.status_code}")
    logger.info(f"Grok API Response - Data Keys: {list(data.keys())}")
    
    # Extract text from OpenAI-compatible response format
    if "choices" in data and len(data["choices"]) > 0:
        text = data["choices"][0]["message"]["content"]
        logger.info(f"Grok API Response - Text Length: {len(text)} characters")
        logger.info(f"Grok API Response - Text Preview: {text[:200]}...")
    else:
        logger.error(f"Grok API Unexpected Response Format: {data}")
        raise GrokError(f"Unexpected Grok response format: {data}")

    return {"text": text, "raw": data}
