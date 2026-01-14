"""Configuration settings for Cortex Knowledge Base Assistant"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"

# Create directories if they don't exist
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

# Model configurations
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Chunking parameters
MAX_CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
SIMILARITY_THRESHOLD = 0.7

# Retrieval parameters
TOP_K_DOCUMENTS = 5
SEMANTIC_WEIGHT = 0.7
KEYWORD_WEIGHT = 0.3

# Ollama configuration
OLLAMA_MODEL = "llama3.2:3b"

# Determine Ollama URL based on environment
# Check environment variable first, then fall back to defaults
import os
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL") or (
    "http://ollama:11434" if os.environ.get("DOCKER_ENV") == "true" else "http://localhost:11434"
)

# n8n configuration (for workflow automation)
# Check environment variable first, then fall back to default
N8N_BASE_URL = os.environ.get("N8N_BASE_URL") or (
    "http://cortex-n8n:5678" if os.environ.get("DOCKER_ENV") == "true" else "http://localhost:5678"
)

# Streamlit configuration
PAGE_TITLE = "Cortex - AI Knowledge Assistant"
PAGE_ICON = "🧠"

# Vector store settings
VECTORSTORE_COLLECTION_NAME = "documents"
VECTORSTORE_PERSIST_DIRECTORY = str(VECTORSTORE_DIR)

# OCR settings
OCR_DPI = 300  # Higher values give better quality but slower processing
OCR_LANGUAGE = "eng"  # Default language for OCR
OCR_CONFIG = "--psm 1 --oem 3"  # Tesseract OCR configuration
OCR_ENABLED = True  # Set to False to disable OCR processing completely

# Auto-loading settings
AUTO_LOAD_DOCUMENTS = False  # Set to False to disable automatic document loading
AUTO_LOAD_SKIP_EXISTING = True  # Skip documents that are already processed
