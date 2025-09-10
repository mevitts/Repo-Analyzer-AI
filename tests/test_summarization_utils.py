import unittest
import numpy as np
from src.backend.utils import summarization_utils

class TestSummarizationUtils(unittest.TestCase):
    def test_stratified_downsample(self):
        points = [
            {"payload": {"filepath": "a.py"}}, {"payload": {"filepath": "a.py"}},
            {"payload": {"filepath": "b.py"}}, {"payload": {"filepath": "b.py"}},
            {"payload": {"filepath": "c.py"}}
        ]
        sampled = summarization_utils.stratified_downsample(points, n_max=3)
        self.assertEqual(len(sampled), 3)
        filepaths = {pt["payload"]["filepath"] for pt in sampled}
        self.assertTrue("a.py" in filepaths and "b.py" in filepaths and "c.py" in filepaths)

    def test_preprocess_points(self):
        points = [
            {"id": 1, "vector": [1, 0], "payload": {"filepath": "src/a.py"}},
            {"id": 2, "vector": [0, 1], "payload": {"filepath": "src/b.py"}}
        ]
        X, meta = summarization_utils.preprocess_points(points)
        self.assertEqual(X.shape, (2, 2))
        self.assertEqual(meta[0]["filepath"], "src/a.py")

    def test_run_kmeans(self):
        X = np.array([[1, 0], [0, 1], [1, 1]])
        labels, centroids = summarization_utils.run_kmeans(X, n_clusters=2)
        self.assertEqual(len(labels), 3)
        self.assertEqual(centroids.shape[0], 2)

    def test_assign_clusters_and_scores(self):
        X = np.array([[1, 0], [0, 1]])
        meta = [{"id": 1, "filepath": "a.py", "payload": {}}, {"id": 2, "filepath": "b.py", "payload": {}}]
        labels = np.array([0, 1])
        centroids = np.array([[1, 0], [0, 1]])
        meta_with_cluster, clusters = summarization_utils.assign_clusters_and_scores(X, meta, labels, centroids)
        self.assertEqual(len(meta_with_cluster), 2)
        self.assertIn(0, clusters)
        self.assertIn(1, clusters)

    def test_get_clusters_and_labels(self):
        meta_with_cluster = [
            {"filename": "a.py", "dirpath": "src", "distance_to_centroid": 0.1},
            {"filename": "b.py", "dirpath": "src", "distance_to_centroid": 0.2}
        ]
        clusters = {0: {"member_indices": [0, 1]}}
        labels = summarization_utils.get_clusters_and_labels(meta_with_cluster, clusters, n_labels=2)
        self.assertIn(0, labels)
        self.assertEqual(len(labels[0]["representatives"]), 2)

    def test_build_cluster_prompt(self):
        cluster_labels = {
            "representatives": [
                {"filepath": "src/a.py", "payload": {"start_line_no": 1, "end_line_no": 10, "excerpt": "def foo(): pass", "ancestors": "Bar", "signature": "def foo()"}}
            ],
            "label": "a.py"
        }
        prompt = summarization_utils.build_cluster_prompt(cluster_labels, repo_id="repo1")
        self.assertIn("Repo: repo1", prompt)
        self.assertIn("Excerpt", prompt)

    def test_build_repo_prompt(self):
        cluster_jsons = [
            {"title": "API", "summary": "Handles requests", "key_files": ["src/api.py"]}
        ]
        repo_metrics = {"points": 10, "clusters": 1, "files": 2, "top_dirs": ["src"]}
        prompt = summarization_utils.build_repo_prompt(cluster_jsons, repo_metrics)
        self.assertIn("Repo metrics", prompt)
        self.assertIn("Clusters:", prompt)

if __name__ == "__main__":
    unittest.main()
