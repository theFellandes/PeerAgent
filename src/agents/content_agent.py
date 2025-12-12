# ContentAgent - Web search and content generation with citations
from typing import Optional, List
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

from src.agents.base import BaseAgent
from src.models.agents import ContentOutput
from src.utils.logger import get_logger


class ContentAgent(BaseAgent):
    """Agent specialized in web search and content creation with citations."""
    
    def __init__(self, session_id: Optional[str] = None):
        super().__init__(session_id)
        self.logger = get_logger("ContentAgent")
        self.search_wrapper = DuckDuckGoSearchAPIWrapper(max_results=5)
        self.search_tool = DuckDuckGoSearchResults(api_wrapper=self.search_wrapper)
    
    @property
    def agent_type(self) -> str:
        return "content_agent"
    
    @property
    def system_prompt(self) -> str:
        return """You are a research specialist. Provide accurate, well-structured information.
Always cite sources when available."""
    
    async def _perform_search(self, query: str) -> tuple[str, List[str]]:
        """Perform web search and return results with URLs."""
        try:
            self.logger.info(f"Searching: {query}")
            results = self.search_tool.invoke(query)
            
            sources = []
            if isinstance(results, str):
                url_pattern = r'https?://[^\s\])]+'
                sources = list(set(re.findall(url_pattern, results)))[:5]
            
            return results, sources
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return f"Search failed: {e}", []
    
    async def execute(
        self,
        task: str,
        search_query: Optional[str] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        **kwargs
    ) -> ContentOutput:
        """Generate content based on web search."""
        self.logger.info(f"ContentAgent executing: {task[:50]}...")
        
        try:
            query = search_query or task
            search_results, sources = await self._perform_search(query)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("system", f"Search results:\n{search_results}"),
                ("human", task)
            ])
            
            messages = prompt.format_messages()
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            
            self.logger.info(f"ContentAgent completed with {len(sources)} sources")
            return ContentOutput(
                content=content,
                sources=sources
            )
            
        except Exception as e:
            self.logger.error(f"ContentAgent error: {e}")
            return ContentOutput(
                content=f"Error researching: {e}",
                sources=[]
            )
