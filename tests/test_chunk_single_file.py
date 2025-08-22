import pytest
from src.backend.utils.chunking_utils import chunk_file
from src.backend.language_enums import Language

TEST_FILE = 'C:/Users/MattEvitts/Repos/Repo-Analyzer-AI/src/backend/main.py'

@pytest.mark.simple
def test_chunk_single_file():
    with open(TEST_FILE, 'r', encoding='utf-8') as f:
        code = f.read()
    chunks = chunk_file(
        file_path=TEST_FILE,
        file_content=code,
        language=Language.PYTHON
    )
    print(f"Chunk count: {len(chunks)}")
    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- Chunk {i} ---\n{chunk}\n")
        print(chunk)
    assert len(chunks) > 0, "No chunks returned!"
