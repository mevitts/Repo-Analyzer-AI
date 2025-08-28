from tkinter import N
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchText
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
class SearchService:
    def __init__(self, qdrant: QdrantClient, embedder, repo_id: str):
        self.qdrant = qdrant
        self.embedder = embedder
        self.repo_id = repo_id

    def semantic_search(self, query: str, repo_id: str = None, file_path: str = None, n_max: int = 10):
        """
        Perform a semantic search on the repo with optional strict filtering.
        - If query is provided: use embedding search.
        - If no query: just apply filter (returns all matching points).
        """
        filter_obj = self.build_filter(repo_id=repo_id, file_path=file_path)
        collection_name = f'repo_{repo_id or self.repo_id}'

        if query:
            query_embedding = self.embedder.embed_query(query)
            results = self.qdrant.query_points(
                collection_name=collection_name,
                query=query_embedding,
                query_filter=filter_obj,
                limit=n_max,
                with_vectors=True
            )
        else:
            results = self.qdrant.scroll(
                collection_name=collection_name,
                scroll_filter=filter_obj,
                with_payload=True,
                limit=n_max,
                with_vectors=True
            )
        logger.info(f"Raw Qdrant search result: {results}")

        return results


    def build_filter(self, repo_id: str = None, file_path: str = None):
        """
        Filter results based on specific criteria.
        This can be extended to include more complex filtering logic.
        """
        musts = []
        
        if repo_id:
            musts.append(FieldCondition(key="repo_id", match=MatchValue(value=repo_id)))

        if file_path:
            musts.append(FieldCondition(key="file_path", match=MatchValue(value=file_path)))

        if musts:
            return Filter(must=musts)
        else:
            return None


    def fetch_all_points(self, repo_id: str = None, n_max: int = 3000):
        """
        Fetch all points from the Qdrant collection for a specific repo.
        """
        filter_obj = self.build_filter(repo_id=repo_id)
        collection_name = f'repo_{repo_id or self.repo_id}'

        results = self.qdrant.scroll(
            collection_name=collection_name,
            scroll_filter=filter_obj,
            with_payload=True,
            with_vectors=True,
            limit=n_max
        )
        logger.info(f"Raw Qdrant fetch all points result: {results}")

        return results
