import logging
from src.backend.utils.chunking_utils import chunk_repo

logger = logging.getLogger(__name__)

def process_repo(file_contents: dict, repo_id: str, embedder):
    from src.backend.qdrant_client import get_qdrant_client
    logger = logging.getLogger(__name__)

    chunks = chunk_repo(file_contents)
    for chunk in chunks[:5]:
        print(f"[process_repo] Sample chunk metadata: {chunk.get('metadata', {})}")

    logger.info(f"[process_repo] Chunked {len(file_contents)} files into {len(chunks)} chunks for repo {repo_id}")

    if not chunks:
        logger.warning(f"[process_repo] No chunks generated for repo {repo_id}")
        return {"chunks_processed": 0, "message": "No chunks generated"}

    client = get_qdrant_client()
    collection_name = f"repo_{repo_id}"

    if not client.collection_exists(collection_name=collection_name):
        from qdrant_client.models import VectorParams, Distance
        client.create_collection(
            collection_name=collection_name, 
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )
        logger.info(f"[process_repo] Created new Qdrant collection: {collection_name}")
    else:
        logger.info(f"[process_repo] Using existing Qdrant collection: {collection_name}")

    embeddings = embedder.embed_chunks(chunks)
    logger.info(f"[process_repo] Got {len(embeddings)} embeddings for repo {repo_id}")

    embedder.upsert_embeddings(client, collection_name, repo_id, embeddings)
    logger.info(f"[process_repo] Upserted embeddings into Qdrant collection: {collection_name}")

    return {
        "chunks_processed": len(chunks),
        "collection_name": collection_name,
        "message": f"Successfully processed {len(chunks)} chunks"
    }