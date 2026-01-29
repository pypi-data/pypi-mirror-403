
import os
import requests
from crewai.tools import tool
from apolis_ai_tools.cores.doc_parser_core.app import process_document

import logging

# Set up tool-specific logger
logger = logging.getLogger("tools.doc_parser")

@tool("parse_document")
def parse_document(file_path: str) -> dict:
    """
    Parse a PDF document and return structured JSON.
    """
    server_url = os.environ.get("DOCLING_SERVER_URL", "http://localhost:8000")
    
    # helper to run local processing
    def run_local():
        logger.warning(f"Server unreachable at {server_url}. Running in fallback local mode (slower)...")
        return process_document(file_path)

    try:
        # Check if server is reachable and active
        # Timeout: (connect_timeout, read_timeout)
        # Connect fast (2s), wait long for processing (600s)
        response = requests.post(
            f"{server_url}/extract", 
            json={"file_path": file_path},
            timeout=(2, 600)
        )
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Server error {response.status_code}: {response.text}. Fallback to local.")
            return run_local()
            
    except requests.exceptions.ConnectionError:
        # Silent fallback for connection refused (server likely not running)
        return run_local()
    except Exception as e:
        logger.warning(f"Unexpected connection error: {e}. Fallback to local.")
        return run_local()

