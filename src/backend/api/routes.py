from fastapi import APIRouter, Request
import logging
from src.backend.services.embedding_service import process_repo
from src.backend.utils.embed_utils import JinaEmbedder
from src.backend.utils.file_utils import list_files, get_file_contents
from src.backend.utils import summarization_utils
import os

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/load_repo")
async def load_repo(request: Request, repo_id: str, owner: str):
    logger.info(f"Loading repository {repo_id} for owner {owner}")
    try:
        # REMOVE Qdrant collection existence check and always fetch files
        file_list_resp = list_files(repo=repo_id, owner=owner)
        logger.info(f"File list response: Completed")
        if file_list_resp["status"] != "success":
            logger.error(f"Failed to list files: {file_list_resp.get('message')}")
            return {"status": "error", "message": file_list_resp.get("message", "Failed to list files")}
        file_list = file_list_resp["files"]

        all_content = {}
        failed_files = []
        for path in file_list:
            logger.info(f"Fetching content for file: {path}")
            result = get_file_contents(repo=repo_id, file_path=path, owner=owner)
            logger.info(f"Result for {path}: {result['status']}")
            if result["status"] == "success":
                all_content[path] = result["content"]
            else:
                failed_files.append(path)
                logger.warning(f"Failed to get content for {path}: {result.get('message', 'Unknown error')}")

        request.app.state.file_contents = all_content
        request.app.state.repo_id = repo_id

        logger.info(f"[load_repo] file_contents keys: {list(all_content.keys())[:5]}... total: {len(all_content)}")
        logger.info(f"[load_repo] request.app.state.file_contents keys: {list(request.app.state.file_contents.keys())[:5]}... total: {len(request.app.state.file_contents)}")

        logger.info(f"Successfully loaded {len(all_content)} files, {len(failed_files)} failed")
        return {
            "status": "success", 
            "files_loaded": len(all_content),
            "files_failed": len(failed_files),
            "failed_files": failed_files,
            "file_contents": all_content
        }
    except Exception as e:
        logger.exception(f"Exception during repository loading: {e}")
        return {"status": "error", "message": str(e)}


from fastapi import Body

@router.post("/ingest")
async def ingest_repo(
    request: Request,
    repo_id: str = Body(...),
    file_contents: dict = Body(None)
):
    client = request.app.state.qdrant
    collection_name = f"repo_{repo_id}"
    if collection_name in [c.name for c in client.get_collections().collections]:
        client.delete_collection(collection_name=collection_name)
    # Now proceed with ingest
    logger.info(f"Starting repository ingestion for repo_id={repo_id}")

    # Prefer file_contents from body, fallback to app.state
    if file_contents is None:
        file_contents = getattr(request.app.state, "file_contents", None)
    state_repo_id = getattr(request.app.state, "repo_id", None)

    # Debug: Log file_contents keys and length before ingest
    if file_contents is not None:
        logger.info(f"[ingest] file_contents keys: {list(file_contents.keys())[:5]}... total: {len(file_contents)}")
    else:
        logger.warning("[ingest] file_contents is None in app state")

    if not file_contents or (state_repo_id and state_repo_id != repo_id):
        logger.warning("No file_contents provided or repo_id mismatch. Ingest expects file_contents in body or /load_repo to be called first in this session.")
        return {"status": "error", "message": "No repo loaded. Please call /load_repo first or provide file_contents."}

    logger.info(f"Ingesting {len(file_contents)} files for repo {repo_id}")

    try:
        embedder = request.app.state.jina_embedder
        result = process_repo(file_contents, repo_id, embedder)
        return {"status": "success", "message": "Ingestion complete.", "chunks_processed": result.get("chunks_processed", 0)}
    except Exception as e:
        return {"status": "error", "message": f"Ingestion failed: {str(e)}"}


@router.post("/search")
async def search(request: Request, query: str, file_path: str = None):
    logger.info(f"Performing search with query: '{query}'")
    
    try:
        search_service = request.app.state.search_service
        repo_id = getattr(request.app.state, "repo_id", None)

        if not repo_id:
            logger.error("No repo_id found for search")
            return {"status": "error", "message": "No repository loaded. Please load a repository first."}

        results = search_service.semantic_search(
            query=query,
            repo_id=repo_id,
            file_path=file_path
        )
        
        logger.info(f"Search completed, found {len(results.points) if hasattr(results, 'points') else 'unknown'} results")
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return {"status": "error", "message": f"Search failed: {str(e)}"}


@router.get("/collections")
def list_collections(request: Request):
    try:
        client = request.app.state.qdrant
        collections = client.get_collections()
        return {"status": "success", "collections": collections}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list collections: {str(e)}"}


@router.get("/status")
def get_status(request: Request):
    """Get the current status of the loaded repository and services"""
    repo_id = getattr(request.app.state, "repo_id", None)
    file_contents = getattr(request.app.state, "file_contents", None)
    
    return {
        "status": "success",
        "repo_loaded": repo_id is not None,
        "repo_id": repo_id,
        "files_loaded": len(file_contents) if file_contents else 0,
        "services_available": {
            "qdrant": hasattr(request.app.state, "qdrant"),
            "embedder": hasattr(request.app.state, "jina_embedder"),
            "search_service": hasattr(request.app.state, "search_service")
        }
    }
    

@router.post("/summarize_repo")
async def summarize_repo(
    request: Request, 
    repo_id: str, 
    max_points: int = 1000, 
    cluster_k: int = 10, 
    reps_per_cluster: int = 3, 
    max_snippets: int = 5
):
    """
    Summarize the repository and its contents.
    Improved logging and error handling for easier debugging.
    """
    logger.info(f"[summarize_repo] Called for repo_id={repo_id}")

    client = request.app.state.qdrant
    collection_name = f"repo_{repo_id}"
    gemini_key = os.getenv("GOOGLE_API_KEY", "")
    if not gemini_key:
        logger.warning("[summarize_repo] GOOGLE_API_KEY not set. Summarization may fail if required.")
        raise RuntimeError("GOOGLE_API_KEY environment variable is not set.")

    # Defensive initialization
    repo_metrics = {}
    repo_summary = {}
    cluster_summaries = []

    if not hasattr(request.app.state, "atlas_cache"):
        request.app.state.atlas_cache = {}
    if not hasattr(request.app.state, "file_nodes_cache"):
        request.app.state.file_nodes_cache = {}

    try:
        logger.info(f"[summarize_repo] Attempting to fetch points from Qdrant collection: {collection_name}")
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [c.name for c in getattr(collections, "collections", [])]
        if collection_name not in collection_names:
            logger.error(f"[summarize_repo] Qdrant collection '{collection_name}' does not exist. Available: {collection_names}")
            raise RuntimeError(f"Qdrant collection '{collection_name}' does not exist. Did ingestion succeed?")

        points, _ = client.scroll(collection_name=collection_name, limit=max_points, with_vectors=True)
        logger.info(f"[summarize_repo] Retrieved {len(points)} points from Qdrant.")
        for i, pt in enumerate(points[:5]):
            logger.info(f"[summarize_repo] Point {i} vector type: {type(getattr(pt, 'vector', None))} length: {len(getattr(pt, 'vector', []) or [])}")

        if not points:
            logger.error(f"[summarize_repo] No points found in collection '{collection_name}'.")
            raise RuntimeError(f"No points found in Qdrant collection '{collection_name}'.")

        content_hash = summarization_utils.compute_content_hash(points)
        cache_key = (repo_id, content_hash)

        if not hasattr(request.app.state, "summarization_cache"):
            cache = request.app.state.summarization_cache = {}
        else:
            cache = request.app.state.summarization_cache

        if cache_key in cache:
            logger.info(f"[summarize_repo] Returning cached summary for {repo_id} version {content_hash}")
            return cache[cache_key]

        logger.info(f"[summarize_repo] Downsampling points for clustering...")
        sampled = summarization_utils.stratified_downsample(points, n_max=max_points)
        logger.info(f"[summarize_repo] Sampled {len(sampled)} points.")

        X, meta = summarization_utils.preprocess_points(sampled)
        logger.info(f"[summarize_repo] Preprocessed points. X shape: {X.shape}, meta count: {len(meta)}")
        
        if X.size == 0 or len(meta) == 0:
            logger.error(f"[summarize_repo] No valid points after preprocessing. Aborting summarization.")
            return {
                "repo_id": repo_id,
                "metrics": repo_metrics,
                "repo_summary": repo_summary,
                "clusters": cluster_summaries,
                "error": "No valid points for summarization after preprocessing."
            }
            
        labels, centroids = summarization_utils.run_kmeans(X, n_clusters=cluster_k)
        logger.info(f"[summarize_repo] Ran KMeans clustering. Labels: {set(labels)}, Centroids shape: {centroids.shape}")

        meta_with_cluster, clusters = summarization_utils.assign_clusters_and_scores(X, meta, labels, centroids)
        logger.info(f"[summarize_repo] Assigned clusters and scores.")
        request.app.state.atlas_cache[repo_id] = meta_with_cluster

        cluster_labels = summarization_utils.get_clusters_and_labels(meta_with_cluster, clusters, n_labels=reps_per_cluster)
        logger.info(f"[summarize_repo] Built cluster labels.")

        cluster_summaries = []
        for cluster_id, info in cluster_labels.items():
            logger.info(f"[summarize_repo] Summarizing cluster {cluster_id}...")
            summary = summarization_utils.summarize_cluster(info, repo_id=repo_id, api_key=gemini_key)
            cluster_summaries.append(summary)

        repo_metrics = {
            "points": len(points),
            "clusters": len(clusters),
            "files": len({m["filepath"] for m in meta}),
            "top_dirs": list({m["dirpath"] for m in meta})[:5]
        }
        logger.info(f"[summarize_repo] Repo metrics: {repo_metrics}")

        repo_summary = summarization_utils.summarize_repo(cluster_summaries, repo_metrics=repo_metrics)
        logger.info(f"[summarize_repo] Repo summary generated.")

        summarization_utils.clusters_to_qdrant(client, collection_name=collection_name, meta_with_cluster=meta_with_cluster)
        logger.info(f"[summarize_repo] Persisted cluster IDs to Qdrant.")

        # Build and store file-level nodes
        file_nodes = summarization_utils.aggregate_chunks_to_files(meta_with_cluster)
        request.app.state.file_nodes_cache[repo_id] = file_nodes

        cache[cache_key] = {
            "repo_id": repo_id,
            "metrics": repo_metrics,
            "repo_summary": repo_summary,
            "clusters": cluster_summaries
        }
        logger.info(f"[summarize_repo] Caching and returning summary for {repo_id}.")
        return cache[cache_key]

    except Exception as e:
        logger.error(f"[summarize_repo] Exception: {type(e).__name__}: {e}", exc_info=True)
        return {
            "repo_id": repo_id,
            "metrics": repo_metrics,
            "repo_summary": repo_summary,
            "clusters": cluster_summaries,
            "error": f"{type(e).__name__}: {e}"
        }

@router.post("/atlas_cluster")
async def atlas_cluster(
    request: Request,
    repo_id: str,
    max_points: int = 1000,
    cluster_k: int = 10
):
    """
    Cluster repo points and cache for Atlas, without running LLM summarization.
    """
    logger.info(f"[atlas_cluster] Clustering for repo {repo_id}")
    client = request.app.state.qdrant
    collection_name = f"repo_{repo_id}"

    collections = client.get_collections()
    collection_names = [c.name for c in getattr(collections, "collections", [])]
    if collection_name not in collection_names:
        logger.error(f"[atlas_cluster] Qdrant collection '{collection_name}' does not exist.")
        return {"status": "error", "message": f"Qdrant collection '{collection_name}' does not exist."}

    points, _ = client.scroll(collection_name=collection_name, limit=max_points, with_vectors=True)
    if not points:
        logger.error(f"[atlas_cluster] No points found in collection '{collection_name}'.")
        return {"status": "error", "message": f"No points found in Qdrant collection '{collection_name}'."}

    X, meta = summarization_utils.preprocess_points(points)
    if X.size == 0 or len(meta) == 0:
        logger.error(f"[atlas_cluster] No valid points after preprocessing.")
        return {"status": "error", "message": "No valid points for clustering."}

    labels, centroids = summarization_utils.run_kmeans(X, n_clusters=cluster_k)
    meta_with_cluster, clusters = summarization_utils.assign_clusters_and_scores(X, meta, labels, centroids)

    if not hasattr(request.app.state, "atlas_cache"):
        request.app.state.atlas_cache = {}
    request.app.state.atlas_cache[repo_id] = meta_with_cluster

    logger.info(f"[atlas_cluster] Cached cluster assignments for repo {repo_id}")
    return {"status": "success", "message": "Cluster assignments cached for Atlas."}


@router.post("/atlas_pack")
async def atlas_pack(
    request: Request,
    repo_id: str,
    similarity_threshold: float = 0.7,
    k_sim: int = 3
):
    """Build and return the atlas pack for a repo (file-level nodes)."""
    logger.info(f"[atlas_pack] Building atlas pack for repo {repo_id}")

    # Check for chunk-level meta
    meta_with_cluster = getattr(request.app.state, "atlas_cache", {}).get(repo_id)
    if not meta_with_cluster:
        logger.error(f"[atlas_pack] No cached chunk-level meta for repo {repo_id}. Run /summarize_repo first.")
        return {"status": "error", "message": "No cached chunk-level meta. Run /summarize_repo first."}

    # Check for file-level nodes
    file_nodes_cache = getattr(request.app.state, "file_nodes_cache", {})
    file_nodes = file_nodes_cache.get(repo_id)
    if not file_nodes:
        logger.warning(f"[atlas_pack] No cached file-level nodes for repo {repo_id}. Rebuilding from chunk meta.")
        # Rebuild file-level nodes if missing
        file_nodes = summarization_utils.aggregate_chunks_to_files(meta_with_cluster)
        if not hasattr(request.app.state, "file_nodes_cache"):
            request.app.state.file_nodes_cache = {}
        request.app.state.file_nodes_cache[repo_id] = file_nodes

    try:
        # Only use file-level nodes for the main Atlas
        atlas_pack = summarization_utils.build_atlas_pack(
            file_nodes,
            repo_id=repo_id,
            similarity_threshold=similarity_threshold,
            k_sim=k_sim
        )
        logger.info(f"[atlas_pack] Atlas pack built for repo {repo_id} (file-level nodes: {len(file_nodes)})")
        return {"repo_id": repo_id, "atlas_pack": atlas_pack}
    except Exception as e:
        logger.error(f"[atlas_pack] Atlas pack build failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.post("/file_atlas")
async def file_atlas(
    request: Request,
    repo_id: str = Body(...),
    filepath: str = Body(...),
    similarity_threshold: float = Body(0.8),
    k_sim: int = Body(3)
):
    logger = logging.getLogger(__name__)
    logger.info(f"[file_atlas] Requested for repo_id={repo_id}, filepath={filepath}")
    meta_with_cluster = getattr(request.app.state, "atlas_cache", {}).get(repo_id)
    if not meta_with_cluster:
        logger.warning(f"[file_atlas] No cached chunk-level meta for repo {repo_id}")
        return {"status": "error", "message": "No cached chunk-level meta. Run /summarize_repo first."}
    # Only use chunk-level meta for the chunk Atlas
    file_chunks = [m for m in meta_with_cluster if m["filepath"] == filepath]
    logger.info(f"[file_atlas] Found {len(file_chunks)} chunks for file {filepath}")
    if not file_chunks:
        logger.warning(f"[file_atlas] No chunks found for file {filepath}")
        return {"status": "error", "message": "No chunks found for this file."}
    try:
        atlas_pack = summarization_utils.build_atlas_pack(
            file_chunks,
            repo_id=repo_id,
            similarity_threshold=similarity_threshold,
            k_sim=k_sim
        )
        logger.info(f"[file_atlas] Built chunk-level atlas with {len(atlas_pack['nodes'])} nodes and {len(atlas_pack['edges'])} edges")
        return {"atlas_pack": atlas_pack}
    
    except Exception as e:
        logger.error(f"[file_atlas] Failed to build chunk-level atlas: {str(e)}")
        return {"status": "error", "message": str(e)}