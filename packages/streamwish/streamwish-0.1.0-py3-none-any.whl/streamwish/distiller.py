from streamwish.llm_interface import LLMBackend

class ContextDistiller:
    def __init__(self, llm_client: LLMBackend):
        self.llm_client = llm_client

    def distill(self, text: str, max_words: int = 50) -> str:
        """
        Compresses text into a high-density summary.
        """
        if len(text.split()) < max_words:
            return text
            
        system_prompt = (
            f"Summarize the following text into strictly less than {max_words} words. "
            "Preserve key entities and relationships. Be telegraphic."
        )
        
        return self.llm_client.generate(text, system_instruction=system_prompt)
