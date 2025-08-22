import logging
from src.backend.utils.chunking_utils import chunk_repo
from src.backend.qdrant_client import get_qdrant_client

logger = logging.getLogger(__name__)

def process_repo(file_contents: dict, repo_id: str, embedder):
    """
    Process a repository by chunking files and storing embeddings
    
    Returns:
        dict: Information about the processing results
    """
    chunks = chunk_repo(file_contents)
    
    if not chunks:
        return {"chunks_processed": 0, "message": "No chunks generated"}
    
    client = get_qdrant_client()
    collection_name = f"repo_{repo_id}"

    if not client.collection_exists(collection_name=collection_name):
        from qdrant_client.models import VectorParams, Distance
        client.create_collection(
            collection_name=collection_name, 
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )
        logger.info(f"Created new collection: {collection_name}")
    else:
        logger.info(f"Using existing collection: {collection_name}")

    embeddings = embedder.embed_chunks(chunks)
    embedder.upsert_embeddings(client, collection_name, repo_id, embeddings)

    return {
        "chunks_processed": len(chunks),
        "collection_name": collection_name,
        "message": f"Successfully processed {len(chunks)} chunks"
    }