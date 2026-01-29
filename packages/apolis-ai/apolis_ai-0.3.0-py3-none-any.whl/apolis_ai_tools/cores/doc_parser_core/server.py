

import os
import sys
from pathlib import Path

# Fix module path so 'cores' can be imported when running this script directly
# We presume we are at <repo>/crew_ai_tools/cores/doc_parser_core/server.py
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import uvicorn
import logging
import apolis_ai_tools.compat  # Shim for older libraries (PaddleOCR)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from apolis_ai_tools.cores.doc_parser_core.app import process_document, _LAYOUT_SERVICE

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DoclingServer")

# CONSTRAINT: This server accepts local file paths. 
# It MUST run on the same machine as the client.
# Do NOT expose this over the internet.
class DocumentRequest(BaseModel):
    file_path: str

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Docling model in main process...")
    # Force initialization of the singleton converter
    if hasattr(_LAYOUT_SERVICE, "converter"):
        _ = _LAYOUT_SERVICE.converter
    logger.info("Docling model initialized and ready on RAM.")
    yield
    # Clean up if needed
    pass

app = FastAPI(title="Docling Extraction Server", lifespan=lifespan)

@app.post("/extract")
async def extract_document(request: DocumentRequest):
    """
    Extracts text and layout from a PDF file.
    The model stays loaded in memory between requests.
    """
    logger.info(f"Received extraction request for: {request.file_path}")
    
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
        
    try:
        # We reuse the same process_document logic, which uses the global _LAYOUT_SERVICE
        # Since this process stays alive, the _LAYOUT_SERVICE.converter stays in RAM
        result = process_document(request.file_path)
        
        if result.get("status") == "failed":
             raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
             
        return result
        
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Allow configuration of port via env var
    port = int(os.environ.get("DOCLING_PORT", 8000))
    logger.info(f"Starting Docling Server on port {port}...")
    
    # CRITICAL: Keep workers=1. Docling uses heavy RAM/Mocking. 
    # Multiple workers will cause memory explosion.
    uvicorn.run(app, host="0.0.0.0", port=port, workers=1)
