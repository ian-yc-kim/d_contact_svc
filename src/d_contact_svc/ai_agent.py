import os
import requests
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
BATCH_SIZE = 10
# API endpoint for GPT-4o-mini; can be configured via environment variable
GPT4O_MINI_API_ENDPOINT = os.getenv("GPT4O_MINI_API_ENDPOINT", "https://api.gpt4o-mini.com/v1/identify")


def _batch_list(items: list, batch_size: int):
    """
    Generator to batch items into lists of size batch_size.

    :param items: List of items to batch
    :param batch_size: Size of each batch
    :return: Generator of batches
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i+batch_size]


def identify_email_owners(email_contexts: list) -> list:
    """
    Identify email owners using GPT-4o-mini API by processing the provided email contexts.
    It batches the input for optimal performance and makes secure API calls with proper error handling.

    :param email_contexts: List of email context strings
    :return: List of dictionaries where each dictionary contains the email_context and the identified owner (or None if not identified).
    """
    api_key = os.getenv("GPT4O_MINI_API_KEY")
    if not api_key:
        logging.error("GPT4O_MINI_API_KEY environment variable is not set")
        raise ValueError("GPT4O_MINI_API_KEY environment variable not set")

    results = []
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        # Process email_contexts in batches for optimal performance
        for batch in _batch_list(email_contexts, BATCH_SIZE):
            payload = {"email_contexts": batch}
            response = requests.post(GPT4O_MINI_API_ENDPOINT, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                # Expected response format: {"results": [{"email_context": <str>, "owner": <str>}, ...]}
                data = response.json()
                results.extend(data.get("results", []))
            else:
                logging.error(f"API call failed with status {response.status_code}: {response.text}")
                # Fallback behavior: mark each context in batch with unknown owner
                results.extend([{"email_context": ctx, "owner": None} for ctx in batch])
    except Exception as e:
        logging.error(e, exc_info=True)
        # Fallback for complete failure: mark all provided contexts with unknown owner
        results = [{"email_context": ctx, "owner": None} for ctx in email_contexts]
    
    return results
