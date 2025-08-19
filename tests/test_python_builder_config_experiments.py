
import pytest
from src.backend.chunking_utils import chunk_file, LANGUAGE_CONFIGS
from src.backend.language_enums import Language

input_file = 'C:\\Users\\MattEvitts\\Repos\\Repo-Analyzer-AI\\src\\backend\\main.py'
output_file = 'C:\\Users\\MattEvitts\\Repos\\Repo-Analyzer-AI\\tests\\ast_chunking_with_expansion_results.txt'

with open(input_file, 'r', encoding='utf-8') as f:
    code = f.read()

print(f"file Path: {input_file}")

@pytest.mark.parametrize("max_chunk_size", [800, 1000, 1200, 1500])
@pytest.mark.parametrize("chunk_overlap", [0, 1, 2])
def test_python_builder_config_experiments(max_chunk_size, chunk_overlap):

    LANGUAGE_CONFIGS[Language.PYTHON]['max_chunk_size'] = max_chunk_size
    LANGUAGE_CONFIGS[Language.PYTHON]['chunk_overlap'] = chunk_overlap

    chunks = chunk_file(
        file_path=input_file,
        file_content=code,
        language="python"
    )

    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*80}\nExperiment: max_chunk_size={max_chunk_size}, chunk_overlap={chunk_overlap}\n{'='*80}\n")
        for i, chunk in enumerate(chunks, 1):
            content = chunk.get('content', chunk.get('context', ''))
            metadata = chunk.get('metadata', {})
            line_count = len(content.split('\n'))
            header = f"{'-' * 25} Chunk {i} ({line_count} lines / {metadata.get('chunk_size', 0)} chars) {'-' * 25}\n"
            f.write(header)
            f.write(content)
            f.write("\n" + "-" * (len(header) - 1) + "\n\n")

