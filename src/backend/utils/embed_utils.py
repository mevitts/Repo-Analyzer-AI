import requests
from qdrant_client.models import PointStruct
import uuid
from src.backend.config import JINA_API_URL, JINA_HEADERS


class JinaEmbedder:
    def __init__(self, api_key, model='jina-embeddings-v3'):
        self.api_url = JINA_API_URL
        self.headers = {**JINA_HEADERS, "Authorization": f"Bearer {api_key}"}
        self.model = model

    def embed_chunks(self, chunk_list):
        """
        Given a list of chunks, call the jina-embeddings-v3 API to embed each chunk
        """
        input_text = [chunk['content'] for chunk in chunk_list]
        data = {
            "model": self.model,
            "task": "text-matching",
            "input": input_text
        }

        response = requests.post(self.api_url, headers=self.headers, json=data)
        response.raise_for_status()

        vecs_with_metadata = []
        for i, emb_data in enumerate(response.json()["data"]):
            vector = emb_data["embedding"]
            metadata = chunk_list[i]["metadata"]
            if not vector or not isinstance(vector, (list, tuple)):
                print(f"[embed_chunks] WARNING: Empty or invalid vector for chunk {i}")
            else:
                print(f"[embed_chunks] Vector {i} length: {len(vector)} type: {type(vector)}")
            vecs_with_metadata.append((vector, metadata))
        print(f"[embed_chunks] Returning {len(vecs_with_metadata)} vectors")
        
        return vecs_with_metadata


    def embed_query(self, query: str):
        """
        Embed a query using the jina-embeddings-v3 API.
        """
        data = {
            "model": self.model,
            "task": "text-matching",
            "input": [query]
        }

        response = requests.post(self.api_url, headers=self.headers, json=data)
        response.raise_for_status()

        return response.json()["data"][0]["embedding"]


    def upsert_embeddings(self, qdrant_client, collection_name, repo_id, vecs_with_metadata):
        """
        Upsert embeddings into Qdrant with repo_id as a filterable field.
        """
        points = []
        for i, (vector, metadata) in enumerate(vecs_with_metadata):
            metadata["repo_id"] = repo_id
            if not vector or not isinstance(vector, (list, tuple)):
                print(f"[upsert_embeddings] WARNING: Skipping upsert for missing/invalid vector at idx {i}: {vector}")
                continue
            print(f"[upsert_embeddings] Upserting vector idx {i} length: {len(vector)}")
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=list(map(float, vector)),
                    payload=metadata
                )
            )
            
        collection_info = qdrant_client.get_collection(collection_name)
        
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )
