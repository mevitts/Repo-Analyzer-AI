import unittest
import numpy as np
from src.backend.utils import summarization_utils

class TestSummarizationUtils(unittest.TestCase):
    def test_build_atlas_pack(self):
        # Create mock meta_with_cluster with at least 5 points
        meta_with_cluster = [
            {"id": f"pt{i}", "filename": f"{chr(97+i)}.py", "filepath": f"src/{chr(97+i)}.py", "cluster_id": i%2, "distance_to_centroid": 0.1*i, "vector": [float(i), float(i%2)]}
            for i in range(5)
        ]
        atlas = summarization_utils.build_atlas_pack(meta_with_cluster, repo_id="repo1", similarity_threshold=0.1, k_sim=2)
        self.assertIn("nodes", atlas)
        self.assertIn("edges", atlas)
        self.assertEqual(len(atlas["nodes"]), 5)
        # Check node fields
        for node in atlas["nodes"]:
            self.assertIn("id", node)
            self.assertIn("label", node)
            self.assertIn("filepath", node)
            self.assertIn("cluster_id", node)
            self.assertIn("score", node)
            self.assertIn("pos", node)
        # Check edge fields
        for edge in atlas["edges"]:
            self.assertIn("source", edge)
            self.assertIn("target", edge)
            self.assertIn("type", edge)
            self.assertIn("weight", edge)
            
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
            {"filename": f"{chr(97+i)}.py", "dirpath": "src", "distance_to_centroid": 0.1*i}
            for i in range(5)
        ]
        clusters = {0: {"member_indices": list(range(5))}}
        labels = summarization_utils.get_clusters_and_labels(meta_with_cluster, clusters, n_labels=5, n_min=1)
        self.assertIn(0, labels)
        self.assertEqual(len(labels[0]["representatives"]), 5)

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
