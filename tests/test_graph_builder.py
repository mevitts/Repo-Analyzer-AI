import unittest
from src.backend.graph_builder import RepoGraphBuilder

class TestRepoGraphBuilder(unittest.TestCase):
    def test_all_files_added(self):
        file_list = [
            {'path': 'src/main.py', 'type': 'code', 'size': 1234},
            {'path': 'README.md', 'type': 'doc', 'size': 234},
            {'path': 'data.bin', 'type': 'binary', 'size': 2000000},
        ]
        builder = RepoGraphBuilder(file_list)
        G = builder.build()
        self.assertEqual(len(G.nodes), 3)
        self.assertIn('src/main.py', G.nodes)
        self.assertIn('README.md', G.nodes)
        self.assertIn('data.bin', G.nodes)
        self.assertEqual(G.nodes['src/main.py']['type'], 'code')
        self.assertEqual(G.nodes['README.md']['type'], 'doc')
        self.assertEqual(G.nodes['data.bin']['type'], 'binary')

if __name__ == '__main__':
    unittest.main()
