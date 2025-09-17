import os
import logging
from astchunk import ASTChunkBuilder
from enum import Enum, auto
from src.backend.language_enums import Language
from src.backend.config import LANGUAGE_CONFIGS

logger = logging.getLogger(__name__)

def get_language_from_path(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    lang = None
    if ext == '.py':
        lang = Language.PYTHON
    elif ext == '.java':
        lang = Language.JAVA
    elif ext in ['.ts', '.tsx']:
        lang = Language.TYPESCRIPT
    elif ext == '.cs':
        lang = Language.CSHARP
    logger.debug(f"[get_language_from_path] {file_path} -> {lang}")
    return lang

def chunk_file(file_path, file_content, language):
    """
    Chunk a file into logical sections (functions/classes for code, paragraphs for docs).
    Returns a list of dicts: [{file_path, start_line, end_line, chunk_text, language}, ...]
    """
    configs = LANGUAGE_CONFIGS.get(language)
    if not configs:
        logger.info(f"[chunk_file] Skipping {file_path}: No config for language {language}")
        return []

    try:
        chunk_builder = ASTChunkBuilder(**configs)

        chunkify_configs = {
            "repo_level_metadata": {
                "filepath": file_path
            }
        }
        chunks = chunk_builder.chunkify(file_content, **chunkify_configs)
        # Add 'excerpt' to each chunk's metadata (use chunk_text or similar field)
        for chunk in chunks:
            if isinstance(chunk, dict):
                meta = chunk.get("metadata", chunk)
                excerpt = chunk.get("chunk_text") or chunk.get("content") or str(chunk)
                if 'metadata' in chunk:
                    chunk['metadata']['excerpt'] = excerpt
                else:
                    chunk['excerpt'] = excerpt
        return chunks

    except Exception as e:
        logger.warning(f"[chunk_file] Could not chunk file {file_path}. Error: {e}")
        return []

def chunk_repo(file_contents):
    """
    Chunks all files in a given repository.

    Args:
        file_contents (dict): A dictionary mapping file paths to their content.
    
    Returns:
        A list containing all chunk dictionaries for the entire repository.
    """
    chunks = []
    for file_path, content in file_contents.items():
        language = get_language_from_path(file_path)
        if not language:
            logger.info(f"[chunk_repo] Skipping {file_path}: language not detected")
            continue
        if not content:
            logger.info(f"[chunk_repo] Skipping {file_path}: empty content")
            continue
        file_chunks = chunk_file(file_path, content, language)
        logger.info(f"[chunk_repo] {file_path}: {len(file_chunks)} chunks")
        chunks.extend(file_chunks)
    logger.info(f"[chunk_repo] Total chunks generated: {len(chunks)}")
    return chunks
