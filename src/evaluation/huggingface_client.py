import os
import requests
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import sys

# --- Path Fix ---
# Add the project's root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# --- End Path Fix ---

# --- Corrected Logger Import ---
from src.monitoring.logger import get_logger # Import the function
logger = get_logger() # Get the logger instance
# --- End Corrected Logger Import ---

MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct" 
API_URL = "https://router.huggingface.co/v1/chat/completions"

load_dotenv()

def query_model(prompt: str) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("HF_API_KEY")
    if not api_key:
        logger.error("HF_API_KEY not found in environment variables.")
        logger.error("Please create a .env file in the project root with HF_API_KEY=hf_...")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,
        "max_tokens": 100
    }

    try:
        logger.debug(f"Sending API request to {API_URL} for model {MODEL_NAME}")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        logger.debug("API request successful.")
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}", exc_info=True) # Add exc_info for traceback
        # Check if response object exists before accessing text
        response_text = getattr(http_err, 'response', None)
        if response_text is not None:
             try:
                  logger.error(f"Response body: {response_text.text}")
             except Exception:
                  logger.error("Could not decode response body.")
        else:
             logger.error("No response object available in HTTPError.")

    except requests.exceptions.Timeout:
        logger.error(f"The request timed out after 30 seconds for prompt: '{prompt[:50]}...'")
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred during the API request: {e}", exc_info=True)

    return None


# Self-Test Block (Remains unchanged for isolated testing if needed)
if __name__ == "__main__":

    # Ensure the parser can be found relative to this script's location for self-test
    try:
        from src.evaluation.response_parser import parse_response
    except ImportError:
         # If run directly, src might not be in path correctly, adjust for test
         sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
         from src.evaluation.response_parser import parse_response


    logger.info("--- [HF Client & Parser Integration Self-Test] ---")

    test_prompt = "What is ((2 + 3) * 4) / 3?"
    logger.info(f"Querying model with prompt: '{test_prompt}'")

    response_data = query_model(test_prompt)

    if response_data:
        logger.info("Successfully received API response.")

        try:
            raw_text = response_data['choices'][0]['message']['content']
            logger.info("--- [Raw Model Response] ---")
            logger.info(raw_text)
            logger.info("--- [End Raw Response] ---")

            logger.info("Running parser...")
            parsed_answer = parse_response(raw_text)

            logger.info(f"Parsed Answer: {parsed_answer}")

            if parsed_answer is not None:
                logger.info("Test Result: PASS")
            else:
                logger.warning("Test Result: FAIL (Parser returned None)")

        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Test Result: FAIL (Could not extract/parse text from response: {e})", exc_info=True)
            logger.error(f"Full Response: {response_data}")
    else:
        logger.error("API call failed during self-test.")

    logger.info("--- [Self-Test Complete] ---")