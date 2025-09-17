import hashlib
import random
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple
from pydantic import Strict
import requests
import os
import numpy as np
from scipy import cluster
from sklearn.cluster import KMeans
import jsonschema
from jsonschema import ValidationError
import json
import re
from umap import UMAP
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

cluster_schema = {"cluster_id": "<id>", 
                  "title": "<short human label>", 
                  "summary": "<2-4 sentences>", 
                  "key_files": ["path/a.py", "path/b.py"], 
                  "notable_symbols": ["ClassX", "function_y"]
                }

repo_schema = {
    "repo_id": "<string>",
    "metrics": {
        "points": "<int>",
        "clusters": "<int>",
        "files": "<int>",
        "top_dirs": ["<string>", "<string>"]
    },
    "repo_summary": {
        "title": "<short repo label>",
        "overview": "<1-paragraph summary>",
        "sections": [
            {"title": "<cluster title>", "summary": "<one-line what it does>"}
        ]
    },
    "clusters": [
        {
            "cluster_id": "<id>",
            "title": "<short human label>",
            "summary": "<2-4 sentences>",
            "key_files": ["path/a.py", "path/b.py"],
            "notable_symbols": ["ClassX", "function_y"],
            "representatives": [
                {"point_id": "...", "filepath": "...", "start": "<int>", "end": "<int>", "preview": "code excerpt ..."}
            ]
        }
    ],
    "atlas_pack": {
        "nodes": [{"id": "<point_id>", "score": "<float>"}],
        "edges": [{"source": "<point_id>", "target": "<point_id>", "type": "semantic", "weight": "<float>"}]
    }
}

def gemini_summarize(prompt: str, api_key: Optional[str] = None, model: str = "models/gemini-1.5-pro-latest") -> str:
    """
    Calls Gemini API to summarize a prompt. Returns the summary string.
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Gemini API key not provided.")
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-001', 
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2,
                    max_output_tokens=512,),
        )
        if response.text:
            return response.text
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}")
    '''
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return str(result)
'''
#groups points by filepath
def stratified_downsample(points: List[Dict[str, Any]], n_max: int) -> List[Dict[str, Any]]:
    """
    Downsample points stratified by filepath so all files are represented.
    """
    if len(points) <= n_max:
        return points
    
    #dictionary of filepath and their points
    by_file = defaultdict(list)
    for pt in points:
        fp = pt.get("payload", {}).get("filepath", "unknown")
        by_file[fp].append(pt)
    
    files = list(by_file.keys())
    quota = max(1, n_max // len(files))
    sampled = []
    for pts in by_file.values():
        if len(pts) <= quota:
            sampled.extend(pts)
        else:
            sampled.extend(random.sample(pts, quota))
            
    # If we have less than n_max, fill up with randoms from leftovers 
    if len(sampled) < n_max:
        leftovers = [pt for pts in by_file.values() for pt in pts if pt not in sampled]
        sampled.extend(random.sample(leftovers, min(n_max - len(sampled), len(leftovers))))
        
    return sampled[:n_max]


def preprocess_points(points: List[Dict[str, Any]]):
    """
    Given a list of Qdrant points, extract and L2-normalize vectors, and build meta[] with filepath, dirpath, filename.
    Returns: X (np.ndarray), meta (List[Dict])
    """
    logger = logging.getLogger(__name__)
    X = []
    meta = []
    logger.info(f"[preprocess_points] Received {len(points)} points")
    for idx, pt in enumerate(points):
        if isinstance(pt, dict):
            vector = pt.get("vector")
            payload = pt.get("payload", {})
            point_id = pt.get("id")
        elif hasattr(pt, "vector") and hasattr(pt, "payload"):
            vector = pt.vector
            payload = pt.payload
            point_id = getattr(pt, "id", None)
        else:
            logger.warning(f"[preprocess_points] Skipping point {idx}: unrecognized type {type(pt)}")
            continue

        if vector is None or not isinstance(vector, (list, tuple, np.ndarray)) or len(vector) == 0:
            logger.warning(f"[preprocess_points] Skipping point {idx}: missing or invalid vector")
            continue
        X.append(vector)
        filepath = payload.get("filepath", "")
        parts = filepath.split("/")
        dirpath = "/".join(parts[:2]) if len(parts) > 1 else parts[0]
        filename = os.path.basename(filepath)
        meta.append({
            "id": point_id,
            "filepath": filepath,
            "dirpath": dirpath,
            "filename": filename,
            "payload": payload,
            "vector": vector 
        })
    if not X:
        # Return a 2D empty array with shape (0, 0)
        return np.empty((0, 0)), []
    X = np.array(X)
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    # L2 normalize
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    X = X / np.clip(norms, 1e-8, None)
    return X, meta


def run_kmeans(X: np.ndarray, n_clusters: int = 10, random_state: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Runs KMeans clustering on X.
    Returns: (labels, centroids)
    """
    # Guard: if X is empty, return empty arrays
    if X.size == 0 or X.shape[0] == 0:
        return np.array([]), np.array([])
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init="auto")
    labels = kmeans.fit_predict(X)
    centroids = kmeans.cluster_centers_
    return labels, centroids


def assign_clusters_and_scores(
    X: np.ndarray,
    meta: List[Dict[str, Any]],
    labels: np.ndarray,
    centroids: np.ndarray
) -> Tuple[List[Dict[str, Any]], Dict[int, Dict[str, Any]]]:
    """
    Assigns cluster_id to each meta entry and computes distances to centroid.
    Returns:
        meta_with_cluster: meta list with 'cluster_id' and 'distance_to_centroid' added
        clusters: dict of cluster_id -> {centroid, member_indices, member_ids}
    """
    if X.size == 0 or labels.size == 0 or centroids.size == 0:
        return [], {}

    # centroid can be None or a numpy array
    clusters: Dict[int, Dict[str, Any]] = defaultdict(
        lambda: {"centroid": None, "member_indices": [], "member_ids": []}
    )
    meta_with_cluster = []

    for i, (m, label) in enumerate(zip(meta, labels)):
        m = dict(m)  # make a copy
        m["cluster_id"] = int(label)
        dist = np.linalg.norm(X[i] - centroids[label])
        m["distance_to_centroid"] = float(dist)
        meta_with_cluster.append(m)

        clusters[label]["member_indices"].append(i)
        clusters[label]["member_ids"].append(m["id"])
        clusters[label]["centroid"] = centroids[label]

    return meta_with_cluster, clusters


def get_clusters_and_labels(meta_with_cluster: List[Dict[str, Any]], clusters: Dict[int, Dict[str, Any]], n_labels: Optional[int] = None, n_min: int = 3) -> Dict[int, Dict[str, Any]]:
    """
    For each cluster, get top n_labels filenames as labels.
    n_labels: max number of representatives per cluster (token guard). Default: 6.
    Returns: dict of cluster_id -> {representatives, label, top_dirs, top_files}
    """
    misc_members = []
    cluster_labels = {}
    for cluster_id, info in clusters.items():
        members = [meta_with_cluster[i] for i in info["member_indices"]]
        if len(members) <= n_min:
            misc_members.extend(members)
            continue
        # Sort members by distance to centroid
        members_sorted = sorted(members, key=lambda m: m["distance_to_centroid"])
        # Token guard: cap number of representatives per cluster to n_labels
        top_members = members_sorted[:n_labels]
        cluster_labels[cluster_id] = {
            "representatives": top_members,
            "label": top_members[0]["filename"] if top_members else None,
            "top_dirs": list({m["dirpath"] for m in top_members}),
            "top_files": list({m["filename"] for m in top_members}),
        }
        
        if misc_members:
            misc_sorted = sorted(misc_members, key=lambda m: m["distance_to_centroid"])
            misc_top = misc_sorted[:n_labels]
            cluster_labels["misc"] = {
                "representatives": misc_top,
                "label": "misc", 
                "top_dirs": list({m["dirpath"] for m in misc_top}),
                "top_files": list({m["filename"] for m in misc_top}),
            }

    return cluster_labels

def build_cluster_prompt(cluster_labels: dict, repo_id: str, max_snippet_chars: Optional[int] = None) -> str:
    """
    Build a prompt for a single cluster using its members, label, filepaths, line ranges, and any signature hints.
    max_snippet_chars: max length for code excerpts (token guard). Default: 600.
    """
    members = cluster_labels.get("representatives", [])
    proto_label = cluster_labels.get("label", "")
    prompt = f"Repo: {repo_id}\nCluster label: {proto_label}\n\n"
    key_files = cluster_labels.get("key_files", [])
    max_snippet_chars = max_snippet_chars if max_snippet_chars is not None else 600
    for mem in members:
        fp = mem.get("filepath", "")
        payload = mem.get("payload", {})
        start = payload.get("start_line_no", "?")
        end = payload.get("end_line_no", "?")
        excerpt = payload.get("excerpt", "")
        ancestors = payload.get("ancestors", "")
        signature = payload.get("signature", "")
        # Token guard: truncate excerpt to max_snippet_chars
        if excerpt and len(excerpt) > max_snippet_chars:
            excerpt = excerpt[:max_snippet_chars] + "..."
        if ancestors:
            prompt += f"Ancestors: {ancestors}\n"
        if signature:
            prompt += f"Signature: {signature}\n"
        prompt += f"Excerpt (truncated to {max_snippet_chars} chars):\n{excerpt}\n\n"
        prompt += (
            "Summarize what this group does (1-2 sentences), key responsibilities/data, and notable entry points.\n"
            "Only use facts present in the excerpts, file paths, and symbols. Do not speculate beyond the provided text.\n"
            f"Only mention files from this list: {key_files}. Do not reference any other files.\n"
            f"Strict JSON output: {cluster_schema}"
        )
    return prompt


def build_repo_prompt(cluster_jsons: List[dict], repo_metrics: dict) -> str:
    """
    Build a prompt for repo-level summary using all cluster summaries and repo metrics.
    """
    prompt = (
        "You are an expert code summarizer. Given the following clusters and repo metrics, "
        "produce a concise repo summary and cluster breakdown.\n\n"
        "Only use facts present in the excerpts, file paths, and symbols. Do not speculate beyond the provided text.\n"
        f"Repo metrics: {repo_metrics}\n\n"
        "Clusters:\n"
    )
    
    for c in cluster_jsons:
        title = c.get("title", "")
        summary = c.get("summary", "")
        key_files = c.get("key_files", [])
        prompt += f"- {title}: {summary}\n"
        if key_files:
            prompt += f"  Key files: {', '.join(key_files)}\n"
            
    prompt += f"""
        Output format (strict JSON):
        {repo_schema}
        Return only this JSON object.
    """
    
    return prompt


def summarize_cluster(cluster_info: dict, repo_id: str, api_key: Optional[str] = None, max_retries: int = 2) -> dict:
    """
    Summarize a cluster using LLM, with sanity check: if summary mentions files not in key_files, re-run with stricter prompt.
    """
    prompt = build_cluster_prompt(cluster_info, repo_id)
    last_summary = None
    last_error = None
    def clean_json_block(s):
        # Remove code block markers and leading/trailing whitespace
        s = s.strip()
        # Remove triple backtick code block (with or without 'json')
        s = re.sub(r'^```(?:json)?', '', s, flags=re.IGNORECASE).strip()
        s = re.sub(r'```$', '', s).strip()
        # If single quotes are used, replace with double quotes (be careful: only if it looks like a dict)
        if s.startswith('{') and "'" in s and '"' not in s:
            s = s.replace("'", '"')
        return s

    for attempt in range(max_retries):
        try:
            summary_str = gemini_summarize(prompt, api_key=api_key)
            logger.info(f"[summarize_cluster] Gemini raw output (attempt {attempt+1}): {summary_str}")
            cleaned = clean_json_block(summary_str)
            summary = json.loads(cleaned)
            jsonschema.validate(instance=summary, schema=cluster_schema)
            # check for mentioned files not in key_files
            key_files = set(cluster_info.get("key_files", []))
            file_pattern = r'[\w\-/]+\.py'
            found_files = set(re.findall(file_pattern, summary.get("summary", "")))
            extra_files = found_files - key_files
            if extra_files:
                logger.warning(f"Sanity check failed: summary mentions files not in key_files: {extra_files}")
                for file in extra_files:
                    summary["summary"] = summary["summary"].replace(file, "")
                continue
            return summary
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"[summarize_cluster] Attempt {attempt+1} failed to parse/validate Gemini output: {e}")
            last_summary = summary_str if 'summary_str' in locals() else None
            last_error = str(e)
        except Exception as e:
            logger.error(f"[summarize_cluster] Unexpected error: {e}")
            last_summary = summary_str if 'summary_str' in locals() else None
            last_error = str(e)
    # Fallback: always return error and raw output for debugging/leniency
    logger.warning(f"[summarize_cluster] All attempts failed. Returning fallback summary.")
    return {"error": last_error, "raw_output": last_summary or ""}


def summarize_repo(cluster_jsons: List[dict], repo_metrics: dict, api_key: Optional[str] = None) -> dict:
    prompt = build_repo_prompt(cluster_jsons, repo_metrics)
    def clean_json_block(s):
        s = s.strip()
        s = re.sub(r'^```(?:json)?', '', s, flags=re.IGNORECASE).strip()
        s = re.sub(r'```$', '', s).strip()
        if s.startswith('{') and "'" in s and '"' not in s:
            s = s.replace("'", '"')
        return s

    summary_str = gemini_summarize(prompt, api_key=api_key)
    logger.info(f"[summarize_repo] Gemini raw output: {summary_str}")
    cleaned = clean_json_block(summary_str)
    try:
        summary = json.loads(cleaned)
        jsonschema.validate(instance=summary, schema=repo_schema)
        return summary
    except (json.JSONDecodeError, ValidationError) as e:
        logger.warning(f"[summarize_repo] Failed to parse/validate Gemini output: {e}")
        return {"error": str(e), "raw_output": summary_str}


def clusters_to_qdrant(qdrant_client, collection_name: str, meta_with_cluster: list):
    """
    Updates Qdrant payloads for each point with its assigned cluster_id.
    """
    for meta in meta_with_cluster:
        point_id = meta.get("id")
        cluster_id = meta.get("cluster_id")
        if point_id is not None and cluster_id is not None:
            qdrant_client.set_payload(
                collection_name=collection_name,
                payload={"cluster_id": cluster_id},
                points=[point_id]
            )


def build_atlas_pack(
    meta_with_cluster: list,
    repo_id: str,
    similarity_threshold: float = 0.8,
    k_sim: int = 3,
    cluster_edge: bool = True,
    file_edge: bool = False
) -> dict:
    # Decide if input is file-level or chunk-level by checking for 'chunk_count' and 'vectors'
    is_file_level = (
        meta_with_cluster
        and isinstance(meta_with_cluster[0], dict)
        and "chunk_count" in meta_with_cluster[0]
        and "vectors" in meta_with_cluster[0]
    )

    nodes = []
    ids = []
    vectors = []
    dirpaths = []

    if is_file_level:
        # File-level nodes
        for node in meta_with_cluster:
            nodes.append({
                "id": node["id"],
                "label": node.get("label", os.path.basename(node["filepath"])),
                "filepath": node["filepath"],
                "dirpath": node.get("dirpath", ""),
                "cluster_id": node.get("cluster_id", ""),
                "loc": node.get("loc", 0),
                "chunk_count": node.get("chunk_count", 1),
                "summary": node.get("summary", ""),
                "vector": node["vector"]
            })
            ids.append(node["id"])
            vectors.append(node["vector"])
            dirpaths.append(node.get("dirpath", ""))
    else:
        # Chunk-level nodes
        for node in meta_with_cluster:
            payload = node.get("payload", {})
            nodes.append({
                "id": node["id"],
                "label": f"{os.path.basename(node['filepath'])}:{payload.get('start_line_no', '')}-{payload.get('end_line_no', '')}",
                "filepath": node["filepath"],
                "dirpath": node.get("dirpath", ""),
                "cluster_id": node.get("cluster_id", ""),
                "start_line_no": payload.get("start_line_no"),
                "end_line_no": payload.get("end_line_no"),
                "excerpt": payload.get("excerpt", ""),
                "vector": node["vector"]
            })
            ids.append(node["id"])
            vectors.append(node["vector"])
            dirpaths.append(node.get("dirpath", ""))

    edge_set = set()
    n_nodes = len(nodes)
    if vectors and n_nodes > 1:
        vecs_np = np.array(vectors)
        norms = np.linalg.norm(vecs_np, axis=1)
        safe_k = min(k_sim + 1, n_nodes)
        for i, vec_a in enumerate(vecs_np):
            similarities = np.dot(vecs_np, vec_a) / (norms * np.linalg.norm(vec_a) + 1e-8)
            actual_k = min(safe_k, len(similarities))
            if actual_k <= 1:
                continue
            top_k_idx = np.argpartition(-similarities, actual_k-1)[:actual_k]
            for j in top_k_idx:
                if j != i and similarities[j] >= similarity_threshold:
                    edge = (min(ids[i], ids[j]), max(ids[i], ids[j]), float(similarities[j]))
                    edge_set.add(edge)

    edge_list = [
        {"source": src, "target": tgt, "type": "semantic", "weight": weight}
        for src, tgt, weight in edge_set
    ]
    return {"nodes": nodes, "edges": edge_list}

def compute_content_hash(points: List) -> str:
    """
    Computes a SHA256 hash of the concatenated filepaths and optionally file contents/excerpts.
    Handles both dicts and Qdrant Record objects.
    """
    def get_payload(pt):
        if isinstance(pt, dict):
            return pt.get("payload", {})
        elif hasattr(pt, "payload"):
            return pt.payload
        return {}

    hash_input = "".join(
        str(get_payload(pt).get("filepath", "")) + str(get_payload(pt).get("excerpt", ""))
        for pt in points
    )
    return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

def aggregate_chunks_to_files(meta_with_cluster: list):
    file_nodes = {}
    for meta in meta_with_cluster:
        fp = meta["filepath"]
        if fp not in file_nodes:
            file_nodes[fp] = {
                "id": fp,
                "label": os.path.basename(fp),
                "filepath": fp,
                "dirpath": os.path.dirname(fp),
                "cluster_id": meta.get("cluster_id"),
                "loc": 0,
                "chunk_count": 0,
                "vectors": [],
                "excerpts": [],
                "summary": meta.get("payload", {}).get("summary", ""),
            }
        file_nodes[fp]["chunk_count"] += 1
        file_nodes[fp]["vectors"].append(meta["vector"])
        file_nodes[fp]["excerpts"].append(meta.get("payload", {}).get("excerpt", ""))
        file_nodes[fp]["loc"] += meta.get("payload", {}).get("line_count", 0)
    for node in file_nodes.values():
        node["vector"] = np.mean(node["vectors"], axis=0).tolist()
    return list(file_nodes.values())