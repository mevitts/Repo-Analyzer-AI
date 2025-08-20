from fastapi import APIRouter, Request
from src.backend.services.embedding_service import process_repo
from src.backend.embed_utils import JinaEmbedder
from src.backend.tools import list_files, get_file_contents

router = APIRouter()


@router.post("/load_repo")
async def load_repo(request: Request, repo_id: str, owner: str):
    """
    Endpoint to load a repository before processing its contents.
    """
    file_list_resp = list_files(repo=repo_id, owner=owner)
    if file_list_resp["status"] != "success":
        return {"status": "error", "message": file_list_resp.get("message", "Failed to list files")}
    file_list = file_list_resp["files"]
    all_content = {}
    for path in file_list:
        result = get_file_contents(repo=repo_id, file_path=path, owner=owner)
        if result["status"] == "success":
            all_content[path] = result["content"]

    request.app.state.file_contents = all_content
    request.app.state.repo_id = repo_id
    return {"status": "success", "files_loaded": len(all_content)}


@router.post("/ingest")
async def ingest_repo(request: Request):
    file_contents = getattr(request.app.state, "file_contents", None)
    repo_id = getattr(request.app.state, "repo_id", None)
    if not file_contents or not repo_id:
        return {"status": "error", "message": "No repo loaded. Please call /load_repo first."}
    embedder = JinaEmbedder(api_key="your_api_key")
    process_repo(file_contents, repo_id, embedder)
    return {"status": "success", "message": "Ingestion complete."}


@router.get("/collections")
def list_collections(request: Request):
    client = request.app.state.qdrant
    return client.get_collections()