import random
from collections import defaultdict
from typing import List, Dict, Any, Optional
import requests
import os
import numpy as np

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


