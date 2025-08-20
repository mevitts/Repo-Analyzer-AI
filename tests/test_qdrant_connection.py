import pytest
from src.backend.qdrant_client import get_qdrant_client


def test_qdrant_connection():
    client = get_qdrant_client()
    collection_name = "test_collection"

    if collection_name not in [c.name for c in client.get_collections().collections]:        
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config={"size": 3, "distance": "Cosine"}
        )

    client.upsert(
        collection_name=collection_name,
        points=[
            {
                "id": 1,
                "vector": [0.1, 0.2, 0.3],
                "payload": {"test": "yes"}
            }
        ]
    )

    result = client.query_points(
        collection_name=collection_name,
        query=[0.1, 0.2, 0.3],
        limit=1
    )

    collections = client.get_collections()
    print("Qdrant collections:", collections)

    assert hasattr(collections, 'collections'), "Qdrant did not return collections!"
    assert any(c.name == collection_name for c in collections.collections), "Collection not found!"
