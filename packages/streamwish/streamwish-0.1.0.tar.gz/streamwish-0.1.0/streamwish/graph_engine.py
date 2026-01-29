import time
from typing import List, Dict, Optional, Set
import networkx as nx
from pydantic import BaseModel, Field
from streamwish.llm_interface import LLMBackend

class Node(BaseModel):
    id: str
    content: str
    timestamp: float = Field(default_factory=time.time)
    embedding: Optional[List[float]] = None
    node_type: str = "chunk" # query, summary, chunk

    class Config:
        arbitrary_types_allowed = True

class ConveyorBeltGraph:
    def __init__(self, llm_client: LLMBackend, max_capacity: int = 100):
        """
        max_capacity: The maximum number of nodes to keep in the 'active' graph belt
        before simpler ones fall off (soft limit for the graph itself, not the LLM context).
        """
        self.graph = nx.DiGraph()
        self.llm_client = llm_client
        self.max_capacity = max_capacity

    def add_node(self, node_id: str, content: str, node_type: str = "chunk", neighbors: List[str] = None):
        """
        Adds a node to the graph. If embedding is missing, it generates one.
        """
        # Generate embedding if needed (simple check)
        # In a real async flow this might be batched
        embedding = self.llm_client.get_embedding(content)
        
        node = Node(
            id=node_id,
            content=content,
            node_type=node_type,
            embedding=embedding
        )

        self.graph.add_node(node_id, data=node)
        
        # Link to neighbors if they exist
        if neighbors:
            for neighbor_id in neighbors:
                if self.graph.has_node(neighbor_id):
                    self.graph.add_edge(node_id, neighbor_id)
                    # Bi-directional? Or conveyor belt flow? 
                    # Usually knowledge graphs are directed but associations are symmetric.
                    # Let's add undirected for similarity access usually.
                    self.graph.add_edge(neighbor_id, node_id)

        self._prune_graph()

    def _prune_graph(self):
        """
        Ensures the graph doesn't grow indefinitely. 
        Simple FIFO eviction for now if over capacity.
        """
        if self.graph.number_of_nodes() > self.max_capacity:
            # Sort nodes by timestamp and remove oldest
            # We need to access the Node object stored in 'data'
            nodes_with_time = []
            for n in self.graph.nodes(data=True):
                # n is (node_id, attributes)
                node_obj = n[1].get('data')
                if node_obj:
                    nodes_with_time.append((n[0], node_obj.timestamp))
            
            # Sort by time ascending (oldest first)
            nodes_with_time.sort(key=lambda x: x[1])
            
            # Remove oldest until back within limit
            num_to_remove = self.graph.number_of_nodes() - self.max_capacity
            for i in range(num_to_remove):
                self.graph.remove_node(nodes_with_time[i][0])

    def get_neighbors(self, node_id: str) -> List[Node]:
        if not self.graph.has_node(node_id):
            return []
        
        neighbor_ids = list(self.graph.neighbors(node_id))
        nodes = []
        for nid in neighbor_ids:
            node_data = self.graph.nodes[nid].get('data')
            if node_data:
                nodes.append(node_data)
        return nodes

    def get_all_nodes(self) -> List[Node]:
        return [data['data'] for _, data in self.graph.nodes(data=True) if 'data' in data]
