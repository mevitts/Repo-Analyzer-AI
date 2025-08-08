import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = "cedar-router-466020-s9"
GOOGLE_API_KEY = None
GITHUB_TOKEN = None
FRONTEND_API_KEY = None

try:
    from src.backend.tools import get_secret
    GOOGLE_API_KEY = get_secret("GOOGLE_API_KEY", PROJECT_ID)
    FRONTEND_API_KEY = get_secret("FRONTEND_API_KEY", PROJECT_ID)
    print("Using Google API key from Secret Manager")
except Exception as e:
    print(f"Could not access Secret Manager: {e}")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in .env file or Secret Manager.")

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