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
from umap import UMAP

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
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 512}
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return str(result)

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
    X = []
    
    meta = []
    for pt in points:
        vector = pt.get("vector")
        if vector is None:
            continue
        X.append(vector)
        
        payload = pt.get("payload", {})
        filepath = payload.get("filepath", "")
        # dirpath: top-1 or top-2 directory parts
        parts = filepath.split("/")
        dirpath = "/".join(parts[:2]) if len(parts) > 1 else parts[0]
        filename = os.path.basename(filepath)
        meta.append({
            "id": pt.get("id"),
            "filepath": filepath,
            "dirpath": dirpath,
            "filename": filename,
            "payload": payload
        })
    if not X:
        return np.array([]), []
    X = np.array(X)
    # L2 normalize
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    X = X / np.clip(norms, 1e-8, None)
    return X, meta

def run_kmeans(X: np.ndarray, n_clusters: int = 10, random_state: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Runs KMeans clustering on X.
    Returns: (labels, centroids)
    """
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init="auto")
    labels = kmeans.fit_predict(X)
    centroids = kmeans.cluster_centers_
    return labels, centroids

def assign_clusters_and_scores(X: np.ndarray, meta: List[Dict[str, Any]], labels: np.ndarray, centroids: np.ndarray):
    """
    Assigns cluster_id to each meta entry and computes distances to centroid.
    Returns:
        meta_with_cluster: meta list with 'cluster_id' and 'distance_to_centroid' added
        clusters: dict of cluster_id -> {centroid, member_indices, member_ids}
    """
    if X.size == 0 or labels.size == 0 or centroids.size == 0:
        return []
    
    meta_with_cluster = []
    clusters = defaultdict(lambda: {"centroid": None, "member_indices": [], "member_ids": []})
    
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

def get_clusters_and_labels(meta_with_cluster: List[Dict[str, Any]], clusters: Dict[int, Dict[str, Any]], n_labels: int = 6) -> Dict[int, Dict[str, Any]]:
    """
    For each cluster, get top n_labels filenames as labels.
    Returns: dict of cluster_id -> {representatiteves, label, top_dirs, top_files}
    """
    cluster_labels = {}
    for cluster_id, info in clusters.items():
        members = [meta_with_cluster[i] for i in info["member_indices"]]
        # Sort members by distance to centroid
        members_sorted = sorted(members, key=lambda m: m["distance_to_centroid"])
        #select top n 
        top_members = members_sorted[:n_labels]
        cluster_labels[cluster_id] = {
            "representatives": top_members,
            "label": top_members[0]["filename"] if top_members else None,
            "top_dirs": list({m["dirpath"] for m in top_members}),
            "top_files": list({m["filename"] for m in top_members}),
        }

    return cluster_labels

def build_cluster_prompt(cluster_labels: dict, repo_id: str) -> str:
    """
    Build a prompt for a single cluster using its members, label, filepaths, line ranges, and any signature hints.
    """
    members = cluster_labels.get("representatives", [])
    proto_label = cluster_labels.get("label", "")
    
    prompt = f"Repo: {repo_id}\nCluster label: {proto_label}\n\n"
    for mem in members:
        fp = mem.get("filepath", "")
        payload = mem.get("payload", {})
        start = payload.get("start_line_no", "?")
        end = payload.get("end_line_no", "?")
        excerpt = payload.get("excerpt", "")
        ancestors = payload.get("ancestors", "")
        signature = payload.get("signature", "")
        
        if ancestors:
            prompt += f"Ancestors: {ancestors}\n"
        if signature:
            prompt += f"Signature: {signature}\n"
            
        prompt += f"Excerpt (truncated to 600 chars):\n{excerpt}\n\n"
        prompt += (
        "Summarize what this group does (1-2 sentences), key responsibilities/data, and notable entry points.\n"
        "Only use facts present in the excerpts, file paths, and symbols. Do not speculate beyond the provided text.\n"
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

def summarize_cluster(cluster_info: dict, repo_id: str, api_key: Optional[str] = None) -> dict:
    prompt = build_cluster_prompt(cluster_info, repo_id)
    summary = gemini_summarize(prompt, api_key=api_key)
    
    try:
        convert = jsonschema.validate(instance=summary, schema=cluster_schema)
    except ValidationError as e:
        print(f"Validation Error: {e.message}")
        print(f"Validation Error: {e.message}")

    return json.loads(summary) if convert else {}

def summarize_repo(cluster_jsons: List[dict], repo_metrics: dict, api_key: Optional[str] = None) -> dict:
    prompt = build_repo_prompt(cluster_jsons, repo_metrics)
    summary = gemini_summarize(prompt, api_key=api_key)
    try:
        convert = jsonschema.validate(instance=summary, schema=repo_schema)
    except ValidationError as e:
        print(f"Validation Error: {e.message}")
        print(f"Validation Error: {e.message}")

    return json.loads(summary) if convert else {}

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

def build_atlas_pack(meta_with_cluster: list, repo_id: str, similarity_threshold: float = 0.8, k_sim: int = 5) -> dict:
    """
    Builds an atlas pack: nodes (points) and edges (semantic relationships).
    Nodes represent code points: id, label, filepath, cluster_id, pos, score
    Edges represent semantic similarity above a set threshold: semantic kNN (k_sim) using cosine similarity
    """
    nodes = []
    vectors = []
    ids = []
    #node building (id and distance score) and vector collection
    for meta in meta_with_cluster:
        node = {
            "id": meta["id"],
            "label": meta["filename"],
            "filepath": meta["filepath"],
            "cluster_id": meta["cluster_id"],
            "score": meta.get("distance_to_centroid", 0.0)
        }
        nodes.append(node)
        vec = meta.get("vector")
        if vec is not None:
            vectors.append(vec)
            ids.append(meta["id"])
        else:
            vectors.append(np.zeros(10))
            ids.append(meta["id"])

    if len(vectors) > 0:
        reducer = UMAP(n_components=2, random_state=42)
        vecs_np = np.array(vectors)
        pos_2d = reducer.fit_transform(vecs_np)
        
        if isinstance(pos_2d, np.ndarray) and pos_2d.ndim == 2 and pos_2d.shape[1] == 2:
            for i, node in enumerate(nodes):
                node["pos"] = {"x": float(pos_2d[i, 0]), "y": float(pos_2d[i, 1])}
        else:
            for node in nodes:
                node["pos"] = {"x": 0.0, "y": 0.0}

    edges = set()
    vecs_np = np.array(vectors)
    norms = np.linalg.norm(vecs_np, axis=1)

    for i, vec_a in enumerate(vecs_np):
        similarities = np.dot(vecs_np, vec_a) / (norms * np.linalg.norm(vec_a) + 1e-8)

        #get top k indices
        top_k_idx = np.argpartition(-similarities, k_sim+1)[:k_sim+1]
        candidates = [(j, similarities[j]) for j in top_k_idx if j != i and similarities[j] >= similarity_threshold]

        #sort and take top k
        top_k = sorted(candidates, key=lambda x: -x[1])[:k_sim]

        for j, similarity in top_k:
            edge = (min(ids[i], ids[j]), max(ids[i], ids[j]), float(similarity))
            edges.add(edge)

    edge_list = [
        {"source": src, "target": tgt, "type": "semantic", "weight": weight}
        for src, tgt, weight in edges
    ]

    return {"nodes": nodes, "edges": edge_list}
