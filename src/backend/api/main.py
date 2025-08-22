import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.backend.qdrant_client import get_qdrant_client
from src.backend.api.routes import router
from src.backend.utils.embed_utils import JinaEmbedder
from src.backend.services.search_service import SearchService
from src.backend.config import CORS_ORIGINS


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Repository Analyzer API",
    description="API for analyzing and searching through GitHub repositories",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    
    try:
        app.state.qdrant = get_qdrant_client()
        logger.info("Qdrant client initialized")
        
        jina_api_key = os.getenv("JINA_API_KEY")
        if not jina_api_key:
            logger.warning("JINA_API_KEY not found in environment variables")
            jina_api_key = "your_api_key_here"
        
        app.state.jina_embedder = JinaEmbedder(api_key=jina_api_key)
        
        
        app.state.search_service = SearchService(
            qdrant=app.state.qdrant,
            embedder=app.state.jina_embedder,
            repo_id="default"
        )
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Repository Analyzer API",
        "version": "1.0.0",
        "endpoints": {
            "load_repo": "POST /load_repo - Load a GitHub repository",
            "ingest": "POST /ingest - Process and embed loaded repository",
            "search": "POST /search - Search through repository content",
            "collections": "GET /collections - List Qdrant collections",
            "status": "GET /status - Get current system status"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        collections = app.state.qdrant.get_collections()
        
        return {
            "status": "healthy",
            "services": {
                "qdrant": "connected",
                "embedder": "initialized" if hasattr(app.state, "jina_embedder") else "not_initialized",
                "search_service": "initialized" if hasattr(app.state, "search_service") else "not_initialized"
            },
            "collections_count": len(collections.collections)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service unhealthy: {str(e)}")


app.include_router(router)