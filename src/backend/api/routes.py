from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/collections")
def list_collections(request: Request):
    client = request.app.state.qdrant
    return client.get_collections()