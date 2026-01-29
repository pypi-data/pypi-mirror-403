from typing import List, Optional
import time
from streamwish.graph_engine import ConveyorBeltGraph, Node
from streamwish.auctioneer import TokenAuctioneer, RecencyBias
from streamwish.llm_interface import LLMBackend
from streamwish.distiller import ContextDistiller

class SlotManager:
    def __init__(self, llm_client: LLMBackend):
        self.llm_client = llm_client
        self.graph = ConveyorBeltGraph(llm_client)
        self.distiller = ContextDistiller(llm_client)
        # Default strategy
        self.auctioneer = TokenAuctioneer(strategy=RecencyBias())
        self.context_limit = 10

    def ingest_stream(self, data_stream: List[str]):
        """
        Simulates reading from a stream.
        """
        import uuid
        for content in data_stream:
            # Distill content before adding to graph to save space/time later
            # Optional: Keep raw content on disk and only graph the distilled version
            distilled_content = self.distiller.distill(content)
            
            node_id = f"chunk_{uuid.uuid4()}"
            self.graph.add_node(node_id, distilled_content)

    def process_query(self, query: str) -> str:
        """
        Main RAG Loop.
        1. Embed Query
        2. Retrieve Candidates (Neighborhood of current focus + Global + etc)
        3. Auction Slots
        4. Generate Answer
        """
        # 1. Embed Query
        query_embedding = self.llm_client.get_embedding(query)
        
        # 2. Gather Candidates
        # In a real graph walk, we would start from a "current position".
        # For now, we get EVERYTHING in the conveyor belt as candidates 
        # (assuming small scale or pre-filtered).
        candidates = self.graph.get_all_nodes()
        
        # Add the query itself as a node context
        query_node = Node(id="current_query", content=query, node_type="query", embedding=query_embedding)
        candidates.append(query_node)

        # 3. Auction
        context_data = {
            "query_embedding": query_embedding,
            "limit": self.context_limit
        }
        winning_nodes = self.auctioneer.auction(candidates, context_data)
        
        # 4. Construct Prompt
        context_text = "\n---\n".join([n.content for n in winning_nodes if n.node_type != "query"])
        
        system_prompt = (
            "You are a helpful assistant with a strictly limited context window.\n"
            "Use the provided context snippets to answer the user's query.\n"
            "If the answer is not in the context, admit it."
        )
        
        full_prompt = f"Context:\n{context_text}\n\nUser Question: {query}"
        
        response = self.llm_client.generate(full_prompt, system_instruction=system_prompt)
        
        return response
