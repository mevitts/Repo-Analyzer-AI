import pytest
from src.backend.utils.summarization_utils import compute_content_hash

@pytest.fixture
def sample_points():
    return [
        {"payload": {"filepath": "src/a.py", "excerpt": "def foo(): pass"}},
        {"payload": {"filepath": "src/b.py", "excerpt": "def bar(): pass"}},
    ]

@pytest.fixture
def sample_points_modified():
    return [
        {"payload": {"filepath": "src/a.py", "excerpt": "def foo(): pass"}},
        {"payload": {"filepath": "src/b.py", "excerpt": "def bar(): print('hi')"}},  # changed excerpt
    ]

def test_content_hash_changes_on_modification(sample_points, sample_points_modified):
    hash1 = compute_content_hash(sample_points)
    hash2 = compute_content_hash(sample_points_modified)
    assert hash1 != hash2, "Hash should change if any excerpt changes"

def test_content_hash_same_for_identical_points(sample_points):
    hash1 = compute_content_hash(sample_points)
    hash2 = compute_content_hash(sample_points)
    assert hash1 == hash2, "Hash should be identical for identical points"

def test_cache_behavior(sample_points):
    # Simulate cache dict
    cache = {}
    repo_id = "repo1"
    content_hash = compute_content_hash(sample_points)
    cache_key = (repo_id, content_hash)
    result = {"summary": "test"}
    # Store in cache
    cache[cache_key] = result
    # Retrieve from cache
    assert cache[cache_key]["summary"] == "test"
    # Change points, hash should change
    new_points = [
        {"payload": {"filepath": "src/a.py", "excerpt": "def foo(): pass"}},
        {"payload": {"filepath": "src/b.py", "excerpt": "def bar(): print('hi')"}},
    ]
    new_hash = compute_content_hash(new_points)
    new_cache_key = (repo_id, new_hash)
    assert new_cache_key not in cache, "Cache miss expected for changed content"
