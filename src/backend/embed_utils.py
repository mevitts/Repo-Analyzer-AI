import requests
from qdrant_client.models import PointStruct
from src.backend.qdrant_client import qdrant_client
import uuid

JINA_API_URL = 'https://api.jina.ai/v1/embeddings'
JINA_HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer jina_0ca89f52b6494763b09d4c006e91718cwDeN3kUByO9ZmKtLHlf4KFp96RBc' #example token
}


def embed_chunks(chunk_list):
    """
    Given a list of chunks, call the jina-embeddings-v3 API to embed each chunk
    """
    input_text = [chunk['content'] for chunk in chunk_list]

    data = {
        "model": "jina-embeddings-v3",
        "task": "text-matching",
        "input": input_text
    }

    response = requests.post(JINA_API_URL, headers=JINA_HEADERS, json=data)
    response.raise_for_status()

    vecs_with_metadata = []
    for i, emb_data in enumerate(response.json()["data"]):
        vector = emb_data["embedding"]
        metadata = chunk_list[i]["metadata"]
        vecs_with_metadata.append((vector, metadata))
    
    return vecs_with_metadata


def upsert_embeddings(qdrant_client, collection_name, repo_id, vecs_with_metadata):
    """
    Upsert embeddings into Qdrant with repo_id as a filterable field.
    """
    points = []
    for vector, metadata in vecs_with_metadata:
        metadata["repo_id"] = repo_id
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=metadata
            )
        )

    qdrant_client.upsert(
        collection_name=collection_name,
        points=points
    )
