import networkx as nx
from typing import List, Dict, Any

class RepoGraphBuilder:
    def __init__(self, file_list: List[Dict[str, Any]]):
        self.file_list = file_list
        self.graph = nx.DiGraph()

    def build(self):
        for file in self.file_list:
            self.graph.add_node(
                file['path'],
                type=file.get('type', 'unknown'),
                size=file.get('size', None)
            )
            # TODO: Add code to parse code files for functions/classes/imports and add as nodes/edges
        return self.graph

    def get_graph(self):
        return self.graph

    # Optionally, add methods for updating, querying, or serializing the graph
