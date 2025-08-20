from qdrant_client import QdrantClient

_qdrant_client = None 

def get_qdrant_client():
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(
            host="localhost",
            port=6333
        )
    return _qdrant_client

def get_collections():
    client = get_qdrant_client()
    return client.get_collections()
