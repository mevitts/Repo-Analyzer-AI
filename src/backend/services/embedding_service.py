from src.backend.chunking_utils import chunk_repo
from src.backend.embed_utils import embed_chunks
from src.backend.qdrant_client import get_qdrant_client

def process_repo(file_contents: dict, repo_id: str, embedder):
    chunks = chunk_repo(file_contents)
    client = get_qdrant_client()
    collection_name = f"repo_{repo_id}"

    if not client.collection_exists(collection_name=collection_name):
        client.create_collection(
            collection_name=collection_name, 
            vectors_config={"distance": "Cosine"}
        )

    embeddings = embedder.embed_chunks(chunks)
    embedder.upsert_embeddings(client, collection_name, repo_id, embeddings)