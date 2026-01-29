from typing import List, Dict, Any
from abc import ABC, abstractmethod
from streamwish.graph_engine import Node

class ValuationStrategy(ABC):
    @abstractmethod
    def score(self, node: Node, context: Dict[str, Any]) -> float:
        """
        Assigns a value score to a node based on the current context.
        Context can include: current_query, current_time, node_type, etc.
        """
        pass

class RecencyBias(ValuationStrategy):
    def score(self, node: Node, context: Dict[str, Any]) -> float:
        # Higher score for more recent nodes
        # Simple decay: score = 1 / (age + 1)
        import time
        age = time.time() - node.timestamp
        return 1.0 / (age + 1.0)

class SemanticRelevanceBias(ValuationStrategy):
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def score(self, node: Node, context: Dict[str, Any]) -> float:
        # This would require an embedding dot product
        # For now, we assume embeddings are pre-calculated and context has 'query_embedding'
        query_embedding = context.get('query_embedding')
        if not query_embedding or not node.embedding:
            return 0.0
        
        # Simple dot product manual calculation (or use numpy if available)
        # Assuming normalized vectors
        dot_product = sum(a*b for a, b in zip(query_embedding, node.embedding))
        return dot_product

class TokenAuctioneer:
    def __init__(self, strategy: ValuationStrategy):
        self.strategy = strategy
        self.allocations = {
            "query": 2,
            "global_summary": 1,
            "neighborhood": 5,
            "path": 1,
            "wish_menu": 1
        } # Default split for 10 slots

    def auction(self, candidates: List[Node], context: Dict[str, Any]) -> List[Node]:
        """
        Selects the best nodes to fill the available slots.
        Refined approach: Instead of strict buckets, maybe we score all and pick top N?
        Or we enforce the buckets from brainstorming.
        
        Let's try the Bucket approach first as per design, but with fallback.
        """
        selected_nodes = []
        
        # 1. Group candidates by type/role (this needs candidate metadata)
        # For this version, we'll simplify: We will score ALL candidates and take the top 10.
        # But we will bump scores based on "Protected" status if needed.
        
        scored_candidates = []
        for node in candidates:
            base_score = self.strategy.score(node, context)
            
            # Boost score based on type to simulate "reserved slots" logic
            if node.node_type == "query":
                base_score += 100 # Always include
            elif node.node_type == "summary":
                base_score += 50
                
            scored_candidates.append((base_score, node))
            
        # Sort descending
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Take top N
        limit = context.get('limit', 10)
        return [item[1] for item in scored_candidates[:limit]]
