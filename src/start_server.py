#!/usr/bin/env python3
"""
Startup script for Repository Analyzer API

This script starts the FastAPI server with proper configuration
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if the environment is properly set up"""
    logger.info("Checking environment setup...")
    
    current_dir = Path.cwd()
    expected_files = ["requirements.txt", "src", "main.py"]
    
    missing_files = []
    for file in expected_files:
        if not (current_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"Missing required files/directories: {missing_files}")
        logger.error("Make sure you're running this from the project root directory")
        return False
    
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        logger.error(f"Python 3.8+ is required. Current version: {python_version.major}.{python_version.minor}")
        return False
    
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.warning("GITHUB_TOKEN not set. Repository loading may fail.")
        logger.info("Set it with: export GITHUB_TOKEN=your_token_here")
    
    jina_api_key = os.getenv("JINA_API_KEY")
    if not jina_api_key:
        logger.warning("JINA_API_KEY not set. You'll need to update the code with your API key.")
        logger.info("Set it with: export JINA_API_KEY=your_api_key_here")
    
    return True


def check_dependencies():
    """Check if required dependencies are installed"""
    logger.info("Checking dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "qdrant-client",
        "requests",
        "astchunk"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.info("Install them with: pip install -r requirements.txt")
        return False
    
    logger.info("All required dependencies are installed")
    return True


def start_qdrant():
    """Check if Qdrant is running and provide instructions if not"""
    logger.info("Checking Qdrant connection...")
    
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient("localhost", port=6333)
        client.get_collections()
        logger.info("Qdrant is running and accessible")
        return True
    except Exception as e:
        logger.error(f"Qdrant is not accessible: {e}")
        logger.info("Start Qdrant with: docker run -p 6333:6333 qdrant/qdrant:latest")
        logger.info("Or install locally and run: qdrant")
        return False


def start_server(host="localhost", port=8000, reload=True):
    """Start the FastAPI server"""
    logger.info(f"Starting Repository Analyzer API server on {host}:{port}")
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.backend.api.main:app",
        "--host", host,
        "--port", str(port)
    ]
    
    if reload:
        cmd.append("--reload")
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except subprocess.CalledProcessError as e:
        logger.error(f"Server failed to start: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
    
    return True


def main():
    """Main function to start the server with all checks"""
    logger.info("=" * 50)
    logger.info("Repository Analyzer API Startup")
    logger.info("=" * 50)
    
    if not check_environment():
        logger.error("Environment check failed")
        sys.exit(1)
    
    if not check_dependencies():
        logger.error("Dependencies check failed")
        sys.exit(1)
    
    if not start_qdrant():
        logger.error("Qdrant check failed")
        logger.info("Please start Qdrant before running the API server")
        sys.exit(1)
    
    logger.info("All checks passed. Starting server...")
    start_server()

if __name__ == "__main__":
    main()
