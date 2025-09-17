"""
Configuration for Repo Analyzer backend.
Loads environment variables, sets up language configs, and CORS origins.
"""

import os
from dotenv import load_dotenv
from .language_enums import Language

load_dotenv()

# Project and API keys
GOOGLE_API_KEY = None
FRONTEND_API_KEY = None

# Uncomment and use Secret Manager in production
# try:
#     from src.backend.tools import get_secret
#     GOOGLE_API_KEY = get_secret("GOOGLE_API_KEY", PROJECT_ID)
#     FRONTEND_API_KEY = get_secret("FRONTEND_API_KEY", PROJECT_ID)
#     print("Using Google API key from Secret Manager")
# except Exception as e:
#     print(f"Could not access Secret Manager: {e}")
#     GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
#     if not GOOGLE_API_KEY:
#         raise ValueError("GOOGLE_API_KEY not found in .env file or Secret Manager.")

# Allowed CORS origins for frontend access
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://cedar-router-466020-s9.uc.r.appspot.com",
    "https://cedar-router-466020-s9.web.app",
    "https://cedar-router-466020-s9.firebaseapp.com"
]

APP_NAME = "Repo_Analysis"

# Per-language chunking and analysis configuration
LANGUAGE_CONFIGS = {
    Language.PYTHON: {
        "max_chunk_size": 850,
        "language": Language.PYTHON.value,
        "metadata_template": "default",
        "chunk_expansion": True,
        "chunk_overlap": 2,
    },
    Language.JAVA: {
        "max_chunk_size": 1000,
        "language": Language.JAVA.value,
        "metadata_template": "default",
        "chunk_expansion": True,
        "chunk_overlap": 2,
    },
    Language.TYPESCRIPT: {
        "max_chunk_size": 900,
        "language": Language.TYPESCRIPT.value,
        "metadata_template": "default",
        "chunk_expansion": True,
        "chunk_overlap": 2,
    },
    Language.CSHARP: {
        "max_chunk_size": 900,
        "language": Language.CSHARP.value,
        "metadata_template": "default",
        "chunk_expansion": True,
        "chunk_overlap": 2,
    }
}

# Jina embedding API configuration
JINA_API_URL = 'https://api.jina.ai/v1/embeddings'
JINA_HEADERS = {
    'Content-Type': 'application/json',
}