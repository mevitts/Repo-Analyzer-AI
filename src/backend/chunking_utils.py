import os
from astchunk import ASTChunkBuilder
from enum import Enum, auto
from .language_enums import Language

'''
class Language(Enum):
    PYTHON = "python"
    JAVA = "java"
    TYPESCRIPT = "typescript"
    CSHARP = "csharp"
    '''

LANGUAGE_CONFIGS = {
    Language.PYTHON: {
        "max_chunk_size": 850,
        "language": Language.PYTHON.value,
        "metadata_template": "default",
        "chunk_expansion": True,
        "chunk_overlap": 2,
    },
    Language.JAVA: {
        "max_chunk_size": 1000,
        "language": Language.JAVA.value,
        "metadata_template": "default",
        "chunk_expansion": True,
        "chunk_overlap": 2,
    },
    Language.TYPESCRIPT: {
        "max_chunk_size": 900,
        "language": Language.TYPESCRIPT.value,
        "metadata_template": "default",
        "chunk_expansion": True,
        "chunk_overlap": 2,
    },
    Language.CSHARP: {
        "max_chunk_size": 900,
        "language": Language.CSHARP.value,
        "metadata_template": "default",
        "chunk_expansion": True,
        "chunk_overlap": 2,
    }
}

def get_language_from_path(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.py':
        return Language.PYTHON
    elif ext == '.java':
        return Language.JAVA
    elif ext in ['.ts', '.tsx']:
        return Language.TYPESCRIPT
    elif ext == '.cs':
        return Language.CSHARP
    return None

def chunk_file(file_path, file_content, language=None):
    """
    Chunk a file into logical sections (functions/classes for code, paragraphs for docs).
    Returns a list of dicts: [{file_path, start_line, end_line, chunk_text, language}, ...]
    """
    configs = LANGUAGE_CONFIGS.get(language)
    if not configs:
        return []

    try:
        chunk_builder = ASTChunkBuilder(**configs)

        chunkify_configs = {
            "repo_level_metadata": {
                "filepath": file_path
            }
        }
        
        chunks = chunk_builder.chunkify(file_content, **chunkify_configs)
        return chunks

    except Exception as e:
        print(f"Warning: Could not chunk file {file_path}. Error: {e}")
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

        if language and content:
            file_chunks = chunk_file(file_path, content, language)
            chunks.extend(file_chunks)

    return chunks
