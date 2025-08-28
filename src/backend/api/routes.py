from fastapi import APIRouter, Request
import logging
from src.backend.services.embedding_service import process_repo
from src.backend.utils.embed_utils import JinaEmbedder
from src.backend.utils.file_utils import list_files, get_file_contents

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/load_repo")
async def load_repo(request: Request, repo_id: str, owner: str):
    """
    Endpoint to load a repository before processing its contents.
    """
    logger.info(f"Loading repository {repo_id} for owner {owner}")
    try:
        file_list_resp = list_files(repo=repo_id, owner=owner)
        logger.info(f"File list response: Completed")
        if file_list_resp["status"] != "success":
            logger.error(f"Failed to list files: {file_list_resp.get('message')}")
            return {"status": "error", "message": file_list_resp.get("message", "Failed to list files")}
        file_list = file_list_resp["files"]

        all_content = {}
        failed_files = []
        for path in file_list:
            logger.info(f"Fetching content for file: {path}")
            result = get_file_contents(repo=repo_id, file_path=path, owner=owner)
            logger.info(f"Result for {path}: {result['status']}")
            if result["status"] == "success":
                all_content[path] = result["content"]
            else:
                failed_files.append(path)
                logger.warning(f"Failed to get content for {path}: {result.get('message', 'Unknown error')}")

        request.app.state.file_contents = all_content
        request.app.state.repo_id = repo_id
        
        logger.info(f"Successfully loaded {len(all_content)} files, {len(failed_files)} failed")
        return {
            "status": "success", 
            "files_loaded": len(all_content),
            "files_failed": len(failed_files),
            "failed_files": failed_files
        }
    except Exception as e:
        logger.exception(f"Exception during repository loading: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/ingest")
async def ingest_repo(request: Request):
    logger.info("Starting repository ingestion")
    
    file_contents = getattr(request.app.state, "file_contents", None)
    repo_id = getattr(request.app.state, "repo_id", None)

    if not file_contents or not repo_id:
        return {"status": "error", "message": "No repo loaded. Please call /load_repo first."}
    
    logger.info(f"Ingesting {len(file_contents)} files for repo {repo_id}")
    
    try:
        embedder = request.app.state.jina_embedder
        result = process_repo(file_contents, repo_id, embedder)
        return {"status": "success", "message": "Ingestion complete.", "chunks_processed": result.get("chunks_processed", 0)}
    except Exception as e:
        return {"status": "error", "message": f"Ingestion failed: {str(e)}"}


@router.post("/search")
async def search(request: Request, query: str, file_path: str = None):
    logger.info(f"Performing search with query: '{query}'")
    
    try:
        search_service = request.app.state.search_service
        repo_id = getattr(request.app.state, "repo_id", None)

        if not repo_id:
            logger.error("No repo_id found for search")
            return {"status": "error", "message": "No repository loaded. Please load a repository first."}

        results = search_service.semantic_search(
            query=query,
            repo_id=repo_id,
            file_path=file_path
        )
        
        logger.info(f"Search completed, found {len(results.points) if hasattr(results, 'points') else 'unknown'} results")
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return {"status": "error", "message": f"Search failed: {str(e)}"}


@router.get("/collections")
def list_collections(request: Request):
    try:
        client = request.app.state.qdrant
        collections = client.get_collections()
        return {"status": "success", "collections": collections}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list collections: {str(e)}"}


@router.get("/status")
def get_status(request: Request):
    """Get the current status of the loaded repository and services"""
    repo_id = getattr(request.app.state, "repo_id", None)
    file_contents = getattr(request.app.state, "file_contents", None)
    
    return {
        "status": "success",
        "repo_loaded": repo_id is not None,
        "repo_id": repo_id,
        "files_loaded": len(file_contents) if file_contents else 0,
        "services_available": {
            "qdrant": hasattr(request.app.state, "qdrant"),
            "embedder": hasattr(request.app.state, "jina_embedder"),
            "search_service": hasattr(request.app.state, "search_service")
        }
    }