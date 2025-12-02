import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.monitoring.logger import get_logger
logger = get_logger()

BASE_URL = "https://api.groq.com/openai/v1"
MODEL_NAME = "openai/gpt-oss-120b" 

load_dotenv()

def query_model(prompt: str) -> Optional[Dict[str, Any]]:
    """
    Queries the model using the OpenAI client pointing to Groq.
    Returns a dict structure compatible with the existing evaluator.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY not found in environment variables.")
        return None

    
    client = OpenAI(
        base_url=BASE_URL,
        api_key=api_key,
    )

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
          messages = [
            {
                "role": "system",
                "content": "You are a precise calculator. Output ONLY the result."
            },
            {
                "role": "user",
                "content": (
                    f"Calculate: {prompt}\n\n"
                    "Rules:\n"
                    "1. Do NOT explain your steps.\n"
                    "2. Do NOT use <think> tags.\n"
                    "3. Output format must be strictly: FINAL_ANSWER: <number>"
                )
            }
        ],
            temperature=0.0,
            max_tokens=1024,
        )

        # Extract content
        response_content = completion.choices[0].message.content
        
        # Return in the structure expected by src/analysis/evaluator.py
        return {
            'choices': [
                {
                    'message': {
                        'content': response_content
                    }
                }
            ]
        }

    except Exception as e:
        # Handle Rate Limits (429) specifically
        if "429" in str(e):
            logger.warning("Groq Rate Limit hit (429). Sleeping for 10s...")
            time.sleep(10)
            return None 
            
        logger.error(f"Groq API Request Error: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    # Quick Test
    test_q = "((2+2)*5)/4"
    print(f"Testing with query: {test_q}")
    result = query_model(test_q)
    print("Result:", result)